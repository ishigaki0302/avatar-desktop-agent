type LogLevel = "debug" | "info" | "warn" | "error";

const LEVEL_ORDER: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

const currentLevel = (): LogLevel => {
  const v = (process.env["LOG_LEVEL"] ?? "info").toLowerCase();
  if (v === "debug" || v === "info" || v === "warn" || v === "error") return v;
  return "info";
};

function log(level: LogLevel, prefix: string, msg: string, extra?: unknown) {
  if (LEVEL_ORDER[level] < LEVEL_ORDER[currentLevel()]) return;
  const ts = new Date().toISOString();
  const line = `[${ts}] [${level.toUpperCase()}] [${prefix}] ${msg}`;
  const out = extra !== undefined ? `${line} ${JSON.stringify(extra)}` : line;
  if (level === "error") {
    process.stderr.write(out + "\n");
  } else {
    process.stdout.write(out + "\n");
  }
}

export function createLogger(prefix: string) {
  return {
    debug: (msg: string, extra?: unknown) => log("debug", prefix, msg, extra),
    info:  (msg: string, extra?: unknown) => log("info",  prefix, msg, extra),
    warn:  (msg: string, extra?: unknown) => log("warn",  prefix, msg, extra),
    error: (msg: string, extra?: unknown) => log("error", prefix, msg, extra),
  };
}
