// Refuses a production dependency whose licence is outside NFR-LIC-001's allow list.
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const ALLOWED = new Set([
  "MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "ISC",
  "PSF-2.0", "MPL-2.0", "Unlicense", "CC0-1.0",
]);

// The first line is the project itself; each other line is one installed package.
const tree = execFileSync("npm", ["ls", "--omit=dev", "--all", "--parseable"], { encoding: "utf8" })
  .split("\n")
  .filter(Boolean)
  .slice(1);

const refused = [];
for (const path of tree) {
  const manifest = JSON.parse(readFileSync(join(path, "package.json"), "utf8"));
  const licence = typeof manifest.license === "string" ? manifest.license : "UNKNOWN";
  const parts = licence.replace(/[()]/g, "").split(/ OR /);
  if (!parts.some((part) => ALLOWED.has(part.trim()))) {
    refused.push(`${manifest.name}@${manifest.version}: ${licence}`);
  }
}

if (refused.length > 0) {
  console.error(`Licences outside NFR-LIC-001:\n${refused.join("\n")}`);
  process.exit(1);
}
console.log(`${tree.length} production packages, all under NFR-LIC-001 licences.`);
