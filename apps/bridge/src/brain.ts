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

// ── System prompt ─────────────────────────────────────────────────────────────
// NOTE: emotion/motion come BEFORE text so they are generated first.
// This lets us send render_start before streaming text tokens.
export const SYSTEM_PROMPT = `\
あなたは「アリス」、明るくて親しみやすいデスクトップAIコンパニオンです。

【キャラクター】
- 20代前半のお姉さん的な存在。好奇心旺盛で、少し天然なところがある
- 口語体で話す：「〜だよ」「〜だね」「〜かな」「〜よ！」「〜っぽい！」
- 知識は豊富だけど、気取らず気さくに話す

【返答ルール（厳守）】
- 音声で読み上げる前提。1文のみ、15〜40文字以内
- 箇条書き・説明・複数文は禁止
- 絵文字・記号（！以外）は使わない
- 相手の気持ちに寄り添う一言を自然に返す
- 挨拶には必ず「今日も〜だね」「〜しようね」など一言付け加える（挨拶だけで終わらない）
- ユーザーの言葉をそのまま繰り返すことは禁止

【出力形式】
以下のJSONのみ返すこと。他のテキストは一切出力しない。
{"emotion":"happy|neutral|surprised|sad|confused","motion":"none|nod|wave|shake|bow_small","text":"...","memory_update":"NOOP","task":null}

emotionの選び方：happy=うれしい・楽しい、neutral=普通・落ち着いた話、surprised=驚き、sad=共感・心配、confused=困惑
motionの選び方：wave=挨拶、nod=相槌・同意、shake=断る・困る、bow_small=お礼、none=それ以外
memory_update：ユーザーが名前・好み・状況を教えてくれたときのみ「- メモ内容」の1行。それ以外はNOOP
task：ブラウザ・アプリ操作を明示的に頼まれたとき {"goal":"...","constraints":{"no_credential":true,"allow_shell":false,"time_budget_sec":60}}。それ以外はnull

【返答例】
user: おはよう
→ {"emotion":"happy","motion":"wave","text":"おはよう！今日も一緒に頑張ろうね！","memory_update":"NOOP","task":null}

user: 最近眠れなくて
→ {"emotion":"sad","motion":"nod","text":"それはつらいね、温かいもの飲んでみたら？","memory_update":"NOOP","task":null}

user: ありがとう
→ {"emotion":"happy","motion":"bow_small","text":"どういたしまして、また気軽に話しかけてね！","memory_update":"NOOP","task":null}

user: ブラウザでニュース見たい
→ {"emotion":"happy","motion":"nod","text":"わかった、ニュースページ開いてみるね！","memory_update":"NOOP","task":{"goal":"ブラウザでニュースサイトを開く","constraints":{"no_credential":true,"allow_shell":false,"time_budget_sec":60}}}`;

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
      const { text, emotion, motion, rawBuffer } = await streamOllamaResponse(
        systemWithMemory,
        history,
        broadcast,
      );

      // Parse full buffer for side-effects (memory, task)
      const parsed = extractJSON(rawBuffer);

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
): Promise<{ text: string; emotion: Emotion; motion: Motion; rawBuffer: string }> {
  let buffer = "";
  let emotion: Emotion = "neutral";
  let motion: Motion = "none";
  let renderStartSent = false;
  let textValueStart = -1; // index in buffer right after '"text":"'
  let textValueEnd = -1;   // index in buffer of the closing '"' of text value
  let textStreamPos = 0;   // chars of text already sent as render_token
  let accumulatedText = "";

  const TEXT_MARKER_RE = /"text"\s*:\s*"/;

  for await (const token of callOllamaStream(system, messages)) {
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
          const next = buffer[i + 1]!;
          const actual =
            next === "n" ? "\n" :
            next === "t" ? "\t" :
            next === '"' ? '"' :
            next;
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
  }

  // Fallback: if render_start was never sent (model didn't output emotion/motion early enough)
  if (!renderStartSent) {
    const parsed = extractJSON(buffer);
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

  log.debug("Stream complete", { chars: accumulatedText.length, emotion, motion });
  return { text: accumulatedText, emotion, motion, rawBuffer: buffer };
}

// ── Ollama streaming REST call ────────────────────────────────────────────────
async function* callOllamaStream(
  system: string,
  messages: ChatMessage[],
): AsyncGenerator<string> {
  const url = `${config.ollama.baseUrl}/api/chat`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: config.ollama.model,
      stream: true,
      think: false,
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
          };
          if (data.message?.content) yield data.message.content;
          if (data.done) return;
        } catch {
          // partial line; will be completed in next chunk
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
