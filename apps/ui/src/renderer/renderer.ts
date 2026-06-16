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
      sendMessage: (msg: string) => Promise<{ ok: boolean; turnId: string | null }>;
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
const feedbackBar = document.getElementById("feedback-bar") as HTMLDivElement;

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

// ── Feedback (Phase 11) ─────────────────────────────────────────────────────
function clearFeedback() {
  feedbackBar.replaceChildren();
}

async function submitFeedback(turnId: string, rating: number, label: string, comment?: string) {
  try {
    await fetch(`${bridgeBase}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ turnId, rating, label, comment }),
    });
    clearFeedback();
    const thanks = document.createElement("span");
    thanks.className = "thanks";
    thanks.textContent = "フィードバックありがとう";
    feedbackBar.appendChild(thanks);
  } catch {
    setStatus("error", "フィードバック送信に失敗しました");
  }
}

function showCommentInput(turnId: string) {
  clearFeedback();
  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = "フィードバックを書く...";
  input.maxLength = 2000;
  const send = document.createElement("button");
  send.textContent = "送信";
  send.addEventListener("click", () => {
    const comment = input.value.trim();
    if (comment) submitFeedback(turnId, 3, "comment", comment);
  });
  feedbackBar.append(input, send);
  input.focus();
}

function showFeedbackButtons(turnId: string) {
  clearFeedback();
  const good = document.createElement("button");
  good.textContent = "👍";
  good.title = "良い";
  good.addEventListener("click", () => submitFeedback(turnId, 5, "helpful"));

  const bad = document.createElement("button");
  bad.textContent = "👎";
  bad.title = "微妙";
  bad.addEventListener("click", () => submitFeedback(turnId, 2, "not_helpful"));

  const note = document.createElement("button");
  note.textContent = "📝";
  note.title = "理由を書く";
  note.addEventListener("click", () => showCommentInput(turnId));

  feedbackBar.append(good, bad, note);
}

// ── Input handling ────────────────────────────────────────────────────────────
async function sendMessage() {
  const msg = userInput.value.trim();
  if (!msg) return;

  sendBtn.disabled = true;
  userInput.value = "";
  bubble.textContent = "...";
  clearFeedback();

  const result = await window.avatarBridge.sendMessage(msg);
  if (!result.ok) {
    setStatus("error", "送信に失敗しました");
    sendBtn.disabled = false;
    return;
  }
  // turnId is null when the agent service is down or in stub mode — skip feedback UI.
  if (result.turnId) showFeedbackButtons(result.turnId);
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
