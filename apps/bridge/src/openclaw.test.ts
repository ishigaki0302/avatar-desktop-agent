/**
 * Unit tests for openclaw.ts
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { isAllowed, summarizeLog } from "./openclaw.js";

// ── isAllowed() ──────────────────────────────────────────────────────────────

describe("isAllowed()", () => {
  // Allow cases
  test("allows a normal browser search goal", () => {
    assert.equal(isAllowed("ブラウザで天気を検索してください"), true);
  });

  test("allows opening an app", () => {
    assert.equal(isAllowed("Spotify を起動してください"), true);
  });

  test("allows clipboard read request", () => {
    assert.equal(isAllowed("クリップボードの内容を読み取ってください"), true);
  });

  // Deny cases
  test("blocks rm command", () => {
    assert.equal(isAllowed("rm -rf /tmp/test"), false);
  });

  test("blocks sudo usage", () => {
    assert.equal(isAllowed("sudo apt-get install curl"), false);
  });

  test("blocks credential keyword", () => {
    assert.equal(isAllowed("fetch my credential from keychain"), false);
  });
});

// ── summarizeLog() ───────────────────────────────────────────────────────────

describe("summarizeLog()", () => {
  test("returns short log unchanged (within 500 chars)", () => {
    // No error/success/result keywords → all lines returned as-is
    const log = "step 1 done\nstep 2 done\nstep 3 done";
    const result = summarizeLog(log);
    assert.equal(result, log);
  });

  test("truncates long log to ≤ 500 chars", () => {
    const longLine = "x".repeat(100);
    const log = Array.from({ length: 20 }, (_, i) => `line ${i}: ${longLine}`).join(
      "\n",
    );
    const result = summarizeLog(log);
    assert.ok(result.length <= 500, `expected ≤500 chars, got ${result.length}`);
  });

  test("prioritizes error lines over other lines", () => {
    const log = [
      "step 1: starting task",
      "step 2: processing data",
      "ERROR: connection refused",
      "step 3: retrying",
    ].join("\n");
    const result = summarizeLog(log);
    assert.ok(
      result.includes("ERROR"),
      "expected error line to appear in summary",
    );
    assert.ok(
      !result.includes("step 1"),
      "expected non-error lines to be excluded when errors exist",
    );
  });
});
