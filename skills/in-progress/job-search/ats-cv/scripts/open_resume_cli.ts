// pdfjs only needs DOMMatrix for rendering; text extraction never touches it.
(globalThis as any).DOMMatrix ??= class {};
(globalThis as any).Path2D ??= class {};
const pdfjs = require("pdfjs-dist/legacy/build/pdf.js");
import { readFileSync } from "fs";
import { groupTextItemsIntoLines } from "lib/parse-resume-from-pdf/group-text-items-into-lines";
import { groupLinesIntoSections } from "lib/parse-resume-from-pdf/group-lines-into-sections";
import { extractResumeFromSections } from "lib/parse-resume-from-pdf/extract-resume-from-sections";

async function main() {
  const data = new Uint8Array(readFileSync(process.argv[2]));
  const pdf = await (pdfjs as any).getDocument({ data, useSystemFonts: true }).promise;
  let items: any[] = [];
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const tc = await page.getTextContent();
    await page.getOperatorList();
    for (const it of tc.items as any[]) {
      const { str, dir, transform, fontName, ...rest } = it;
      const font = page.commonObjs.has(fontName) ? page.commonObjs.get(fontName) : null;
      items.push({ ...rest, fontName: font?.name ?? fontName, text: str.replace(/-­‐/g, "-"), x: transform[4], y: transform[5] });
    }
  }
  items = items.filter((t) => t.hasEOL || t.text.trim() !== "");
  const sections = groupLinesIntoSections(groupTextItemsIntoLines(items));
  console.log(JSON.stringify({ sections: Object.keys(sections), resume: extractResumeFromSections(sections) }, null, 2));
}
main().catch((e) => { console.error(e); process.exit(1); });
