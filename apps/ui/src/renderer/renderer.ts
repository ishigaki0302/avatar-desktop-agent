/**
 * Renderer process entrypoint.
 * Connects to Bridge SSE, dispatches render/status/result events to UI components.
 */
import type { UIEvent, RenderEvent, StatusEvent, ResultEvent } from "@avatar-agent/schema";
import { AvatarRenderer } from "./avatar.js";
import { Typewriter } from "./typewriter.js";

declare global {
  interface Window {
    avatarBridge: {
      sendMessage: (msg: string) => Promise<boolean>;
      getSseUrl: () => Promise<string>;
    };
  }
}

// ── DOM refs ─────────────────────────────────────────────────────────────────
const canvas     = document.getElementById("avatar-canvas") as HTMLCanvasElement;
const bubble     = document.getElementById("speech-bubble") as HTMLDivElement;
const statusBar  = document.getElementById("status-bar") as HTMLDivElement;
const userInput  = document.getElementById("user-input") as HTMLInputElement;
const sendBtn    = document.getElementById("send-btn") as HTMLButtonElement;

// ── Components ────────────────────────────────────────────────────────────────
const avatar = new AvatarRenderer(canvas, 8);

const typewriter = new Typewriter(bubble, {
  onMouthOpen:  () => avatar.setMouthOpen(true),
  onMouthClose: () => avatar.setMouthOpen(false),
  onDone:       () => { sendBtn.disabled = false; },
});

// ── SSE connection ────────────────────────────────────────────────────────────
let reconnectDelay = 3000;

async function connectSSE() {
  const url = await window.avatarBridge.getSseUrl();
  const es = new EventSource(url);

  es.onmessage = (e: MessageEvent) => {
    try {
      const event = JSON.parse(e.data as string) as UIEvent;
      reconnectDelay = 3000; // reset backoff on successful message
      handleEvent(event);
    } catch {
      console.error("Failed to parse SSE event", e.data);
    }
  };

  es.onerror = () => {
    setStatus("error", "Bridge に接続できません。再接続中...");
    es.close();
    setTimeout(() => {
      reconnectDelay = Math.min(reconnectDelay * 2, 30_000);
      connectSSE();
    }, reconnectDelay);
  };
}

function handleEvent(event: UIEvent) {
  switch (event.type) {
    case "render":  handleRender(event);  break;
    case "status":  handleStatus(event);  break;
    case "result":  handleResult(event);  break;
  }
}

function handleRender(event: RenderEvent) {
  sendBtn.disabled = true;
  avatar.setEmotion(event.emotion);
  if (event.motion !== "none") avatar.playMotion(event.motion);
  typewriter.play(event.text);
}

function handleStatus(event: StatusEvent) {
  setStatus(event.state, event.message);
}

function handleResult(event: ResultEvent) {
  const detail = event.details ? `\n${event.details}` : "";
  bubble.textContent = `[結果] ${event.summary}${detail}`;
}

function setStatus(state: "running" | "idle" | "error", message: string) {
  statusBar.textContent = message;
  statusBar.className = state === "error" ? "error" : "";
}

// ── Input handling ────────────────────────────────────────────────────────────
async function sendMessage() {
  const msg = userInput.value.trim();
  if (!msg) return;

  sendBtn.disabled = true;
  userInput.value = "";
  bubble.textContent = "...";

  const ok = await window.avatarBridge.sendMessage(msg);
  if (!ok) {
    setStatus("error", "送信に失敗しました");
    sendBtn.disabled = false;
  }
}

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// ── Boot ──────────────────────────────────────────────────────────────────────
connectSSE();
bubble.textContent = "こんにちは！話しかけてみてください。";
