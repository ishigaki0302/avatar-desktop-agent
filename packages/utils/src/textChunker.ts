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
 * Extract the first JSON object found inside a string.
 * Returns null if not found.
 */
export function extractJSON(text: string): Record<string, unknown> | null {
  const start = text.indexOf("{");
  if (start === -1) return null;
  // Find matching closing brace
  let depth = 0;
  for (let i = start; i < text.length; i++) {
    if (text[i] === "{") depth++;
    else if (text[i] === "}") {
      depth--;
      if (depth === 0) {
        try {
          return JSON.parse(text.slice(start, i + 1)) as Record<string, unknown>;
        } catch {
          return null;
        }
      }
    }
  }
  return null;
}
