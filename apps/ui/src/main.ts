/**
 * Electron main process.
 * Creates the avatar window and connects to the Bridge SSE stream.
 */
import "dotenv/config";
import { app, BrowserWindow, ipcMain } from "electron";
import { join } from "node:path";
import { createLogger } from "@avatar-agent/utils";

const log = createLogger("ui:main");
const BRIDGE_BASE = `http://127.0.0.1:${process.env["BRIDGE_PORT"] ?? 3000}`;

let mainWindow: BrowserWindow | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 480,
    height: 640,
    resizable: false,
    alwaysOnTop: true,
    frame: false,
    transparent: true,
    webPreferences: {
      preload: join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
    backgroundColor: "#00000000",
  });

  mainWindow.loadFile(join(__dirname, "renderer", "index.html"));

  if (process.env["NODE_ENV"] === "development") {
    mainWindow.webContents.openDevTools({ mode: "detach" });
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ── IPC: send message to Bridge ─────────────────────────────────────────────
ipcMain.handle("chat:send", async (_event, message: string) => {
  try {
    const res = await fetch(`${BRIDGE_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    return res.ok;
  } catch (err) {
    log.error("Failed to send chat message", err);
    return false;
  }
});

// ── IPC: get SSE stream URL ──────────────────────────────────────────────────
ipcMain.handle("sse:url", () => `${BRIDGE_BASE}/events`);

app.whenReady().then(() => {
  createWindow();
  log.info("UI window created");
});

app.on("window-all-closed", () => {
  app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
