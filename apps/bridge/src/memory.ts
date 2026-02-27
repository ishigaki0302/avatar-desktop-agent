/**
 * Lightweight file-based memory.
 * Reads persona.md + user_profile.md and returns combined context string.
 */
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { join } from "node:path";
import { config, createLogger, truncate } from "@avatar-agent/utils";

const log = createLogger("memory");
const MAX_MEMORY_CHARS = 2000;

export async function readMemory(): Promise<string> {
  const dir = config.memory.dir;
  const parts: string[] = [];

  for (const file of ["persona.md", "user_profile.md"]) {
    try {
      const text = await readFile(join(dir, file), "utf-8");
      parts.push(`## ${file}\n${text}`);
    } catch {
      // File may not exist yet; skip silently
    }
  }

  const combined = parts.join("\n\n");
  return truncate(combined, MAX_MEMORY_CHARS);
}

/**
 * Apply a memory diff returned by Brain.
 *
 * If diff is "NOOP" or blank, does nothing.
 * Otherwise, appends the diff to user_profile.md with a timestamp header.
 */
export async function applyMemoryUpdate(diff: string): Promise<void> {
  const trimmed = diff.trim();
  if (!trimmed || trimmed === "NOOP") return;

  const dir = config.memory.dir;
  const path = join(dir, "user_profile.md");

  try {
    await mkdir(dir, { recursive: true });
    const existing = await readFile(path, "utf-8").catch(() => "");
    const ts = new Date().toISOString().slice(0, 19).replace("T", " ");
    const updated = existing
      ? `${existing}\n\n<!-- updated ${ts} -->\n${trimmed}`
      : trimmed;
    await writeFile(path, updated, "utf-8");
    log.info("user_profile.md updated");
  } catch (err) {
    log.error("Failed to apply memory update", err);
  }
}

export async function writeEpisode(date: string, summary: string): Promise<void> {
  const dir = join(config.memory.dir, "episodes");
  try {
    await mkdir(dir, { recursive: true });
    const path = join(dir, `${date}.md`);
    const existing = await readFile(path, "utf-8").catch(() => "");
    const updated = existing
      ? `${existing}\n\n---\n\n${summary}`
      : summary;
    await writeFile(path, updated, "utf-8");
    log.info(`Episode written to ${path}`);
  } catch (err) {
    log.error("Failed to write episode", err);
  }
}
