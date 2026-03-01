/**
 * Brain: wraps Ollama REST API (granite4:3b).
 *
 * Always returns a RenderEvent. Internally:
 *  - Builds a system prompt with persona memory
 *  - Calls Ollama with format:"json" to get structured output
 *  - Strips <think>…</think> and markdown fences before JSON parsing
 *  - Retries up to MAX_RETRIES on malformed responses
 *  - Applies memory_update to user_profile.md if not "NOOP"
 *  - Delegates desktop tasks to OpenClaw if task field is set
 */
import type { RenderEvent, UIEvent } from "@avatar-agent/schema";
import { parseRenderEvent } from "@avatar-agent/schema";
import { config, createLogger, extractJSON, truncate } from "@avatar-agent/utils";
import { readMemory, applyMemoryUpdate } from "./memory.js";
import { delegateTask } from "./openclaw.js";

const log = createLogger("brain");

// ── Stub mode (STUB_MODE=1 で Ollama なしで UI 確認可能) ──────────────────────
const STUB_MODE = process.env["STUB_MODE"] === "1";
const STUB_RESPONSES: RenderEvent[] = [
  { type: "render", text: "こんにちは！今日も良い一日ですね。何かお手伝いできることはありますか？", emotion: "happy",     motion: "wave"      },
  { type: "render", text: "えっ！本当ですか？それは驚きました！もっと教えてください。",                 emotion: "surprised", motion: "nod"       },
  { type: "render", text: "なるほど、わかりました。よろしくお願いします！",                             emotion: "happy",     motion: "bow_small" },
  { type: "render", text: "そうなんですね！面白いですね。",                                             emotion: "surprised", motion: "nod"       },
];
let stubIndex = 0;

// ── Constants ─────────────────────────────────────────────────────────────────
const MAX_RETRIES = 2;
const MAX_HISTORY_MESSAGES = 10; // granite4:3b はコンテキストが短いため絞る

// ── System prompt ─────────────────────────────────────────────────────────────
const SYSTEM_PROMPT = `\
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
{"text":"...","emotion":"happy|neutral|surprised|sad|confused","motion":"none|nod|wave|shake|bow_small","memory_update":"NOOP","task":null}

emotionの選び方：happy=うれしい・楽しい、neutral=普通・落ち着いた話、surprised=驚き、sad=共感・心配、confused=困惑
motionの選び方：wave=挨拶、nod=相槌・同意、shake=断る・困る、bow_small=お礼、none=それ以外
memory_update：ユーザーが名前・好み・状況を教えてくれたときのみ「- メモ内容」の1行。それ以外はNOOP
task：ブラウザ・アプリ操作を明示的に頼まれたとき {"goal":"...","constraints":{"no_credential":true,"allow_shell":false,"time_budget_sec":60}}。それ以外はnull

【返答例】
user: おはよう
→ {"text":"おはよう！今日も一緒に頑張ろうね！","emotion":"happy","motion":"wave","memory_update":"NOOP","task":null}

user: 最近眠れなくて
→ {"text":"それはつらいね、温かいもの飲んでみたら？","emotion":"sad","motion":"nod","memory_update":"NOOP","task":null}

user: ありがとう
→ {"text":"どういたしまして、また気軽に話しかけてね！","emotion":"happy","motion":"bow_small","memory_update":"NOOP","task":null}

user: ブラウザでニュース見たい
→ {"text":"わかった、ニュースページ開いてみるね！","emotion":"happy","motion":"nod","memory_update":"NOOP","task":{"goal":"ブラウザでニュースサイトを開く","constraints":{"no_credential":true,"allow_shell":false,"time_budget_sec":60}}}`;

// ── Conversation history ───────────────────────────────────────────────────────
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const history: ChatMessage[] = [];

function trimHistory() {
  // Keep at most MAX_HISTORY_MESSAGES entries (user+assistant pairs)
  if (history.length > MAX_HISTORY_MESSAGES) {
    history.splice(0, history.length - MAX_HISTORY_MESSAGES);
  }
}

// ── Public API ────────────────────────────────────────────────────────────────
export async function ask(
  userMessage: string,
  broadcast: (event: UIEvent) => void,
): Promise<RenderEvent> {
  if (STUB_MODE) {
    log.info(`[STUB] responding to: "${userMessage}"`);
    const response = STUB_RESPONSES[stubIndex % STUB_RESPONSES.length]!;
    stubIndex++;
    return response;
  }

  const memory = await readMemory();
  const systemWithMemory = memory
    ? `${SYSTEM_PROMPT}\n\n# Current memory\n${memory}`
    : SYSTEM_PROMPT;

  history.push({ role: "user", content: userMessage });
  trimHistory();

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const raw = await callOllama(systemWithMemory, history);
      log.debug("Ollama raw", { attempt, length: raw.length });

      const parsed = extractJSON(raw);
      if (!parsed) {
        log.warn(`Attempt ${attempt + 1}: no JSON found`);
        continue;
      }

      const rawText = typeof parsed["text"] === "string" ? parsed["text"].trim() : "";
      if (!rawText) {
        log.warn(`Attempt ${attempt + 1}: empty text`);
        continue;
      }
      // 複数文が来た場合は1文目だけ使う（音声向け）
      const text = firstSentence(rawText);

      // Handle delegated task
      const taskField = parsed["task"];
      if (taskField && typeof taskField === "object") {
        const t = taskField as Record<string, unknown>;
        const goal = typeof t["goal"] === "string" ? t["goal"].trim() : "";
        if (goal) {
          broadcast({
            type: "status",
            state: "running",
            message: `タスク実行中: ${truncate(goal, 40)}`,
          });
          const summary = await delegateTask(goal);
          broadcast({ type: "result", summary, details: null });
        }
      }

      // Apply memory update asynchronously (fire-and-forget)
      const memUpdate = parsed["memory_update"];
      if (typeof memUpdate === "string" && memUpdate !== "NOOP") {
        applyMemoryUpdate(memUpdate).catch((e) =>
          log.warn("memory update failed", e),
        );
      }

      const renderEvent = parseRenderEvent({
        text,
        emotion: parsed["emotion"] as string,
        motion: parsed["motion"] as string,
      });

      history.push({ role: "assistant", content: JSON.stringify(parsed) });
      trimHistory();
      return renderEvent;
    } catch (err) {
      if (err instanceof TypeError && (err as TypeError).message.includes("fetch")) {
        broadcast({ type: "status", state: "error", message: "Ollama に接続できません" });
      }
      log.warn(`Attempt ${attempt + 1} error`, err);
    }
  }

  log.error("All retries exhausted, using fallback");
  history.push({
    role: "assistant",
    content: '{"text":"すみません、うまく応答できませんでした。","emotion":"confused","motion":"none","memory_update":"NOOP","task":null}',
  });
  return {
    type: "render",
    text: "すみません、うまく応答できませんでした。もう一度お試しください。",
    emotion: "confused",
    motion: "none",
  };
}

/** Expose history for testing */
export function getHistory(): Readonly<ChatMessage[]> {
  return history;
}

/** Reset history (for testing) */
export function resetHistory(): void {
  history.length = 0;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * 音声向けに1文目だけ返す。
 * - 末尾の閉じ括弧・記号ゴミを除去してからセンテンス分割
 * - 1文目が10文字未満なら全体を返す（例: 短い挨拶はそのまま）
 */
function firstSentence(text: string): string {
  // 末尾のゴミ文字（閉じ引用符・括弧・カンマなど）を除去
  const cleaned = text.replace(/[」』）\],;\s]+$/u, "").trim();
  const match = cleaned.match(/^.+?[。！？!?]/u);
  if (match && match[0] && match[0].length >= 10) return match[0];
  return cleaned;
}

// ── Ollama REST call ──────────────────────────────────────────────────────────
async function callOllama(system: string, messages: ChatMessage[]): Promise<string> {
  const url = `${config.ollama.baseUrl}/api/chat`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: config.ollama.model,
      stream: false,
      messages: [
        { role: "system", content: system },
        ...messages,
      ],
      format: "json",
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

  const data = await res.json() as { message?: { content?: string } };
  return data?.message?.content ?? "";
}
