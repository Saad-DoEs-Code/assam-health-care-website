// Copies the self-hosted web fonts from node_modules into static/fonts/ so
// Django serves them. Both fonts are licensed under the SIL Open Font License.
// Run with: npm run fonts
import { copyFileSync, mkdirSync } from "node:fs";

const fonts = [
  "@fontsource-variable/manrope/files/manrope-latin-wght-normal.woff2",
  "@fontsource-variable/source-serif-4/files/source-serif-4-latin-wght-normal.woff2",
];

mkdirSync("static/fonts", { recursive: true });

for (const font of fonts) {
  const name = font.split("/").pop();
  copyFileSync(`node_modules/${font}`, `static/fonts/${name}`);
  console.log(`Copied ${name}`);
}
