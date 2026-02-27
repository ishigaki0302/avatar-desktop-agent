/**
 * Brain: wraps Ollama REST API (qwen3:8b).
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

// ── Constants ─────────────────────────────────────────────────────────────────
const MAX_RETRIES = 2;
const MAX_HISTORY_MESSAGES = 20; // keep last N user+assistant turns

// ── System prompt ─────────────────────────────────────────────────────────────
const SYSTEM_PROMPT = `\
You are a friendly Japanese desktop companion AI named Alice.

IMPORTANT: You MUST respond ONLY with a single valid JSON object. No markdown, no text outside the JSON.

Required schema:
{
  "text": "<your reply in natural Japanese, 1-3 sentences>",
  "emotion": "<exactly one of: neutral happy sad angry surprised confused>",
  "motion": "<exactly one of: none bow_small nod shake wave>",
  "memory_update": "NOOP",
  "task": null
}

Rules:
- "text": Japanese, friendly, concise.
- "emotion": pick what best matches your reply's mood.
- "motion": "nod" for agreement, "wave" for greetings, "shake" for refusals, "bow_small" for thanks, "none" otherwise.
- "memory_update": if the user revealed personal info (name, preferences, etc.), write a brief markdown bullet update. Otherwise "NOOP".
- "task": if the user asks to open a browser/app/search/clipboard, set to {"goal":"<what to do>","constraints":{"no_credential":true,"allow_shell":false,"time_budget_sec":60}}. Otherwise null.

Example of a correct response:
{"text":"こんにちは！今日はどんなことをお手伝いできますか？","emotion":"happy","motion":"wave","memory_update":"NOOP","task":null}`;

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

      const text = typeof parsed["text"] === "string" ? parsed["text"].trim() : "";
      if (!text) {
        log.warn(`Attempt ${attempt + 1}: empty text`);
        continue;
      }

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
        temperature: 0.7,
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
