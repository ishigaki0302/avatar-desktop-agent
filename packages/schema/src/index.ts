// ─── Shared type definitions ──────────────────────────────────────────────────
// All packages import from here. UI only consumes RenderEvent | StatusEvent | ResultEvent.

export type Emotion = "neutral" | "happy" | "sad" | "angry" | "surprised" | "confused";
export type Motion = "none" | "bow_small" | "nod" | "shake" | "wave";
export type StatusState = "running" | "idle" | "error";

// ─── Brain → UI ──────────────────────────────────────────────────────────────
export interface RenderEvent {
  type: "render";
  text: string;
  emotion: Emotion;
  motion: Motion;
}

// ─── Bridge → UI ─────────────────────────────────────────────────────────────
export interface StatusEvent {
  type: "status";
  state: StatusState;
  message: string;
}

export interface ResultEvent {
  type: "result";
  summary: string;
  details: string | null;
}

export type UIEvent = RenderEvent | StatusEvent | ResultEvent;

// ─── Brain → Bridge / OpenClaw (internal) ────────────────────────────────────
export interface TaskConstraints {
  no_credential: boolean;
  allow_shell: boolean;
  time_budget_sec: number;
}

export interface TaskEvent {
  type: "task";
  goal: string;
  constraints: TaskConstraints;
}

// ─── Brain raw output (before parsing) ───────────────────────────────────────
export interface BrainRawOutput {
  text: string;
  emotion?: string;
  motion?: string;
  memory_update?: string; // "NOOP" or markdown diff
  task?: Omit<TaskEvent, "type">;
}

// ─── Validation helpers ───────────────────────────────────────────────────────
const VALID_EMOTIONS = new Set<string>([
  "neutral", "happy", "sad", "angry", "surprised", "confused",
]);
const VALID_MOTIONS = new Set<string>([
  "none", "bow_small", "nod", "shake", "wave",
]);

export function isValidEmotion(v: unknown): v is Emotion {
  return typeof v === "string" && VALID_EMOTIONS.has(v);
}

export function isValidMotion(v: unknown): v is Motion {
  return typeof v === "string" && VALID_MOTIONS.has(v);
}

export function parseRenderEvent(raw: BrainRawOutput): RenderEvent {
  return {
    type: "render",
    text: raw.text,
    emotion: isValidEmotion(raw.emotion) ? raw.emotion : "neutral",
    motion: isValidMotion(raw.motion) ? raw.motion : "none",
  };
}

// ─── Schema validation (lightweight, no ajv dependency) ──────────────────────
export function validateUIEvent(obj: unknown): obj is UIEvent {
  if (typeof obj !== "object" || obj === null) return false;
  const t = (obj as Record<string, unknown>)["type"];
  if (t === "render") {
    const e = obj as Record<string, unknown>;
    return (
      typeof e["text"] === "string" &&
      isValidEmotion(e["emotion"]) &&
      isValidMotion(e["motion"])
    );
  }
  if (t === "status") {
    const e = obj as Record<string, unknown>;
    return (
      typeof e["message"] === "string" &&
      ["running", "idle", "error"].includes(e["state"] as string)
    );
  }
  if (t === "result") {
    const e = obj as Record<string, unknown>;
    return (
      typeof e["summary"] === "string" &&
      (e["details"] === null || typeof e["details"] === "string")
    );
  }
  return false;
}
