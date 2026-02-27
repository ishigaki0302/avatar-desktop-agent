/**
 * Lightweight schema validation tests (Node built-in test runner).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  validateUIEvent,
  parseRenderEvent,
  isValidEmotion,
  isValidMotion,
} from "./index.js";

test("validateUIEvent: valid render", () => {
  assert.ok(validateUIEvent({
    type: "render",
    text: "hello",
    emotion: "happy",
    motion: "wave",
  }));
});

test("validateUIEvent: invalid emotion falls through parseRenderEvent", () => {
  const result = parseRenderEvent({ text: "hi", emotion: "unknown", motion: "nod" });
  assert.equal(result.emotion, "neutral"); // fallback
  assert.equal(result.motion, "nod");
});

test("validateUIEvent: valid status", () => {
  assert.ok(validateUIEvent({ type: "status", state: "running", message: "thinking" }));
});

test("validateUIEvent: valid result", () => {
  assert.ok(validateUIEvent({ type: "result", summary: "done", details: null }));
});

test("validateUIEvent: unknown type fails", () => {
  assert.equal(validateUIEvent({ type: "unknown" }), false);
});

test("isValidEmotion: all valid emotions", () => {
  for (const e of ["neutral", "happy", "sad", "angry", "surprised", "confused"]) {
    assert.ok(isValidEmotion(e));
  }
  assert.equal(isValidEmotion("unknown"), false);
});

test("isValidMotion: all valid motions", () => {
  for (const m of ["none", "bow_small", "nod", "shake", "wave"]) {
    assert.ok(isValidMotion(m));
  }
  assert.equal(isValidMotion("jump"), false);
});
