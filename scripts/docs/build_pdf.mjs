// Build one documentation PDF from its Markdown source: cover, document control,
// table of contents with page numbers, numbered sections and landscape figure pages.
//
// Usage, from the repository root:
//   node scripts/docs/build_pdf.mjs docs/sextante-documentacao.pt.md docs/sextante-documentacao.pt.pdf
//
// The page numbers of the table of contents come from a first printing: each heading
// is looked up in the text of that PDF (pdftotext), then the document is printed again.
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { marked } from "marked";

import { openPage } from "./cdp.mjs";

const [input, output] = process.argv.slice(2);
const here = dirname(fileURLToPath(import.meta.url));
const build = join(here, ".build");
mkdirSync(build, { recursive: true });

const { meta, markdown } = splitFrontMatter(readFileSync(input, "utf8"));
const headings = [];
const body = renderBody(markdown, headings);
const htmlPath = join(build, `${meta.lang}.html`);

const page = await openPage();
writeFileSync(htmlPath, documentHtml(meta, body, headings, null));
const firstPass = await printPdf(page, htmlPath, join(build, `${meta.lang}-pass1.pdf`));
writeFileSync(htmlPath, documentHtml(meta, body, headings, pageNumbers(firstPass, headings)));
await printPdf(page, htmlPath, resolve(output));
await page.close();
console.log(`${input} -> ${output}`);

function splitFrontMatter(source) {
  const match = source.match(/^---\n([\s\S]*?)\n---\n/);
  const meta = {};
  for (const line of match[1].split("\n")) {
    const at = line.indexOf(":");
    if (at > 0) meta[line.slice(0, at).trim()] = line.slice(at + 1).trim();
  }
  return { meta, markdown: source.slice(match[0].length) };
}

function renderBody(markdown, headings) {
  const renderer = new marked.Renderer();
  renderer.heading = ({ tokens, depth }) => {
    const html = marked.Parser.parseInline(tokens);
    const text = html.replace(/<[^>]+>/g, "").replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#39;/g, "'");
    if (depth > 3) return `<h${depth}>${html}</h${depth}>`;
    const id = `h-${headings.length}`;
    headings.push({ id, depth, text });
    return `<h${depth} id="${id}">${html}</h${depth}>`;
  };
  renderer.table = function (token) {
    return `<div class="table">${marked.Renderer.prototype.table.call(this, token)}</div>`;
  };
  return marked.parse(markdown, { renderer, gfm: true });
}

async function printPdf(page, htmlPath, pdfPath) {
  await page.goto(pathToFileURL(htmlPath).href);
  await page.evaluate("document.fonts.ready.then(() => Promise.all([...document.images].map((i) => i.decode().catch(() => null)))).then(() => true)");
  const { data } = await page.send("Page.printToPDF", {
    preferCSSPageSize: true, printBackground: true, displayHeaderFooter: false,
  });
  writeFileSync(pdfPath, Buffer.from(data, "base64"));
  return pdfPath;
}

// The page of each heading in the first printing, searched in reading order.
function pageNumbers(pdfPath, headings) {
  const text = execFileSync("pdftotext", ["-layout", pdfPath, "-"], { encoding: "utf8", maxBuffer: 64 << 20 });
  // A heading is a line of its own; in the table of contents it shares the line with
  // its page number, so an exact line match skips the contents pages.
  const pages = text.split("\f").map((content) => content.split("\n").map(squash));
  const numbers = {};
  let from = 1;
  for (const heading of headings) {
    const needle = squash(heading.text);
    const found = pages.findIndex((lines, index) => index >= from && lines.includes(needle));
    if (found < 0) throw new Error(`heading not found in the PDF: ${heading.text}`);
    numbers[heading.id] = found + 1;
    from = found;
  }
  return numbers;
}

function squash(value) {
  return value.replace(/\s+/g, " ").trim();
}

function documentHtml(meta, body, headings, numbers) {
  const fonts = join(here, "node_modules/@fontsource");
  const face = (family, file, weight, style = "normal") =>
    `@font-face{font-family:"${family}";font-weight:${weight};font-style:${style};src:url("${pathToFileURL(join(fonts, file)).href}")}`;
  const faces = [400, 500, 600, 700].map((w) => face("Plex", `ibm-plex-sans/files/ibm-plex-sans-latin-${w}-normal.woff2`, w))
    .concat([face("Plex", "ibm-plex-sans/files/ibm-plex-sans-latin-400-italic.woff2", 400, "italic"),
      face("PlexMono", "ibm-plex-mono/files/ibm-plex-mono-latin-400-normal.woff2", 400),
      face("PlexMono", "ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff2", 500)]).join("\n");
  const css = readFileSync(join(here, "document.css"), "utf8")
    .replaceAll("{{running}}", meta.running).replaceAll("{{classification}}", meta.classification);
  const base = pathToFileURL(resolve(dirname(input)) + "/").href;
  const logo = pathToFileURL(resolve(meta.logo)).href;
  return `<!doctype html><html lang="${meta.lang}"><head><meta charset="utf-8"><base href="${base}">
<title>${meta.title}</title><style>${faces}\n${css}</style></head><body>
${cover(meta, logo)}
${control(meta)}
${contents(meta, headings, numbers)}
<main>${body}</main>
</body></html>`;
}

function cover(meta, logo) {
  const rows = ["client", "version", "date", "classification"]
    .map((key) => `<div><dt>${meta[`label_${key}`]}</dt><dd>${meta[key]}</dd></div>`).join("");
  return `<section class="cover">
  <div class="cover-top"><div class="logo"><img src="${logo}" alt="AMT"></div><div class="kind">${meta.kind}</div></div>
  <div class="cover-title">
    <div class="eyebrow">${meta.eyebrow}</div>
    <h1 class="product">${meta.product}</h1>
    <p class="subtitle">${meta.subtitle}</p>
    <p class="doc">${meta.title}</p>
  </div>
  <dl class="cover-meta">${rows}</dl>
  ${meta.cover_foot ? `<div class="cover-foot">${meta.cover_foot}</div>` : ""}
</section>`;
}

function control(meta) {
  const history = meta.history.split("|").map((row) => `<tr>${row.split(";").map((cell) => `<td>${cell.trim()}</td>`).join("")}</tr>`).join("");
  const head = meta.history_head.split(";").map((cell) => `<th>${cell.trim()}</th>`).join("");
  const facts = meta.control.split("|").map((row) => {
    const [key, value] = row.split(";");
    return `<tr><th scope="row">${key.trim()}</th><td>${value.trim()}</td></tr>`;
  }).join("");
  return `<section class="control">
  <h1 class="page-title">${meta.control_title}</h1>
  <div class="table"><table class="facts"><tbody>${facts}</tbody></table></div>
  <h3 class="minor">${meta.history_title}</h3>
  <div class="table"><table><thead><tr>${head}</tr></thead><tbody>${history}</tbody></table></div>
  <div class="callout"><strong>${meta.notice_title}</strong> ${meta.notice}</div>
</section>`;
}

function contents(meta, headings, numbers) {
  const items = headings.filter((h) => h.depth <= 3).map((h) => {
    const number = numbers ? numbers[h.id] : "00";
    return `<li class="toc-${h.depth}"><span class="toc-text">${h.text}</span><span class="toc-dots"></span><span class="toc-page">${number}</span></li>`;
  }).join("");
  return `<section class="contents"><h1 class="page-title">${meta.contents_title}</h1><ol>${items}</ol></section>`;
}
