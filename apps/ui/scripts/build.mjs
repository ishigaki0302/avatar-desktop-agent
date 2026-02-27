/**
 * Production build script.
 * Outputs to apps/ui/dist/.
 */
import esbuild from "esbuild";
import { copyFileSync, mkdirSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const uiRoot = path.join(__dirname, "..");
const projectRoot = path.join(uiRoot, "../..");

const alias = {
  "@avatar-agent/schema": path.join(projectRoot, "packages/schema/src/index.ts"),
  "@avatar-agent/utils":  path.join(projectRoot, "packages/utils/src/index.ts"),
};

mkdirSync(path.join(uiRoot, "dist/renderer"), { recursive: true });
copyFileSync(
  path.join(uiRoot, "src/renderer/index.html"),
  path.join(uiRoot, "dist/renderer/index.html"),
);

await Promise.all([
  esbuild.build({
    entryPoints: [path.join(uiRoot, "src/main.ts")],
    bundle: true, platform: "node", format: "cjs",
    outfile: path.join(uiRoot, "dist/main.js"),
    external: ["electron"], minify: true, alias,
  }),
  esbuild.build({
    entryPoints: [path.join(uiRoot, "src/preload.ts")],
    bundle: true, platform: "node", format: "cjs",
    outfile: path.join(uiRoot, "dist/preload.js"),
    external: ["electron"], minify: true, alias,
  }),
  esbuild.build({
    entryPoints: [path.join(uiRoot, "src/renderer/renderer.ts")],
    bundle: true, platform: "browser", format: "iife",
    outfile: path.join(uiRoot, "dist/renderer/renderer.js"),
    minify: true, alias,
    define: {
      __SPRITE_BASE__: JSON.stringify(
        path.join(projectRoot, "assets/sprites").replace(/\\/g, "/"),
      ),
    },
  }),
]);

console.log("Build complete.");
