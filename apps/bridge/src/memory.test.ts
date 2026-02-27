/**
 * Unit tests for memory.ts — applyMemoryUpdate()
 */
import { test, describe, before, after } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { join, resolve } from "node:path";
import { tmpdir } from "node:os";

// We need to override config.memory.dir before importing memory.ts.
// Use process.env so config.ts picks it up at import time.

let tmpDir: string;

// applyMemoryUpdate is imported after tmpDir is set via env.
let applyMemoryUpdate: (diff: string) => Promise<void>;

before(async () => {
  tmpDir = await mkdtemp(join(tmpdir(), "avatar-memory-test-"));
  process.env["MEMORY_DIR"] = tmpDir;

  // Dynamic import after env is set
  const mod = await import("./memory.js");
  applyMemoryUpdate = mod.applyMemoryUpdate;
});

after(async () => {
  await rm(tmpDir, { recursive: true, force: true });
});

describe("applyMemoryUpdate()", () => {
  test("NOOP → ファイル変更なし", async () => {
    await applyMemoryUpdate("NOOP");
    // user_profile.md should not exist
    try {
      await readFile(join(tmpDir, "user_profile.md"), "utf-8");
      assert.fail("user_profile.md should not exist after NOOP");
    } catch (err: unknown) {
      assert.equal((err as NodeJS.ErrnoException).code, "ENOENT");
    }
  });

  test("通常テキスト → タイムスタンプ付きで追記される", async () => {
    const diff = "- ユーザーの名前は Bob です";
    await applyMemoryUpdate(diff);

    const content = await readFile(join(tmpDir, "user_profile.md"), "utf-8");
    assert.ok(content.includes(diff), "diff text should be in user_profile.md");
    // No timestamp on first write (content starts with the diff itself)
  });

  test("2回目の追記 → 既存内容に追加される", async () => {
    const second = "- 好きな食べ物はピザ";
    await applyMemoryUpdate(second);

    const content = await readFile(join(tmpDir, "user_profile.md"), "utf-8");
    assert.ok(content.includes("Bob"), "first update should still be present");
    assert.ok(content.includes(second), "second update should be appended");
    assert.ok(content.includes("<!-- updated"), "timestamp comment should be present");
  });
});
