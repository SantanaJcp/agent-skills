import assert from "node:assert/strict";
import test from "node:test";
import { visibleSkills } from "../src/catalog.mjs";

test("visitor sees the complete catalog", () => {
  assert.equal(visibleSkills().length, 3);
});
