/**
 * Electron preload script.
 * Exposes a minimal, safe API to the renderer via contextBridge.
 */
import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("avatarBridge", {
  sendMessage: (message: string) =>
    ipcRenderer.invoke("chat:send", message) as Promise<boolean>,
  getSseUrl: () =>
    ipcRenderer.invoke("sse:url") as Promise<string>,
});
