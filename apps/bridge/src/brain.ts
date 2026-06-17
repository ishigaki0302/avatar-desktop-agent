/**
 * Brain: wraps Ollama REST API (default: Gemma 4 31B) with streaming.
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

// Result of a completed turn, surfaced so the bridge can log it to the agent service.
export interface TurnResult {
  user: string;
  assistant: string;
  emotion: Emotion;
  motion: Motion;
  latencyMs: number;
}

// ── Runtime model state ───────────────────────────────────────────────────────
let currentModel = config.ollama.model;

export function setModel(model: string): void {
  if (config.brainBackend === "remote-gpu") {
    throw new Error("Model switching is not supported for remote-gpu backend");
  }
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
// Designed for Ollama format:json output (Gemma 4 31B 標準、他モデルにも流用可)
export const SYSTEM_PROMPT = `\
あなたは「アリス」、明るいデスクトップAIコンパニオン（20代女性）。
返答は必ず以下のJSON1行のみ。前後に一切のテキスト不要。
引用符は必ず半角ダブルクォート（"）を使う。全角引用符は使わない。

{"emotion":"値","motion":"値","text":"値","memory_update":"NOOP"}

【emotion】happy / neutral / surprised / sad / confused のどれか1つ
【motion】wave=挨拶のみ / nod=相槌・共感 / shake=嫌がる・断る / bow_small=お礼 / none=その他
【text】口語体で1文・15〜35文字・絵文字禁止・！以外の記号禁止（ツール結果がある場合は別途指示に従い長め・記号可）
【memory_update】名前や好みを教えてくれたとき "- キー: 値"、それ以外は必ず "NOOP"

【例】
おはよう → {"emotion":"happy","motion":"wave","text":"おはよう！今日も一緒に楽しくやっていこうね！","memory_update":"NOOP"}
疲れたな → {"emotion":"sad","motion":"nod","text":"お疲れさま、無理しないでゆっくり休んでね。","memory_update":"NOOP"}
ありがとう → {"emotion":"happy","motion":"bow_small","text":"どういたしまして、また気軽に話しかけてね！","memory_update":"NOOP"}
それは嫌だな → {"emotion":"confused","motion":"shake","text":"そっか、気持ちわかるよ、どうしたらいいかな。","memory_update":"NOOP"}
コーヒーが好き → {"emotion":"happy","motion":"nod","text":"コーヒー好きなんだね、私も大好きだよ！","memory_update":"- 好きなもの: コーヒー"}
名前は田中です → {"emotion":"happy","motion":"nod","text":"田中さんって言うんだね！よろしくね！","memory_update":"- 名前: 田中"}`;

// ── JSON repair ───────────────────────────────────────────────────────────────
// ローカル LLM は稀にキー無引用符や全角引用符 」 を吐くため、保険として補修する。
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

// ── Tool use: plan → execute (Python agent) → ground the answer (#69) ──────────
const TOOL_USE_ENABLED = process.env["TOOL_USE_ENABLED"] !== "0";
const MAX_TOOL_CALLS = 2;
const MAX_AGENT_STEPS = 3;
const TOOL_EXEC_TIMEOUT_MS = 30_000;
const TOOL_OUTPUT_MAX = 1500;

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
}

const AGENT_STEP_PROMPT = `\
あなたはツール使用エージェント。ユーザーに答えるため、必要なら複数回ツールを使う。
会話履歴と「これまでに試したツールと結果(引数つき)」を踏まえ、次の行動をJSON1行で返す: {"tool_calls":[{"name":"...","args":{...}}]}
すぐ諦めないこと:
- 既に試した tool+引数と同じものは絶対に繰り返さない（同じ検索の連発は禁止）
- 結果が空/不十分なら、必ず引数を変える・条件を広げる・別ツールに切り替える
  例) filesystem.search '*自己紹介*.pptx' が空 → '*.pptx' に広げて候補を出す / web.search の後は browser.read で本文取得
- 十分な情報が集まった、または挨拶・雑談・これ以上手段が無い場合のみ {"tool_calls":[]}

使えるツール:
- weather {"location":"都市名(空で現在地)"} : 天気・気温
- web.search {"query":"検索語"} : 最新情報・ニュース・事実確認
- browser.read {"url":"https://..."} : 特定URLの本文取得
- filesystem.search {"pattern":"*.pptx"} : PC内のファイルを名前/拡張子で探す
- filesystem.list {"path":"."} / filesystem.read {"path":"..."} : 一覧・読取
- memory.search {"query":"語"} : 過去の記憶を検索`;

/** Parse the planner's JSON into at most MAX_TOOL_CALLS valid tool calls. Pure (tested). */
export function parseToolCalls(raw: string): ToolCall[] {
  const parsed = extractJSON(repairJSON(raw));
  const calls = parsed?.["tool_calls"];
  if (!Array.isArray(calls)) return [];
  const out: ToolCall[] = [];
  for (const c of calls) {
    if (c && typeof c === "object" && typeof (c as Record<string, unknown>)["name"] === "string") {
      const rec = c as Record<string, unknown>;
      const args = rec["args"];
      out.push({ name: rec["name"] as string, args: (args && typeof args === "object" ? args : {}) as Record<string, unknown> });
    }
    if (out.length >= MAX_TOOL_CALLS) break;
  }
  return out;
}

async function callOllamaJSON(system: string, messages: ChatMessage[]): Promise<string> {
  const res = await fetch(`${config.ollama.baseUrl}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: currentModel,
      stream: false,
      think: false,
      format: "json",
      messages: [{ role: "system", content: system }, ...messages],
      options: { temperature: 0, num_predict: 200 },
    }),
    signal: AbortSignal.timeout(config.ollama.timeoutMs),
  });
  if (!res.ok) throw new Error(`Ollama ${res.status}`);
  const data = await res.json() as { message?: { content?: string } };
  return data.message?.content ?? "";
}

/**
 * Multi-step agentic loop: repeatedly let the LLM pick tools, run them, and
 * feed results back so it can retry with different args/tools when a result is
 * empty or insufficient — instead of giving up after one try. Returns the
 * accumulated tool-result transcript (empty string if no tools were used).
 */
async function runAgentLoop(broadcast: (event: UIEvent) => void, turnId: string | null): Promise<string> {
  const transcript: string[] = [];
  for (let step = 0; step < MAX_AGENT_STEPS; step++) {
    // Give the planner the conversation history (so follow-ups have context) plus
    // exactly what was already tried with which args (so it doesn't repeat).
    const stepMessages: ChatMessage[] = history.slice(-MAX_HISTORY_MESSAGES).map((m) => ({ ...m }));
    if (transcript.length > 0) {
      stepMessages.push({
        role: "user",
        content:
          "# これまでに試したツールと結果（同じ tool+引数は繰り返さない。空なら引数を変える/広げる）\n" +
          transcript.join("\n\n"),
      });
    }
    let calls: ToolCall[];
    try {
      calls = parseToolCalls(await callOllamaJSON(AGENT_STEP_PROMPT, stepMessages));
    } catch (e) {
      log.warn("agent step failed", e);
      break;
    }
    if (calls.length === 0) break;
    const result = await executeTools(calls, broadcast, turnId);
    transcript.push(result || `(ツール ${calls.map((c) => c.name).join(", ")} は結果なし)`);
  }
  return transcript.join("\n\n");
}

/** Execute planned tools via the Python agent service. Read-only web is auto-confirmed. */
async function executeTools(
  calls: ToolCall[],
  broadcast: (event: UIEvent) => void,
  turnId: string | null,
): Promise<string> {
  const base = config.agentService.baseUrl;
  const blocks: string[] = [];
  for (const call of calls) {
    broadcast({ type: "status", state: "running", message: `ツール実行中: ${call.name}` });
    try {
      const res = await fetch(`${base}/tools/${call.name}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ args: call.args, confirm: true, turn_id: turnId }),
        signal: AbortSignal.timeout(TOOL_EXEC_TIMEOUT_MS),
      });
      if (!res.ok) continue;
      const data = await res.json() as { ok: boolean; output?: unknown; error?: string };
      // Include the args so the planner can see exactly what was already tried.
      const head = `## ${call.name} ${JSON.stringify(call.args)}`;
      blocks.push(data.ok
        ? `${head}\n${truncate(JSON.stringify(data.output), TOOL_OUTPUT_MAX)}`
        : `${head}: エラー ${data.error ?? ""}`);
    } catch (e) {
      log.warn(`tool ${call.name} failed`, e);
    }
  }
  return blocks.join("\n\n");
}

// ── Public API ────────────────────────────────────────────────────────────────
export async function ask(
  userMessage: string,
  broadcast: (event: UIEvent) => void,
  session?: SessionLogger,
  turnId: string | null = null,
): Promise<TurnResult | null> {
  if (STUB_MODE) {
    log.info(`[STUB] responding to: "${userMessage}"`);
    const response = STUB_RESPONSES[stubIndex % STUB_RESPONSES.length]!;
    stubIndex++;
    broadcast({ type: "render_start", emotion: response.emotion, motion: response.motion });
    for (const char of response.text) {
      broadcast({ type: "render_token", token: char });
    }
    broadcast({ type: "render_end" });
    return null;
  }

  const memory = await readMemory();
  const systemWithMemory = memory
    ? `${SYSTEM_PROMPT}\n\n# Current memory\n${memory}`
    : SYSTEM_PROMPT;

  history.push({ role: "user", content: userMessage });
  trimHistory();

  // Agentic tool use: multi-step loop (retries with different tools/args), then
  // ground the answer in the accumulated results.
  let systemPrompt = systemWithMemory;
  if (TOOL_USE_ENABLED && config.brainBackend === "ollama") {
    const toolContext = await runAgentLoop(broadcast, turnId);
    if (toolContext) {
      // Tool results often contain paths/URLs/numbers, so relax the short-answer
      // format: allow longer text and symbols (/ . : etc.) to report specifics.
      systemPrompt =
        `${systemWithMemory}\n\n# ツール実行結果(この事実に基づいて具体的に答える)\n${toolContext}\n\n` +
        "※この結果を使うときは text の制約を緩める: 40〜140文字可、ファイルパス・URL・数値・記号を含めてよい。" +
        "見つかったファイル名やパスは具体的に答える。該当が無ければ正直に無いと言う。";
    }
  }

  const startMs = Date.now();

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const { text, emotion, motion, rawBuffer, tokensPerSec, ttftMs } = await streamOllamaResponse(
        systemPrompt,
        history,
        broadcast,
      );

      // Parse full buffer for side-effects (memory). Actions go through the
      // tool-calling loop now; the legacy OpenClaw `task` path was removed.
      const parsed = extractJSON(repairJSON(rawBuffer));

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

      return { user: userMessage, assistant: text, emotion, motion, latencyMs: Date.now() - startMs };
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

  return { user: userMessage, assistant: fallbackText, emotion: "confused", motion: "none", latencyMs: Date.now() - startMs };
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

  if (config.brainBackend === "remote-gpu") {
    return callRemoteGpuResponse(system, messages, broadcast);
  }

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

// ── Remote GPU (non-streaming) REST call ──────────────────────────────────────
async function callRemoteGpuResponse(
  system: string,
  messages: ChatMessage[],
  broadcast: (event: UIEvent) => void,
): Promise<{ text: string; emotion: Emotion; motion: Motion; rawBuffer: string; tokensPerSec?: number; ttftMs?: number }> {
  const { baseUrl, maxNewTokens, temperature, timeoutMs } = config.remoteGpu;

  // Build prompt: system + conversation history as plain text
  const historyText = messages
    .map((m) => (m.role === "user" ? `ユーザー: ${m.content}` : `アシスタント: ${m.content}`))
    .join("\n");
  const prompt = `${system}\n\n${historyText}\nアシスタント:`;

  const startMs = Date.now();

  const res = await fetch(`${baseUrl}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      max_new_tokens: maxNewTokens,
      temperature,
      do_sample: temperature > 0,
    }),
    signal: AbortSignal.timeout(timeoutMs),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`remote-gpu ${res.status}: ${truncate(body, 200)}`);
  }

  const data = await res.json() as { generated_text: string; elapsed_sec?: number };
  const ttftMs = Date.now() - startMs;
  const rawBuffer = data.generated_text.trim();
  const tokensPerSec = data.elapsed_sec ? maxNewTokens / data.elapsed_sec : undefined;

  // Parse JSON from the generated text
  const parsed = extractJSON(repairJSON(rawBuffer));

  let emotion: Emotion = "neutral";
  let motion: Motion = "none";
  let accumulatedText = "";

  if (parsed) {
    emotion = isValidEmotion(parsed["emotion"]) ? parsed["emotion"] as Emotion : "neutral";
    motion = isValidMotion(parsed["motion"]) ? parsed["motion"] as Motion : "none";
    accumulatedText = typeof parsed["text"] === "string" ? parsed["text"].trim() : "";
  }

  // Use render event (not streaming events) so typewriter.play() handles
  // character-by-character timing and lipsync on the renderer side.
  broadcast({ type: "render", emotion, motion, text: accumulatedText });

  if (!accumulatedText) {
    throw new Error("No text extracted from remote-gpu response");
  }

  log.debug("remote-gpu complete", { chars: accumulatedText.length, emotion, motion, tokensPerSec, ttftMs });
  return { text: accumulatedText, emotion, motion, rawBuffer, tokensPerSec, ttftMs };
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
