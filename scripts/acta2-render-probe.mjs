#!/usr/bin/env node

/* Dependency-free headless-Chromium render probe for Acta v2 artifacts.
 *
 * Headless Chromium clamps --window-size to a ~500px minimum, so narrow
 * mobile viewports cannot be exercised with plain flags. This probe drives
 * Chromium over the DevTools protocol through --remote-debugging-pipe
 * (JSON messages over stdio fds 3/4 — no network, no npm dependency),
 * applies a real device-metrics override, reports document overflow, and
 * optionally captures a screenshot.
 *
 * Usage:
 *   node scripts/acta2-render-probe.mjs --url file:///abs/page.html \
 *     --width 320 --height 700 [--out shot.png] [--chrome /path/to/chrome]
 *
 * Prints:  PROBE width=320 scrollWidth=320 clientWidth=320 overflow=none
 * Exits 1 when document-level horizontal overflow is detected.
 */

import { spawn } from "node:child_process";
import { access, writeFile } from "node:fs/promises";

/** @param {string} name @param {string | undefined} [fallback] @returns {string | undefined} */
function argValue(name, fallback = undefined) {
  const index = process.argv.indexOf(name);
  if (index === -1) return fallback;
  const value = process.argv[index + 1];
  if (value === undefined) throw new Error(`${name} requires a value.`);
  return value;
}

const url = argValue("--url");
if (!url) throw new Error("--url is required.");
const width = Number(argValue("--width", "320"));
const height = Number(argValue("--height", "700"));
const out = argValue("--out");
const noJs = process.argv.includes("--no-js");
const dumpDom = process.argv.includes("--dump");
const chromeCandidates = /** @type {string[]} */ ([
  argValue("--chrome"),
  process.env.CHROME_BIN,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium-browser",
].filter(Boolean));
/** @type {string | null} */
let chrome = null;
for (const candidate of chromeCandidates) {
  try {
    await access(candidate);
    chrome = candidate;
    break;
  } catch {}
}
if (!chrome) {
  console.error("PROBE-SKIP no Chromium binary found");
  process.exit(2);
}

const browser = spawn(
  chrome,
  ["--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run", "--remote-debugging-pipe", "about:blank"],
  { stdio: ["ignore", "ignore", "ignore", "pipe", "pipe"] },
);

const writePipe = /** @type {import("node:stream").Writable} */ (browser.stdio[3]);
const readPipe = /** @type {import("node:stream").Readable} */ (browser.stdio[4]);

let nextId = 1;
/** @type {Map<number, (value: any) => void>} */
const pending = new Map();
let buffer = "";
readPipe.setEncoding("utf8");
readPipe.on("data", (chunk) => {
  buffer += chunk;
  let boundary = buffer.indexOf("\0");
  while (boundary !== -1) {
    const raw = buffer.slice(0, boundary);
    buffer = buffer.slice(boundary + 1);
    boundary = buffer.indexOf("\0");
    if (!raw) continue;
    const message = JSON.parse(raw);
    const resolve = message.id ? pending.get(message.id) : undefined;
    if (resolve) {
      pending.delete(message.id);
      resolve(message);
    }
  }
});

/** @param {string} method @param {Record<string, any>} [params] @param {string} [sessionId] */
function send(method, params = {}, sessionId = undefined) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, resolve);
    const payload = { id, method, params };
    if (sessionId) /** @type {any} */ (payload).sessionId = sessionId;
    writePipe.write(`${JSON.stringify(payload)}\0`, (error) => {
      if (error) reject(error);
    });
    setTimeout(() => {
      if (pending.has(id)) {
        pending.delete(id);
        reject(new Error(`CDP timeout for ${method}`));
      }
    }, 30000);
  });
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

try {
  const created = await send("Target.createTarget", { url: "about:blank" });
  const targetId = created.result.targetId;
  const attached = await send("Target.attachToTarget", { targetId, flatten: true });
  const sessionId = attached.result.sessionId;

  await send("Page.enable", {}, sessionId);
  await send(
    "Emulation.setDeviceMetricsOverride",
    { width, height, deviceScaleFactor: 1, mobile: width < 720 },
    sessionId,
  );
  if (noJs) {
    // Deterministic no-JS emulation (headless --blink-settings is flaky with --dump-dom).
    await send("Emulation.setScriptExecutionDisabled", { value: true }, sessionId);
  }
  await send("Page.navigate", { url }, sessionId);
  await delay(1200);

  const evalExpression = argValue("--eval");
  if (evalExpression) {
    // Drive an interacted state (e.g. select a radio, type a rationale)
    // before measuring or capturing. QA-only; the page itself is untouched.
    await send(
      "Runtime.evaluate",
      { expression: evalExpression, returnByValue: true },
      sessionId,
    );
    await delay(400);
  }

  if (dumpDom) {
    const dom = await send(
      "Runtime.evaluate",
      { returnByValue: true, expression: "document.documentElement.outerHTML" },
      sessionId,
    );
    process.stdout.write(String(dom.result.result.value ?? ""));
    browser.kill();
    process.exit(0);
  }

  if (process.argv.includes("--probe-disabled")) {
    const styles = await send(
      "Runtime.evaluate",
      {
        returnByValue: true,
        expression: `(() => {
          const pick = (el) => {
            if (!el) return null;
            const cs = getComputedStyle(el);
            return { cursor: cs.cursor, opacity: Number(cs.opacity) };
          };
          const choice = document.querySelector(".a2-choice:has(input[disabled])");
          return {
            button: pick(document.querySelector("button[disabled]")),
            slider: pick(document.querySelector("input[type=range][disabled]")),
            textarea: pick(document.querySelector("textarea[disabled]")),
            choiceLabel: pick(choice),
          };
        })()`,
      },
      sessionId,
    );
    console.log(`DISABLED-STYLES ${JSON.stringify(styles.result.result.value)}`);
    browser.kill();
    process.exit(0);
  }

  const metrics = await send(
    "Runtime.evaluate",
    {
      returnByValue: true,
      expression: `(() => {
        const doc = document.documentElement;
        const offenders = [];
        for (const el of document.querySelectorAll("*")) {
          const rect = el.getBoundingClientRect();
          if (rect.right > doc.clientWidth + 1 && !el.closest(".codewrap,.tablewrap,.flowwrap,.plotwrap,pre")) {
            offenders.push(el.tagName + (el.className && typeof el.className === "string" ? "." + el.className.split(" ")[0] : "") + ":" + Math.round(rect.right));
          }
        }
        return {
          scrollWidth: doc.scrollWidth,
          clientWidth: doc.clientWidth,
          title: document.title,
          offenders: offenders.slice(0, 10),
        };
      })()`,
    },
    sessionId,
  );
  const { scrollWidth, clientWidth, title, offenders } = metrics.result.result.value;
  const overflow = scrollWidth > clientWidth + 1;

  if (out) {
    const shot = await send(
      "Page.captureScreenshot",
      { format: "png", captureBeyondViewport: false },
      sessionId,
    );
    await writeFile(out, Buffer.from(shot.result.data, "base64"));
  }

  console.log(
    `PROBE width=${width} scrollWidth=${scrollWidth} clientWidth=${clientWidth} overflow=${overflow ? "YES" : "none"} title=${JSON.stringify(title)}${
      offenders.length ? ` offenders=${offenders.join(",")}` : ""
    }`,
  );
  browser.kill();
  process.exit(overflow ? 1 : 0);
} catch (error) {
  browser.kill();
  console.error(`PROBE-ERROR ${error.message}`);
  process.exit(3);
}
