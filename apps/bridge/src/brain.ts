/**
 * Brain: wraps Ollama REST API (qwen3:8b).
 *
 * System prompt instructs the model to ALWAYS return JSON:
 * {
 *   "text": "<reply>",
 *   "emotion": "<emotion>",
 *   "motion": "<motion>",
 *   "memory_update": "NOOP" | "<diff>",
 *   "task": null | { "goal": "...", "constraints": {...} }
 * }
 *
 * If the model returns malformed JSON, we retry up to MAX_RETRIES times.
 * If all retries fail, we return a fallback render event.
 */
import type { RenderEvent, UIEvent } from "@avatar-agent/schema";
import { parseRenderEvent } from "@avatar-agent/schema";
import { config, createLogger, extractJSON, truncate } from "@avatar-agent/utils";
import { readMemory } from "./memory.js";
import { delegateTask } from "./openclaw.js";

const log = createLogger("brain");
const MAX_RETRIES = 2;

const SYSTEM_PROMPT = `
You are a friendly desktop companion AI. You must ALWAYS reply in this exact JSON format (no markdown fences, no extra text outside the JSON):
{
  "text": "<your reply in Japanese>",
  "emotion": "<one of: neutral happy sad angry surprised confused>",
  "motion": "<one of: none bow_small nod shake wave>",
  "memory_update": "NOOP",
  "task": null
}
If the user asks you to perform a desktop task (open browser, search, launch app, etc.), set "task" to:
{
  "goal": "<describe what to do>",
  "constraints": { "no_credential": true, "allow_shell": false, "time_budget_sec": 60 }
}
Keep replies concise and natural. Choose emotion/motion to match the feeling of your reply.
`.trim();

interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

const conversationHistory: ChatMessage[] = [];

export async function ask(
  userMessage: string,
  broadcast: (event: UIEvent) => void,
): Promise<RenderEvent> {
  // Load memory context
  const memory = await readMemory();
  const systemWithMemory = `${SYSTEM_PROMPT}\n\n# Memory\n${memory}`;

  conversationHistory.push({ role: "user", content: userMessage });

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const raw = await callOllama(systemWithMemory, conversationHistory);
      log.debug("Ollama raw response", raw);

      const parsed = extractJSON(raw);
      if (!parsed) {
        log.warn(`Attempt ${attempt + 1}: No JSON found in response`);
        continue;
      }

      const text = typeof parsed["text"] === "string" ? parsed["text"] : "";
      if (!text) {
        log.warn(`Attempt ${attempt + 1}: Empty text in response`);
        continue;
      }

      // Check for delegated task
      if (parsed["task"] && typeof parsed["task"] === "object") {
        const taskObj = parsed["task"] as Record<string, unknown>;
        const goal = typeof taskObj["goal"] === "string" ? taskObj["goal"] : "";
        if (goal) {
          broadcast({ type: "status", state: "running", message: `タスク実行中: ${truncate(goal, 40)}` });
          const taskResult = await delegateTask(goal);
          broadcast({ type: "result", summary: taskResult, details: null });
        }
      }

      const renderEvent = parseRenderEvent({
        text,
        emotion: parsed["emotion"] as string,
        motion: parsed["motion"] as string,
        memory_update: parsed["memory_update"] as string,
      });

      conversationHistory.push({ role: "assistant", content: raw });
      return renderEvent;
    } catch (err) {
      log.warn(`Attempt ${attempt + 1} failed`, err);
      if (attempt === MAX_RETRIES) {
        log.error("All retries exhausted, returning fallback");
      }
    }
  }

  // Fallback
  conversationHistory.push({
    role: "assistant",
    content: JSON.stringify({
      text: "すみません、うまく応答できませんでした。もう一度お試しください。",
      emotion: "confused",
      motion: "none",
      memory_update: "NOOP",
      task: null,
    }),
  });

  return {
    type: "render",
    text: "すみません、うまく応答できませんでした。もう一度お試しください。",
    emotion: "confused",
    motion: "none",
  };
}

async function callOllama(system: string, messages: ChatMessage[]): Promise<string> {
  const url = `${config.ollama.baseUrl}/api/chat`;
  const body = {
    model: config.ollama.model,
    stream: false,
    messages: [
      { role: "system", content: system },
      ...messages,
    ],
    format: "json",
    options: {
      temperature: 0.7,
      num_predict: 512,
    },
  };

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(60_000),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Ollama error ${res.status}: ${truncate(errText, 200)}`);
  }

  const data = await res.json() as { message?: { content?: string } };
  const content = data?.message?.content ?? "";
  return content;
}
