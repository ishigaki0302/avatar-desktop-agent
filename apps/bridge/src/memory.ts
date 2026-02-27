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
