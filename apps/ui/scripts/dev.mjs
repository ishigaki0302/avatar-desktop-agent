/**
 * Development build + Electron launcher.
 *
 * 1. Bundles main.ts + preload.ts → CommonJS (Electron main process)
 * 2. Bundles renderer/*.ts → IIFE (browser context)
 * 3. Copies index.html to dist/renderer/
 * 4. Spawns Electron from the project root so dotenv finds .env
 * 5. On source change, rebuilds and restarts Electron (watch mode)
 */
import esbuild from "esbuild";
import { spawn } from "child_process";
import { copyFileSync, mkdirSync } from "fs";
import { createRequire } from "module";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const uiRoot = path.join(__dirname, "..");
const projectRoot = path.join(uiRoot, "../..");

// Resolve electron binary
const _require = createRequire(import.meta.url);
const electronBin = String(_require("electron"));

// Workspace package aliases for esbuild
const alias = {
  "@avatar-agent/schema": path.join(projectRoot, "packages/schema/src/index.ts"),
  "@avatar-agent/utils":  path.join(projectRoot, "packages/utils/src/index.ts"),
};

// Prepare output directories
mkdirSync(path.join(uiRoot, "dist/renderer"), { recursive: true });

function copyHtml() {
  copyFileSync(
    path.join(uiRoot, "src/renderer/index.html"),
    path.join(uiRoot, "dist/renderer/index.html"),
  );
}

// ── Electron process management ──────────────────────────────────────────────
let electronProcess = null;
let restarting = false;

function startElectron() {
  if (restarting) return;
  restarting = true;
  setTimeout(() => { restarting = false; }, 500);

  if (electronProcess) {
    electronProcess.removeAllListeners();
    electronProcess.kill();
  }

  electronProcess = spawn(electronBin, [path.join(uiRoot, "dist/main.js")], {
    cwd: projectRoot, // CWD = project root so dotenv finds .env
    stdio: "inherit",
    env: { ...process.env, NODE_ENV: "development" },
  });

  electronProcess.on("exit", (code) => {
    if (code !== 0 && code !== null && code !== 130) {
      console.error(`[dev] Electron exited with code ${code}`);
    }
  });
}

// ── esbuild contexts (watch mode) ────────────────────────────────────────────
const mainCtx = await esbuild.context({
  entryPoints: [path.join(uiRoot, "src/main.ts")],
  bundle: true,
  platform: "node",
  format: "cjs",
  outfile: path.join(uiRoot, "dist/main.js"),
  external: ["electron"],
  sourcemap: true,
  alias,
  plugins: [{
    name: "restart-on-main-change",
    setup(build) {
      build.onEnd((result) => {
        if (result.errors.length === 0) {
          console.log("[dev] main rebuilt → restarting Electron");
          startElectron();
        }
      });
    },
  }],
});

const preloadCtx = await esbuild.context({
  entryPoints: [path.join(uiRoot, "src/preload.ts")],
  bundle: true,
  platform: "node",
  format: "cjs",
  outfile: path.join(uiRoot, "dist/preload.js"),
  external: ["electron"],
  sourcemap: true,
  alias,
});

const rendererCtx = await esbuild.context({
  entryPoints: [path.join(uiRoot, "src/renderer/renderer.ts")],
  bundle: true,
  platform: "browser",
  format: "iife",
  outfile: path.join(uiRoot, "dist/renderer/renderer.js"),
  sourcemap: true,
  alias,
  // Define sprite base path as absolute URL for Electron file:// protocol
  define: {
    __SPRITE_BASE__: JSON.stringify(
      path.join(projectRoot, "assets/sprites").replace(/\\/g, "/"),
    ),
  },
});

// ── Initial build ─────────────────────────────────────────────────────────────
console.log("[dev] Building...");
copyHtml();
await Promise.all([
  preloadCtx.rebuild(),
  rendererCtx.rebuild(),
  mainCtx.rebuild(), // triggers startElectron via plugin
]);

// ── Watch ─────────────────────────────────────────────────────────────────────
await Promise.all([
  mainCtx.watch(),
  preloadCtx.watch(),
  rendererCtx.watch(),
]);

console.log("[dev] Watching for changes (Ctrl+C to quit)...");

// Graceful shutdown
process.on("SIGINT", async () => {
  electronProcess?.kill();
  await Promise.all([mainCtx.dispose(), preloadCtx.dispose(), rendererCtx.dispose()]);
  process.exit(0);
});
