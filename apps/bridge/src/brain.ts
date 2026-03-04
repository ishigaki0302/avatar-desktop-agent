/**
 * Brain: wraps Ollama REST API (Qwen3.5-2B) with streaming.
 *
 * Streaming flow:
 *  1. callOllamaStream() yields tokens from Ollama (stream:true, think:false)
 *  2. Buffer tokens; detect emotion/motion → broadcast render_start
 *  3. Stream text field chars → broadcast render_token
 *  4. broadcast render_end when text field is complete
 *  5. Parse full buffer for memory_update / task (fire-and-forget)
 */
import type { UIEvent, Emotion, Motion } from "@avatar-agent/schema";
import { isValidEmotion, isValidMotion } from "@avatar-agent/schema";
import { config, createLogger, extractJSON, truncate } from "@avatar-agent/utils";
import { readMemory, applyMemoryUpdate } from "./memory.js";
import { delegateTask } from "./openclaw.js";
import type { SessionLogger } from "./session.js";

const log = createLogger("brain");

// ── Stub mode (STUB_MODE=1 で Ollama なしで UI 確認可能) ──────────────────────
const STUB_MODE = process.env["STUB_MODE"] === "1";
const STUB_RESPONSES: Array<{ text: string; emotion: Emotion; motion: Motion }> = [
  { text: "こんにちは！今日も良い一日ですね。何かお手伝いできることはありますか？", emotion: "happy",     motion: "wave"      },
  { text: "えっ！本当ですか？それは驚きました！もっと教えてください。",                 emotion: "surprised", motion: "nod"       },
  { text: "なるほど、わかりました。よろしくお願いします！",                             emotion: "happy",     motion: "bow_small" },
  { text: "そうなんですね！面白いですね。",                                             emotion: "surprised", motion: "nod"       },
];
let stubIndex = 0;

// ── Constants ─────────────────────────────────────────────────────────────────
const MAX_RETRIES = 2;
const MAX_HISTORY_MESSAGES = 10;

// ── Runtime model state ───────────────────────────────────────────────────────
let currentModel = config.ollama.model;

export function setModel(model: string): void {
  if (!config.ollama.availableModels.includes(model)) {
    throw new Error(`Unknown model: ${model}. Available: ${config.ollama.availableModels.join(", ")}`);
  }
  currentModel = model;
  // Reset conversation history when switching models
  history.length = 0;
  log.info(`Model switched to: ${model}`);
}

export function getCurrentModel(): string {
  return currentModel;
}

// ── System prompt ─────────────────────────────────────────────────────────────
// NOTE: emotion/motion come BEFORE text so they are generated first.
// This lets us send render_start before streaming text tokens.
// Optimized for qwen3.5:2b + format:json
export const SYSTEM_PROMPT = `\
あなたは「アリス」、明るいデスクトップAIコンパニオン（20代女性）。
返答は必ず以下のJSON1行のみ。前後に一切のテキスト不要。
引用符は必ず半角ダブルクォート（"）を使う。全角引用符は使わない。

{"emotion":"値","motion":"値","text":"値","memory_update":"NOOP","task":null}

【emotion】happy / neutral / surprised / sad / confused のどれか1つ
【motion】wave=挨拶のみ / nod=相槌・共感 / shake=嫌がる・断る / bow_small=お礼 / none=その他
【text】口語体で1文・15〜35文字・絵文字禁止・！以外の記号禁止
【memory_update】名前や好みを教えてくれたとき "- キー: 値"、それ以外は必ず "NOOP"
【task】操作依頼のとき {"goal":"内容","constraints":{"no_credential":true,"allow_shell":false,"time_budget_sec":60}}、それ以外は必ず null

【例】
おはよう → {"emotion":"happy","motion":"wave","text":"おはよう！今日も一緒に楽しくやっていこうね！","memory_update":"NOOP","task":null}
疲れたな → {"emotion":"sad","motion":"nod","text":"お疲れさま、無理しないでゆっくり休んでね。","memory_update":"NOOP","task":null}
ありがとう → {"emotion":"happy","motion":"bow_small","text":"どういたしまして、また気軽に話しかけてね！","memory_update":"NOOP","task":null}
それは嫌だな → {"emotion":"confused","motion":"shake","text":"そっか、気持ちわかるよ、どうしたらいいかな。","memory_update":"NOOP","task":null}
コーヒーが好き → {"emotion":"happy","motion":"nod","text":"コーヒー好きなんだね、私も大好きだよ！","memory_update":"- 好きなもの: コーヒー","task":null}
名前は田中です → {"emotion":"happy","motion":"nod","text":"田中さんって言うんだね！よろしくね！","memory_update":"- 名前: 田中","task":null}
YouTube開いて → {"emotion":"happy","motion":"nod","text":"ちょっと待ってね、YouTubeを開いてみるね！","memory_update":"NOOP","task":{"goal":"ブラウザでYouTubeを開く","constraints":{"no_credential":true,"allow_shell":false,"time_budget_sec":60}}}`;

// ── JSON repair ───────────────────────────────────────────────────────────────
// qwen3.5:2b sometimes emits unquoted keys or uses 」 as a closing quote.
function repairJSON(s: string): string {
  // Replace Japanese closing quote 」 with "
  let out = s.replaceAll("」", '"');
  // Fix unquoted JSON keys (e.g. memory_update:"NOOP" → "memory_update":"NOOP")
  out = out.replace(/([{,]\s*)(emotion|motion|text|memory_update|task)(\s*:(?!\s*"))/g, '$1"$2"$3');
  // Fix bare NOOP value (memory_update:NOOP → memory_update":"NOOP)
  out = out.replace(/:(\s*)NOOP\b/g, ':"NOOP"');
  return out;
}

// ── Conversation history ───────────────────────────────────────────────────────
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const history: ChatMessage[] = [];

function trimHistory() {
  if (history.length > MAX_HISTORY_MESSAGES) {
    history.splice(0, history.length - MAX_HISTORY_MESSAGES);
  }
}

// ── Ollama metrics ────────────────────────────────────────────────────────────
interface OllamaMetrics {
  tokensPerSec?: number;
}

// ── Public API ────────────────────────────────────────────────────────────────
export async function ask(
  userMessage: string,
  broadcast: (event: UIEvent) => void,
  session?: SessionLogger,
): Promise<void> {
  if (STUB_MODE) {
    log.info(`[STUB] responding to: "${userMessage}"`);
    const response = STUB_RESPONSES[stubIndex % STUB_RESPONSES.length]!;
    stubIndex++;
    broadcast({ type: "render_start", emotion: response.emotion, motion: response.motion });
    for (const char of response.text) {
      broadcast({ type: "render_token", token: char });
    }
    broadcast({ type: "render_end" });
    return;
  }

  const memory = await readMemory();
  const systemWithMemory = memory
    ? `${SYSTEM_PROMPT}\n\n# Current memory\n${memory}`
    : SYSTEM_PROMPT;

  history.push({ role: "user", content: userMessage });
  trimHistory();

  const startMs = Date.now();

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const { text, emotion, motion, rawBuffer, tokensPerSec, ttftMs } = await streamOllamaResponse(
        systemWithMemory,
        history,
        broadcast,
      );

      // Parse full buffer for side-effects (memory, task)
      const parsed = extractJSON(repairJSON(rawBuffer));

      const taskField = parsed?.["task"];
      if (taskField && typeof taskField === "object") {
        const t = taskField as Record<string, unknown>;
        const goal = typeof t["goal"] === "string" ? t["goal"].trim() : "";
        if (goal) {
          broadcast({ type: "status", state: "running", message: `タスク実行中: ${truncate(goal, 40)}` });
          const summary = await delegateTask(goal);
          broadcast({ type: "result", summary, details: null });
        }
      }

      const memUpdate = parsed?.["memory_update"];
      if (typeof memUpdate === "string" && memUpdate !== "NOOP") {
        applyMemoryUpdate(memUpdate).catch((e) => log.warn("memory update failed", e));
      }

      history.push({ role: "assistant", content: rawBuffer });
      trimHistory();

      session?.logTurn({
        user: userMessage,
        assistant: text,
        emotion,
        motion,
        latency_ms: Date.now() - startMs,
        tokens_per_sec: tokensPerSec,
        ttft_ms: ttftMs,
      }).catch((e) => log.warn("session log failed", e));

      return;
    } catch (err) {
      if (err instanceof TypeError && (err as TypeError).message.includes("fetch")) {
        broadcast({ type: "status", state: "error", message: "Ollama に接続できません" });
      }
      log.warn(`Attempt ${attempt + 1} error`, err);
    }
  }

  log.error("All retries exhausted, using fallback");
  const fallbackText = "すみません、うまく応答できませんでした。もう一度お試しください。";
  broadcast({ type: "render_start", emotion: "confused", motion: "none" });
  for (const char of fallbackText) {
    broadcast({ type: "render_token", token: char });
  }
  broadcast({ type: "render_end" });

  session?.logTurn({
    user: userMessage,
    assistant: fallbackText,
    emotion: "confused",
    motion: "none",
    latency_ms: Date.now() - startMs,
  }).catch((e) => log.warn("session log failed", e));
}

/** Expose history for testing */
export function getHistory(): Readonly<ChatMessage[]> {
  return history;
}

/** Reset history (for testing) */
export function resetHistory(): void {
  history.length = 0;
}

// ── Streaming response parser ──────────────────────────────────────────────────
async function streamOllamaResponse(
  system: string,
  messages: ChatMessage[],
  broadcast: (event: UIEvent) => void,
): Promise<{ text: string; emotion: Emotion; motion: Motion; rawBuffer: string; tokensPerSec?: number; ttftMs?: number }> {
  let buffer = "";
  let emotion: Emotion = "neutral";
  let motion: Motion = "none";
  let renderStartSent = false;
  let textValueStart = -1; // index in buffer right after '"text":"'
  let textValueEnd = -1;   // index in buffer of the closing '"' of text value
  let textStreamPos = 0;   // chars of text already sent as render_token
  let accumulatedText = "";
  let ttftMs: number | undefined;
  let isFirstToken = true;
  const streamStartMs = Date.now();

  const TEXT_MARKER_RE = /"text"\s*:\s*"/;

  const gen = callOllamaStream(system, messages);
  let next = await gen.next();

  while (!next.done) {
    const token = next.value;

    if (isFirstToken) {
      ttftMs = Date.now() - streamStartMs;
      isFirstToken = false;
    }

    buffer += token;

    // 1. Detect emotion and motion → send render_start
    if (!renderStartSent) {
      const eMatch = buffer.match(/"emotion"\s*:\s*"([^"]+)"/);
      const mMatch = buffer.match(/"motion"\s*:\s*"([^"]+)"/);
      if (eMatch && mMatch) {
        emotion = isValidEmotion(eMatch[1]) ? eMatch[1] as Emotion : "neutral";
        motion = isValidMotion(mMatch[1]) ? mMatch[1] as Motion : "none";
        broadcast({ type: "render_start", emotion, motion });
        renderStartSent = true;
      }
    }

    // 2. Find start of text field value (handle optional whitespace after colon)
    if (textValueStart === -1) {
      const m = TEXT_MARKER_RE.exec(buffer);
      if (m) textValueStart = m.index + m[0].length;
    }

    // 3. Stream text characters one by one
    if (renderStartSent && textValueStart !== -1 && textValueEnd === -1) {
      const from = textValueStart + textStreamPos;
      for (let i = from; i < buffer.length; i++) {
        const char = buffer[i]!;
        if (char === "\\") {
          if (i + 1 >= buffer.length) break; // wait for next token
          const next2 = buffer[i + 1]!;
          const actual =
            next2 === "n" ? "\n" :
            next2 === "t" ? "\t" :
            next2 === '"' ? '"' :
            next2;
          broadcast({ type: "render_token", token: actual });
          accumulatedText += actual;
          textStreamPos += 2;
          i++; // skip escaped char
        } else if (char === '"') {
          textValueEnd = i;
          break;
        } else {
          broadcast({ type: "render_token", token: char });
          accumulatedText += char;
          textStreamPos++;
        }
      }
    }

    next = await gen.next();
  }

  const metrics: OllamaMetrics = next.value;

  // Fallback: if render_start was never sent (model didn't output emotion/motion early enough)
  if (!renderStartSent) {
    const parsed = extractJSON(repairJSON(buffer));
    if (parsed) {
      emotion = isValidEmotion(parsed["emotion"]) ? parsed["emotion"] as Emotion : "neutral";
      motion = isValidMotion(parsed["motion"]) ? parsed["motion"] as Motion : "none";
      const rawText = typeof parsed["text"] === "string" ? parsed["text"].trim() : "";
      accumulatedText = rawText;
    }
    broadcast({ type: "render_start", emotion, motion });
    for (const char of accumulatedText) {
      broadcast({ type: "render_token", token: char });
    }
  }

  broadcast({ type: "render_end" });

  if (!accumulatedText) {
    throw new Error("No text extracted from stream");
  }

  log.debug("Stream complete", { chars: accumulatedText.length, emotion, motion, tokensPerSec: metrics.tokensPerSec, ttftMs });
  return { text: accumulatedText, emotion, motion, rawBuffer: buffer, tokensPerSec: metrics.tokensPerSec, ttftMs };
}

// ── Ollama streaming REST call ────────────────────────────────────────────────
async function* callOllamaStream(
  system: string,
  messages: ChatMessage[],
): AsyncGenerator<string, OllamaMetrics> {
  const url = `${config.ollama.baseUrl}/api/chat`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: currentModel,
      stream: true,
      think: false,
      format: "json",
      messages: [
        { role: "system", content: system },
        ...messages,
      ],

      options: {
        temperature: 0.75,
        num_predict: config.ollama.maxPredictTokens,
      },
    }),
    signal: AbortSignal.timeout(config.ollama.timeoutMs),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Ollama ${res.status}: ${truncate(body, 200)}`);
  }

  if (!res.body) throw new Error("Ollama response has no body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let metrics: OllamaMetrics = {};

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const lines = decoder.decode(value, { stream: true }).split("\n");
      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const data = JSON.parse(line) as {
            message?: { content?: string };
            done?: boolean;
            eval_count?: number;
            eval_duration?: number;
          };
          if (data.message?.content) yield data.message.content;
          if (data.done) {
            const ec = data.eval_count;
            const ed = data.eval_duration;
            metrics = {
              tokensPerSec: ec && ed ? ec / (ed / 1e9) : undefined,
            };
            return metrics;
          }
        } catch {
          // partial line; will be completed in next chunk
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  return metrics;
}
