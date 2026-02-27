/**
 * Brain parser unit tests.
 *
 * Tests extractJSON / stripLLMNoise / parseRenderEvent pipeline
 * without calling Ollama (pure logic only).
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { extractJSON, stripLLMNoise } from "@avatar-agent/utils";
import { parseRenderEvent, isValidEmotion, isValidMotion } from "@avatar-agent/schema";

// ── stripLLMNoise ─────────────────────────────────────────────────────────────
describe("stripLLMNoise", () => {
  test("removes <think> block", () => {
    const input = "<think>lots of reasoning here</think>\n{\"text\":\"hi\"}";
    const result = stripLLMNoise(input);
    assert.ok(!result.includes("<think>"));
    assert.ok(result.includes('{"text":"hi"}'));
  });

  test("removes multiline <think> block", () => {
    const input = "<think>\nstep1\nstep2\n</think>\n{\"a\":1}";
    assert.ok(!stripLLMNoise(input).includes("<think>"));
  });

  test("removes markdown json fence", () => {
    const input = "```json\n{\"text\":\"hello\"}\n```";
    const result = stripLLMNoise(input);
    assert.ok(!result.includes("```"));
    assert.ok(result.includes('{"text":"hello"}'));
  });

  test("removes plain markdown fence", () => {
    const input = "```\n{\"x\":1}\n```";
    const result = stripLLMNoise(input);
    assert.equal(result, '{"x":1}');
  });

  test("leaves clean JSON unchanged", () => {
    const input = '{"text":"ok","emotion":"happy"}';
    assert.equal(stripLLMNoise(input), input);
  });
});

// ── extractJSON ───────────────────────────────────────────────────────────────
describe("extractJSON", () => {
  test("parses clean JSON", () => {
    const obj = extractJSON('{"text":"hello","emotion":"happy"}');
    assert.equal(obj?.["text"], "hello");
    assert.equal(obj?.["emotion"], "happy");
  });

  test("extracts JSON after <think> block", () => {
    const raw = '<think>Let me think...</think>\n{"text":"result","emotion":"neutral","motion":"nod","memory_update":"NOOP","task":null}';
    const obj = extractJSON(raw);
    assert.ok(obj !== null);
    assert.equal(obj["text"], "result");
  });

  test("extracts JSON from markdown fence", () => {
    const raw = "Here is my reply:\n```json\n{\"text\":\"こんにちは\"}\n```";
    const obj = extractJSON(raw);
    assert.ok(obj !== null);
    assert.equal(obj["text"], "こんにちは");
  });

  test("handles nested JSON objects (task field)", () => {
    const raw = '{"text":"ok","task":{"goal":"search","constraints":{"no_credential":true}}}';
    const obj = extractJSON(raw);
    assert.ok(obj !== null);
    assert.equal(typeof obj["task"], "object");
  });

  test("handles JSON with escaped quotes in strings", () => {
    const raw = '{"text":"彼は\\"こんにちは\\"と言った","emotion":"neutral"}';
    const obj = extractJSON(raw);
    assert.ok(obj !== null);
    assert.ok((obj["text"] as string).includes("こんにちは"));
  });

  test("returns null for no JSON", () => {
    assert.equal(extractJSON("no json here at all"), null);
  });

  test("returns null for truncated JSON", () => {
    assert.equal(extractJSON('{"text":"truncated'), null);
  });
});

// ── parseRenderEvent ──────────────────────────────────────────────────────────
describe("parseRenderEvent", () => {
  test("valid fields pass through", () => {
    const ev = parseRenderEvent({ text: "hello", emotion: "happy", motion: "wave" });
    assert.equal(ev.type, "render");
    assert.equal(ev.text, "hello");
    assert.equal(ev.emotion, "happy");
    assert.equal(ev.motion, "wave");
  });

  test("invalid emotion falls back to neutral", () => {
    const ev = parseRenderEvent({ text: "hi", emotion: "unknown_emotion", motion: "nod" });
    assert.equal(ev.emotion, "neutral");
  });

  test("invalid motion falls back to none", () => {
    const ev = parseRenderEvent({ text: "hi", emotion: "sad", motion: "jump" });
    assert.equal(ev.motion, "none");
  });

  test("undefined fields fall back to defaults", () => {
    const ev = parseRenderEvent({ text: "hi" });
    assert.equal(ev.emotion, "neutral");
    assert.equal(ev.motion, "none");
  });
});

// ── Full pipeline simulation ──────────────────────────────────────────────────
describe("Full parse pipeline (simulate Ollama output → RenderEvent)", () => {
  function pipelineFrom(raw: string) {
    const parsed = extractJSON(raw);
    if (!parsed) return null;
    const text = typeof parsed["text"] === "string" ? parsed["text"] : "";
    if (!text) return null;
    return parseRenderEvent({
      text,
      emotion: parsed["emotion"] as string,
      motion: parsed["motion"] as string,
    });
  }

  test("clean JSON output", () => {
    const raw = '{"text":"了解です！","emotion":"happy","motion":"nod","memory_update":"NOOP","task":null}';
    const ev = pipelineFrom(raw);
    assert.ok(ev !== null);
    assert.equal(ev!.text, "了解です！");
    assert.ok(isValidEmotion(ev!.emotion));
    assert.ok(isValidMotion(ev!.motion));
  });

  test("output with think + fence", () => {
    const raw = "<think>I should be friendly</think>\n```json\n{\"text\":\"ありがとう！\",\"emotion\":\"happy\",\"motion\":\"wave\",\"memory_update\":\"NOOP\",\"task\":null}\n```";
    const ev = pipelineFrom(raw);
    assert.ok(ev !== null);
    assert.equal(ev!.emotion, "happy");
  });

  test("missing optional fields → defaults", () => {
    const raw = '{"text":"テスト"}';
    const ev = pipelineFrom(raw);
    assert.ok(ev !== null);
    assert.equal(ev!.emotion, "neutral");
    assert.equal(ev!.motion, "none");
  });

  test("empty text → returns null (brain should retry)", () => {
    const raw = '{"text":"","emotion":"happy"}';
    const ev = pipelineFrom(raw);
    assert.equal(ev, null);
  });
});
