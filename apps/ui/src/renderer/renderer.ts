/**
 * Renderer process entrypoint.
 * Connects to Bridge SSE, dispatches render/status/result events to UI components.
 */
import type { UIEvent, RenderEvent, RenderStartEvent, RenderTokenEvent, StatusEvent, ResultEvent } from "@avatar-agent/schema";
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
const canvas      = document.getElementById("avatar-canvas") as HTMLCanvasElement;
const bubble      = document.getElementById("speech-bubble") as HTMLDivElement;
const statusBar   = document.getElementById("status-bar") as HTMLDivElement;
const userInput   = document.getElementById("user-input") as HTMLInputElement;
const sendBtn     = document.getElementById("send-btn") as HTMLButtonElement;
const modelSelect = document.getElementById("model-select") as HTMLSelectElement;
const modelLabel  = document.getElementById("model-label") as HTMLSpanElement;

// ── Components ────────────────────────────────────────────────────────────────
const avatar = new AvatarRenderer(canvas, 8);

const typewriter = new Typewriter(bubble, {
  onMouthOpen:  () => avatar.setMouthOpen(true),
  onMouthClose: () => avatar.setMouthOpen(false),
  onDone:       () => { sendBtn.disabled = false; },
});

// ── Bridge base URL ───────────────────────────────────────────────────────────
let bridgeBase = "";

async function initBridgeBase() {
  const sseUrl = await window.avatarBridge.getSseUrl();
  bridgeBase = sseUrl.replace(/\/events$/, "");
}

// ── Model selector ────────────────────────────────────────────────────────────
async function loadModels() {
  try {
    const res = await fetch(`${bridgeBase}/models`);
    if (!res.ok) return;
    const data = await res.json() as { current: string; available: string[]; backend: string };
    if (data.backend === "remote-gpu") {
      modelSelect.style.display = "none";
      modelLabel.style.display = "inline";
      modelLabel.textContent = "remote-gpu";
      return;
    }
    modelSelect.innerHTML = "";
    for (const m of data.available) {
      const opt = document.createElement("option");
      opt.value = m;
      opt.textContent = m;
      if (m === data.current) opt.selected = true;
      modelSelect.appendChild(opt);
    }
  } catch {
    // Bridge not yet ready — ignore
  }
}

modelSelect.addEventListener("change", async () => {
  const model = modelSelect.value;
  try {
    await fetch(`${bridgeBase}/model`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model }),
    });
  } catch {
    setStatus("error", "モデル切替に失敗しました");
  }
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
    case "render":        handleRender(event);      break;
    case "render_start":  handleRenderStart(event); break;
    case "render_token":  handleRenderToken(event); break;
    case "render_end":    handleRenderEnd();        break;
    case "status":        handleStatus(event);      break;
    case "result":        handleResult(event);      break;
  }
}

function handleRender(event: RenderEvent) {
  sendBtn.disabled = true;
  avatar.setEmotion(event.emotion);
  if (event.motion !== "none") avatar.playMotion(event.motion);
  typewriter.play(event.text);
}

function handleRenderStart(event: RenderStartEvent) {
  sendBtn.disabled = true;
  avatar.setEmotion(event.emotion);
  if (event.motion !== "none") avatar.playMotion(event.motion);
  typewriter.startStream();
}

function handleRenderToken(event: RenderTokenEvent) {
  typewriter.appendToken(event.token);
}

function handleRenderEnd() {
  typewriter.endStream();
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
  if (e.key === "Enter" && e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// ── Boot ──────────────────────────────────────────────────────────────────────
initBridgeBase().then(() => {
  connectSSE();
  loadModels();
});
bubble.textContent = "こんにちは！話しかけてみてください。";
