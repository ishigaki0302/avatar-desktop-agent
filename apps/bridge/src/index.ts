/**
 * Bridge entrypoint.
 * Starts the HTTP server and connects to Ollama.
 */
// Load .env from project root (DOTENV_CONFIG_PATH env var set by dev script).
// Must be the first import so env vars are set before utils/config.ts runs.
import "dotenv/config";
import { startServer } from "./server.js";
import { SessionLogger } from "./session.js";
import { SYSTEM_PROMPT } from "./brain.js";
import { createLogger } from "@avatar-agent/utils";

const log = createLogger("bridge");

process.on("uncaughtException", (err) => {
  log.error("Uncaught exception", err);
  process.exit(1);
});
process.on("unhandledRejection", (reason) => {
  log.error("Unhandled rejection", reason);
});

const session = new SessionLogger(SYSTEM_PROMPT);

// グレースフルシャットダウン時にセッションログを閉じる
async function shutdown() {
  await session.end();
  process.exit(0);
}
process.on("SIGINT",  () => { shutdown().catch(() => process.exit(1)); });
process.on("SIGTERM", () => { shutdown().catch(() => process.exit(1)); });

log.info("Starting bridge...");
startServer(session).catch((err) => {
  log.error("Failed to start server", err);
  process.exit(1);
});
