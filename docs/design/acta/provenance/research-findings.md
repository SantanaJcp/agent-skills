# Investigación visual: HTML Effectiveness (upstream)

Fecha: 2026-07-21 · Upstream: https://github.com/ThariqS/html-effectiveness @ `1787245d94aa680edf18b52027e3f859032776ba` (Apache-2.0)
Método: clon local, análisis de código fuente de los 32 HTML (20 principales + 11 unknowns + índices), render con Chrome headless a 1280px y 320px, lectura del blog post.

## 1. Verificación de la hipótesis central

**Hipótesis:** "Un shell reconocible alrededor de instrumentos deliberadamente diferentes."

**Veredicto: se sostiene, con una corrección importante.**

En el upstream hay DOS shells distintos que la hipótesis original mezcla:

1. **Shell de galería (marco del blog):** eyebrow con guion clay, h1 serif, lede sans, tarjeta "The prompt" con cita serif itálica + botón Copy prompt, divisor mono "WHAT CLAUDE PRODUCED", artefacto dentro de una card blanca sobre ivory, footer de atribución. Este marco existe porque los ejemplos acompañan un blog; **no** es parte del artefacto que un agente produciría.
2. **Convenciones del artefacto interior** (lo que sí es reutilizable como "shell"):
   - eyebrow de contexto en mono uppercase con tracking (a veces breadcrumb `ACME / EDITOR / TRIAGE`);
   - título serif + subtítulo/metadata con chips mono;
   - banda de métricas (chips EFFORT / FILES / RISK / …);
   - a veces banner de instrucciones de lectura ("This plan is sorted by likelihood-of-tweaking…");
   - secciones numeradas (chip mono `01` + h2 serif) o con letra (A/B/C) + badge de prioridad;
   - export/copy como cierre (última sección o botón primario arriba a la derecha en editores);
   - footer de procedencia informal sólo en algunos ("Authored from on-call notes + alert history · reviewed by …").

**Corrección:** el "shell editorial estable" upstream es en gran parte artefacto de presentación del blog. Para nuestra colección, el shell debe rediseñarse como contrato propio del artefacto (procedencia formal, no marco de galería) — y eso es una oportunidad, no una copia.

## 2. Verificación de los demás patrones

| Patrón hipotetizado | Veredicto | Evidencia |
| --- | --- | --- |
| Jerarquía con tipografía/bordes/espacio/fondos | ✅ Confirmado | Cards con hairline `1px` oat; fondos oat/ivory para callouts; casi sin sombras |
| Sombras escasas | ✅ Confirmado | ~12 usos en 32 archivos, mayoría sutiles o `none`; jerarquía nunca depende de sombra |
| Triada serif/sans/mono por función | ✅ Confirmado | serif=display+headings (121 usos), sans=cuerpo/UI (53), mono=labels/datos/código/eyebrows (365+43). Stacks de sistema, cero webfonts |
| Progressive disclosure por valor de decisión | ✅ Confirmado | u08: secciones ordenadas por "likelihood-of-tweaking"; "Mechanical work (trust me)" colapsado por bajo valor de decisión, no por longitud |
| Alternativas con igual fidelidad | ✅ Confirmado | 01-exploration: 3 columnas idénticas en estructura (código+PRO/CON+chips); recomendación DESPUÉS, en bloque aparte con borde rust |
| Overview primero, detalle después | ✅ Confirmado | Flowchart: SVG general + panel lateral de detalle al click; quiz: "mental model" antes de comportamientos; concept explainer con modelo antes de detalle |
| Copy/export como cierre del loop | ✅ Confirmado | u08 "Tweak these three things" (respuestas de una línea copiables); triage "Copy as markdown"; quiz exporta score/gaps. Patrón: estado → markdown → clipboard con fallback execCommand + flash "Copied ✓" |
| SVG inline para relaciones espaciales | ✅ Confirmado | 13 archivos; flechas SVG entre cajas HTML (16-plan) o diagrama SVG completo (13-flowchart); leyendas por forma+color |
| Color semántico consistente | ⚠️ Parcial | olive=éxito, rust=fallo/coste, clay=acción/atención. PERO clay es también acento de marca → ambigüedad atención-vs-marca; warning no tiene color propio (reusa clay/oat). Defecto a corregir |
| Layouts según el problema | ✅ Confirmado | Doc de 1 columna (incident), 3 columnas iguales (exploration), board de 4 columnas (triage), split diagrama+rail (flowchart), split editor+preview (prompt tuner) |

## 3. Tokens y sistema extraídos

- **Paleta:** ivory `#FAF9F5` (página), paper `#FFFFFF` (card), oat `#E3DACC` (tinte/bordes), slate `#141413` (tinta + superficies oscuras invertidas), clay `#D97757` / clay-d `#B85C3E` (acento), olive `#788C5D` (éxito), rust `#B04A3F` (fallo/coste). Declarada como `--vars` en `:root` pero con inconsistencias de copia-pega entre archivos.
- **Tipografía:** `ui-serif/Georgia`, `system-ui`, `ui-monospace/SF Mono`. Display serif 32–42px; cuerpo sans 14–15px/1.55; labels mono 10.5–12px uppercase tracking 0.08–0.14em. Números y datos SIEMPRE en mono.
- **Espaciado:** sin escala formal; padding de cards 20–28px; separación entre secciones 48–72px; medida de texto ~65–75ch en docs.
- **Radius:** cards 10–14px, chips/pills 999px, código 8–10px.
- **Bordes:** hairline 1px (oat o rgba slate); acentos de estado con borde 1.5px o borde izquierdo 3px.
- **Superficie invertida:** bloques slate oscuros para TL;DR y código (alto contraste deliberado como jerarquía).
- **Motion:** transiciones 120–240ms en border/background/transform; una animación larga (1.7s) para progreso. Nada esencial depende de motion.
- **Estados:** pills con texto+color (SEV-2, Resolved); toggles "View alternative →"; score chip en quiz; feedback de copy por cambio de texto del botón.
- **Navegación:** TOC fija derecha "ON THIS PAGE" (incident, explainers); sticky rails en 10 archivos; sin TOC en artefactos cortos.
- **Export:** botón primario oscuro (slate pill) en editores; botones Copy secundarios pill oat; markdown generado a mano desde el estado JS.

## 4. Invariantes útiles (conservar como principios)

1. Dos capas: contrato de shell estable + instrumento libre por trabajo.
2. Jerarquía por tipografía, espacio, hairlines y tintes de fondo; sombra casi nunca.
3. Tres voces tipográficas con roles estrictos (lectura / interfaz / datos), stacks de sistema.
4. Datos y números siempre en mono; labels uppercase con tracking.
5. Disclosure gobernado por valor de decisión (lo mecánico se pliega, lo decidible se expande).
6. Alternativas estructuralmente idénticas; la recomendación llega después y separada.
7. Overview → detalle (mapa antes que zoom), también en diagramas.
8. Todo estado interactivo desemboca en un export textual copiable (cerrar el loop).
9. SVG inline y semántico para relaciones espaciales, con leyenda forma+color.
10. Superficie invertida como recurso escaso para lo más importante (TL;DR, código).
11. El layout es del problema, no de la plantilla.
12. Micro-motion utilitario (~120–240ms), nunca decorativo esencial.

## 5. Decisiones específicas de un artefacto (no generalizar)

- Orden "likelihood-of-tweaking" (u08) — brillante para planes, no para reports.
- Board de 4 columnas con drag (triage) — sólo para trabajos de priorización.
- Ventana-mockup con barra (mockups de 16) — firma del upstream, además NO copiable.
- WHAT/WHY/WHERE rows (quiz) — específico de explicación de comportamiento.
- Panel lateral click-to-inspect (flowchart) — específico de diagramas grandes.

## 6. Defectos del upstream (superar, no heredar)

1. **Cero `@media print`** en los 32 archivos.
2. **Cero `prefers-reduced-motion`.**
3. **Cero `<noscript>`**; el quiz renderiza las opciones por JS → sin JS no hay contenido esencial.
4. **`innerHTML` con concatenación** de strings en 9 archivos (patrón XSS-inseguro con datos no confiables) + `onclick` inline en u08.
5. **ARIA casi ausente** (sólo toolbar-mock la usa); sin live regions para el feedback de copy; sin focus management.
6. **Breakpoints ad hoc** distintos por archivo (640/720/560/480/880/960/920/900/…).
7. **Overflow sin contenedor de scroll**: código cortado a 1280 en 01-exploration; data-flow y tabla de riesgos recortados a 320 en 16-plan.
8. **Etiquetas solapadas** en el flowchart a 1280 (colisión de label de arista con nodo).
9. **Procedencia informal e inconsistente**: sin fecha/commit/scope/entradas; imposible auditar obsolescencia.
10. **Sin diferenciación hecho/inferencia/simplificación.**
11. **Drag sin alternativa de teclado** (triage board).
12. **Warning sin color propio**; clay sobrecargado (marca + atención + acción).
13. Tokens duplicados inconsistentemente entre archivos (sin fuente canónica — nuestro publisher lo resuelve por materialización).

## 7. Cosas que NO copiaremos (identidad)

- Paleta clay/oat/ivory/olive/slate y sus hex.
- Nombres de tokens (`--clay`, `--oat`, …).
- La barra de ventana como firma de mockups.
- Cards/layouts específicos tal cual, SVGs, ilustraciones, escenarios "Acme", textos.
- El marco de galería (eyebrow+prompt+"What Claude produced") como estructura obligatoria del artefacto.

Atribución: los principios se inspiran en HTML Effectiveness (Apache-2.0, Thariq Shihipar); identidad, tokens, componentes y scaffolds serán originales.
