import { createLogger } from "./logger.js";

const log = createLogger("config");

function env(key: string, fallback: string): string {
  return process.env[key] ?? fallback;
}

function envInt(key: string, fallback: number): number {
  const v = process.env[key];
  if (v === undefined) return fallback;
  const n = parseInt(v, 10);
  if (isNaN(n)) {
    log.warn(`Invalid int for ${key}="${v}", using ${fallback}`);
    return fallback;
  }
  return n;
}

export const config = {
  brainBackend: env("BRAIN_BACKEND", "ollama") as "ollama" | "remote-gpu",
  ollama: {
    baseUrl:          env("OLLAMA_BASE_URL", "http://localhost:11434"),
    model:            env("OLLAMA_MODEL", "qwen3.5:2b"),
    availableModels:  env("OLLAMA_AVAILABLE_MODELS", "qwen3.5:2b").split(",") as string[],
    timeoutMs:        envInt("OLLAMA_TIMEOUT_MS", 60_000),
    maxPredictTokens: envInt("OLLAMA_MAX_PREDICT", 512),
  },
  remoteGpu: {
    baseUrl:       env("REMOTE_GPU_BASE_URL", "http://127.0.0.1:10003"),
    maxNewTokens:  envInt("REMOTE_GPU_MAX_NEW_TOKENS", 512),
    temperature:   parseFloat(env("REMOTE_GPU_TEMPERATURE", "0.75")),
    timeoutMs:     envInt("REMOTE_GPU_TIMEOUT_MS", 120_000),
  },
  bridge: {
    port: envInt("BRIDGE_PORT", 3000),
    host: env("BRIDGE_HOST", "127.0.0.1"),
  },
  openclaw: {
    gatewayUrl: env("OPENCLAW_GATEWAY_URL", ""),
    apiKey:     env("OPENCLAW_API_KEY", ""),
  },
  typewriter: {
    charMs:          envInt("TYPEWRITER_CHAR_MS", 45),
    lipsyncToggleMs: envInt("LIPSYNC_TOGGLE_MS", 120),
    pauseCommaMs:    envInt("LIPSYNC_PAUSE_COMMA_MS", 150),
    pauseSentenceMs: envInt("LIPSYNC_PAUSE_SENTENCE_MS", 400),
    pauseNewlineMs:  envInt("LIPSYNC_PAUSE_NEWLINE_MS", 400),
    motionFps:       envInt("MOTION_FPS", 8),
  },
  memory: {
    dir: env("MEMORY_DIR", "./storage/memory"),
  },
  session: {
    dir: env("SESSION_DIR", "./storage/sessions"),
  },
  // OpenClaw task allowlist
  openclaw_allow: [
    "browser_open",
    "browser_search",
    "app_launch",
    "clipboard_read",
    "clipboard_write",
    "screenshot",
  ] as string[],
} as const;
