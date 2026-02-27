/**
 * OpenClaw Gateway client (Route A).
 *
 * Phase 3 placeholder — connects to OpenClaw Gateway via WebSocket.
 * In Phase 1/2, returns a stub result.
 *
 * The intent is to reuse the official OpenClaw TS SDK when available,
 * rather than re-implementing the signing handshake.
 *
 * Execution logs are summarized to ≤500 chars before returning.
 */
import { config, createLogger, truncate } from "@avatar-agent/utils";

const log = createLogger("openclaw");
const MAX_LOG_CHARS = 500;

// Allowed action types (allowlist enforced by Bridge, not by OpenClaw)
const ALLOWED_ACTIONS = new Set(config.openclaw_allow);

export async function delegateTask(goal: string): Promise<string> {
  if (!config.openclaw.gatewayUrl) {
    log.warn("OPENCLAW_GATEWAY_URL not set — returning stub result");
    return stubResult(goal);
  }

  // Validate goal doesn't request disallowed operations
  if (!isAllowed(goal)) {
    log.warn(`Task blocked by allowlist: "${goal}"`);
    return "このタスクは許可されていません。";
  }

  try {
    return await gatewayDelegate(goal);
  } catch (err) {
    log.error("OpenClaw delegation failed", err);
    return `タスク実行中にエラーが発生しました: ${truncate(String(err), 100)}`;
  }
}

function isAllowed(goal: string): boolean {
  // Simple keyword check; replace with schema-level intent classification in Phase 4
  const lower = goal.toLowerCase();
  for (const action of ALLOWED_ACTIONS) {
    if (lower.includes(action.replace("_", " ")) || lower.includes(action)) {
      return true;
    }
  }
  // Default: allow if no dangerous keywords detected
  const dangerous = ["rm ", "sudo", "eval(", "exec(", "password", "credential"];
  return !dangerous.some((d) => lower.includes(d));
}

/**
 * Actual WebSocket delegation to OpenClaw Gateway.
 * TODO (Phase 3): integrate official OpenClaw TS SDK.
 */
async function gatewayDelegate(goal: string): Promise<string> {
  // Phase 3 stub — WebSocket connection will go here.
  // import { OpenClawClient } from "@openclaw/sdk";
  // const client = new OpenClawClient(config.openclaw.gatewayUrl, config.openclaw.apiKey);
  // const result = await client.execute({ goal, constraints: { allow_shell: false, no_credential: true } });
  // return summarize(result.log);
  log.info(`[Phase3 TODO] Would delegate to OpenClaw: "${goal}"`);
  return stubResult(goal);
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
  // Prefer lines containing result keywords
  const important = lines.filter((l) =>
    /error|success|result|完了|失敗|取得/i.test(l),
  );
  const summary = (important.length > 0 ? important : lines)
    .slice(-10)
    .join("\n");
  return truncate(summary, MAX_LOG_CHARS);
}
