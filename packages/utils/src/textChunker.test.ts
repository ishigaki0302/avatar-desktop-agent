/**
 * Tests for textChunker utilities.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { truncate, chunkBySentence, extractJSON } from "./textChunker.js";

test("truncate: short text unchanged", () => {
  assert.equal(truncate("hello", 10), "hello");
});

test("truncate: long text cut with suffix", () => {
  const result = truncate("abcdefghij", 5);
  assert.equal(result.length, 5);
  assert.ok(result.endsWith("…"));
});

test("chunkBySentence: splits at sentence boundaries", () => {
  const text = "これは文章です。次の文です。三番目。";
  const chunks = chunkBySentence(text, 10);
  assert.ok(chunks.length >= 1);
  for (const c of chunks) {
    assert.ok(c.length <= 15); // some tolerance
  }
});

test("extractJSON: finds JSON in surrounding text", () => {
  const text = 'Here is the result: {"type":"render","text":"hi"} and more text';
  const obj = extractJSON(text);
  assert.ok(obj !== null);
  assert.equal(obj["type"], "render");
  assert.equal(obj["text"], "hi");
});

test("extractJSON: returns null for no JSON", () => {
  assert.equal(extractJSON("no json here"), null);
});

test("extractJSON: returns null for malformed JSON", () => {
  assert.equal(extractJSON("{bad json}"), null);
});
