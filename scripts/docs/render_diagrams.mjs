// Render every .excalidraw file of the documentation to a self-contained SVG with the
// real Excalidraw renderer, so the drawings keep their hand-drawn look. The fonts are
// embedded in each SVG, which then shows the same in a browser, on GitHub and in a PDF.
//
// Usage, from the repository root:
//   node scripts/docs/render_diagrams.mjs docs/diagramas/documentacao docs/assets/diagrams
import { readdirSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, relative, dirname, resolve } from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";

import { openPage } from "./cdp.mjs";

const [sourceDir, outDir] = process.argv.slice(2);
const here = dirname(fileURLToPath(import.meta.url));
const modules = resolve(here, "node_modules");
const assets = join(modules, "@excalidraw/excalidraw/dist/excalidraw-assets");
const FONTS = { Virgil: "Virgil.woff2", Cascadia: "Cascadia.woff2" };

const sources = walk(sourceDir).filter((file) => file.endsWith(".excalidraw"));
const page = await openPage();
await page.goto(pathToFileURL(writeHost()).href);
await page.evaluate("document.fonts.ready.then(() => true)");
for (const source of sources) {
  const scene = readFileSync(source, "utf8");
  const svg = await page.evaluate(`window.render(${JSON.stringify(scene)})`);
  const target = join(outDir, relative(sourceDir, source)).replace(/\.excalidraw$/, ".svg");
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, embedFonts(svg));
  console.log(`${source} -> ${target}`);
}
await page.close();

function walk(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory() ? walk(join(dir, entry.name)) : [join(dir, entry.name)],
  );
}

function writeHost() {
  const host = join(here, ".render-host.html");
  const script = (path) => `<script src="${pathToFileURL(join(modules, path)).href}"></script>`;
  const faces = Object.entries(FONTS)
    .map(([family, file]) => `@font-face{font-family:"${family}";src:url("${pathToFileURL(join(assets, file)).href}")}`)
    .join("");
  writeFileSync(host, `<!doctype html><meta charset="utf-8"><style>${faces}</style>
<p style="font-family:Virgil">á</p><p style="font-family:Cascadia">á</p>
<script>window.EXCALIDRAW_ASSET_PATH = ${JSON.stringify(pathToFileURL(dirname(assets)).href + "/")};</script>
${script("react/umd/react.production.min.js")}
${script("react-dom/umd/react-dom.production.min.js")}
${script("@excalidraw/excalidraw/dist/excalidraw.production.min.js")}
<script>
window.render = async (json) => {
  const scene = JSON.parse(json);
  const elements = ExcalidrawLib.restoreElements(scene.elements, null);
  const svg = await ExcalidrawLib.exportToSvg({
    elements,
    appState: { exportBackground: true, viewBackgroundColor: "#ffffff", exportWithDarkMode: false },
    files: scene.files || {},
    exportPadding: 24,
  });
  return svg.outerHTML;
};
</script>`);
  return host;
}

// Replace the font links Excalidraw writes with the font files themselves.
function embedFonts(svg) {
  const faces = Object.entries(FONTS)
    .map(([family, file]) => {
      const data = readFileSync(join(assets, file)).toString("base64");
      return `@font-face{font-family:"${family}";src:url(data:font/woff2;base64,${data}) format("woff2")}`;
    })
    .join("");
  // HTML serialisation writes &nbsp;, which XML does not define.
  const withoutLinks = svg.replace(/<style class="style-fonts">[\s\S]*?<\/style>/, "").replaceAll("&nbsp;", "&#160;");
  return withoutLinks.replace(/<defs>/, `<defs><style class="style-fonts">${faces}</style>`);
}
