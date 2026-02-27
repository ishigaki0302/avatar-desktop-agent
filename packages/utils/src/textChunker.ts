/**
 * Truncate text to maxChars, appending a suffix if cut.
 */
export function truncate(text: string, maxChars: number, suffix = "…"): string {
  if (text.length <= maxChars) return text;
  return text.slice(0, maxChars - suffix.length) + suffix;
}

/**
 * Split text into chunks of roughly chunkSize characters, breaking at sentence
 * boundaries where possible.
 */
export function chunkBySentence(text: string, chunkSize = 500): string[] {
  const sentences = text.split(/(?<=[。.!?！？\n])/u);
  const chunks: string[] = [];
  let current = "";
  for (const s of sentences) {
    if (current.length + s.length > chunkSize && current.length > 0) {
      chunks.push(current.trim());
      current = s;
    } else {
      current += s;
    }
  }
  if (current.trim()) chunks.push(current.trim());
  return chunks;
}

/**
 * Strip LLM noise from a raw response string before JSON extraction.
 *
 * Handles:
 *  - qwen3 <think>…</think> reasoning blocks
 *  - Markdown code fences: ```json … ``` or ``` … ```
 *  - Leading/trailing whitespace
 */
export function stripLLMNoise(text: string): string {
  // Remove <think>…</think> blocks (qwen3 chain-of-thought)
  let cleaned = text.replace(/<think>[\s\S]*?<\/think>/gi, "");
  // Remove markdown code fences (```json or ```)
  cleaned = cleaned.replace(/```(?:json)?\s*([\s\S]*?)\s*```/g, "$1");
  return cleaned.trim();
}

/**
 * Extract the first JSON object found inside a string.
 *
 * Tries in order:
 *  1. Parse the whole (stripped) string as JSON
 *  2. Find the first { … } block via bracket matching
 *
 * Returns null if no valid JSON object is found.
 */
export function extractJSON(text: string): Record<string, unknown> | null {
  const cleaned = stripLLMNoise(text);

  // Fast path: entire content is already valid JSON
  if (cleaned.startsWith("{")) {
    try {
      return JSON.parse(cleaned) as Record<string, unknown>;
    } catch {
      // fall through to bracket search
    }
  }

  // Bracket-match search
  const start = cleaned.indexOf("{");
  if (start === -1) return null;

  let depth = 0;
  let inString = false;
  let escape = false;

  for (let i = start; i < cleaned.length; i++) {
    const ch = cleaned[i]!;

    if (escape) { escape = false; continue; }
    if (ch === "\\" && inString) { escape = true; continue; }
    if (ch === '"') { inString = !inString; continue; }
    if (inString) continue;

    if (ch === "{") depth++;
    else if (ch === "}") {
      depth--;
      if (depth === 0) {
        try {
          return JSON.parse(cleaned.slice(start, i + 1)) as Record<string, unknown>;
        } catch {
          return null;
        }
      }
    }
  }
  return null;
}
