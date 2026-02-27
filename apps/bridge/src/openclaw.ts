/**
 * OpenClaw Gateway client (Route A).
 *
 * Phase 3: connects to OpenClaw Gateway via WebSocket (raw JSON frames).
 * Falls back to stub result when OPENCLAW_GATEWAY_URL is not set.
 *
 * Protocol:
 *  1. Connect WebSocket
 *  2. Send type:"connect" with role and auth token
 *  3. Receive event:"hello-ok" → send type:"req" / method:"chat.send"
 *  4. Accumulate event:"chat.message" log lines
 *  5. Receive type:"res" (matching request id) → summarizeLog → resolve
 *  6. Timeout at 70 s → reject
 *
 * Execution logs are summarized to ≤500 chars before returning.
 */
import { config, createLogger, truncate } from "@avatar-agent/utils";

const log = createLogger("openclaw");
const MAX_LOG_CHARS = 500;
const GATEWAY_TIMEOUT_MS = 70_000;

// ── Deny-list (takes precedence over everything) ──────────────────────────────
const DENY_PATTERNS = [
  /\brm\s/i,
  /\bsudo\b/i,
  /eval\(/,
  /exec\(/,
  /password/i,
  /credential/i,
  /private\.key/i,
];

export async function delegateTask(goal: string): Promise<string> {
  if (!config.openclaw.gatewayUrl) {
    log.warn("OPENCLAW_GATEWAY_URL not set — returning stub result");
    return stubResult(goal);
  }

  if (!isAllowed(goal)) {
    log.warn(`Task blocked by deny-list: "${goal}"`);
    return "このタスクは許可されていません。";
  }

  try {
    return await gatewayDelegate(goal);
  } catch (err) {
    log.error("OpenClaw delegation failed", err);
    return `タスク実行中にエラーが発生しました: ${truncate(String(err), 100)}`;
  }
}

export function isAllowed(goal: string): boolean {
  return !DENY_PATTERNS.some((pattern) => pattern.test(goal));
}

/**
 * Delegate task to OpenClaw Gateway via WebSocket.
 */
async function gatewayDelegate(goal: string): Promise<string> {
  const reqId = `req-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

  return new Promise<string>((resolve, reject) => {
    const timer = setTimeout(() => {
      ws.close();
      reject(new Error("OpenClaw gateway timeout (70s)"));
    }, GATEWAY_TIMEOUT_MS);

    const ws = new WebSocket(config.openclaw.gatewayUrl);
    const logLines: string[] = [];

    ws.onopen = () => {
      log.info("OpenClaw WS connected");
      ws.send(
        JSON.stringify({
          type: "connect",
          role: "operator",
          auth: { token: config.openclaw.apiKey },
        }),
      );
    };

    ws.onmessage = (event: MessageEvent) => {
      let frame: Record<string, unknown>;
      try {
        frame = JSON.parse(event.data as string) as Record<string, unknown>;
      } catch {
        log.warn("Invalid JSON from gateway", event.data);
        return;
      }

      const frameEvent = frame["event"] as string | undefined;
      const frameType = frame["type"] as string | undefined;
      const frameId = frame["id"] as string | undefined;

      if (frameEvent === "hello-ok") {
        log.info("OpenClaw hello-ok — sending chat.send request");
        ws.send(
          JSON.stringify({
            type: "req",
            id: reqId,
            method: "chat.send",
            params: { message: goal },
          }),
        );
        return;
      }

      if (frameEvent === "chat.message") {
        const content = frame["content"] as string | undefined;
        if (content) logLines.push(content);
        return;
      }

      if (frameType === "res" && frameId === reqId) {
        clearTimeout(timer);
        ws.close();
        const rawLog = logLines.join("\n");
        log.info(`OpenClaw task complete (${logLines.length} log lines)`);
        resolve(summarizeLog(rawLog));
      }
    };

    ws.onerror = (err: Event) => {
      clearTimeout(timer);
      log.error("OpenClaw WS error", err);
      reject(new Error("OpenClaw WebSocket error"));
    };

    ws.onclose = () => {
      clearTimeout(timer);
    };
  });
}

function stubResult(goal: string): string {
  return `[OpenClaw スタブ] タスク「${truncate(goal, 60)}」は Phase 3 で実装予定です。`;
}

/**
 * Summarize raw execution log to ≤ MAX_LOG_CHARS.
 * Extracts key lines (errors, final outputs) rather than passing raw logs to LLM.
 */
export function summarizeLog(rawLog: string): string {
  const lines = rawLog.split("\n").filter((l) => l.trim().length > 0);
  // Prefer error lines first, then other important lines
  const errorLines = lines.filter((l) => /error|失敗/i.test(l));
  const important = lines.filter((l) =>
    /success|result|完了|取得/i.test(l),
  );
  const selected =
    errorLines.length > 0
      ? errorLines
      : important.length > 0
        ? important
        : lines;
  const summary = selected.slice(-10).join("\n");
  return truncate(summary, MAX_LOG_CHARS);
}
