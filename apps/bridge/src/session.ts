/**
 * Session logger.
 *
 * Writes one JSONL file per bridge session to storage/sessions/.
 * Each line is a self-contained JSON object:
 *
 *   {"type":"session_start", ...metadata}
 *   {"type":"turn", "seq":1, "timestamp":"...", "user":"...", "assistant":"...", ...}
 *   {"type":"session_end", ...}
 *
 * Files are named: YYYY-MM-DD_HH-MM-SS_<shortId>.jsonl
 * for easy sorting and analysis.
 */
import { appendFile, mkdir } from "node:fs/promises";
import { join } from "node:path";
import { config, createLogger } from "@avatar-agent/utils";

const log = createLogger("session");

interface SessionStartRecord {
  type: "session_start";
  session_id: string;
  started_at: string;
  model: string;
  max_predict_tokens: number;
  system_prompt_hash: string;
}

interface TurnRecord {
  type: "turn";
  seq: number;
  timestamp: string;
  user: string;
  assistant: string;
  emotion: string;
  motion: string;
  latency_ms: number;
  tokens_per_sec?: number;
  ttft_ms?: number;
}

interface SessionEndRecord {
  type: "session_end";
  session_id: string;
  ended_at: string;
  turn_count: number;
}

type SessionRecord = SessionStartRecord | TurnRecord | SessionEndRecord;

export class SessionLogger {
  private readonly sessionId: string;
  private readonly filePath: string;
  private turnCount = 0;
  private ready: Promise<void>;

  constructor(systemPrompt: string) {
    const now = new Date();
    const dateStr = now.toISOString().slice(0, 19).replace("T", "_").replaceAll(":", "-");
    const shortId = Math.random().toString(36).slice(2, 8);
    this.sessionId = `${dateStr}_${shortId}`;
    this.filePath = join(config.session.dir, `${this.sessionId}.jsonl`);

    // 簡易ハッシュ（プロンプト変更を検知するため）
    const hash = systemPrompt
      .split("")
      .reduce((acc, c) => (acc * 31 + c.charCodeAt(0)) >>> 0, 0)
      .toString(16)
      .padStart(8, "0");

    const startRecord: SessionStartRecord = {
      type: "session_start",
      session_id: this.sessionId,
      started_at: now.toISOString(),
      model: config.ollama.model,
      max_predict_tokens: config.ollama.maxPredictTokens,
      system_prompt_hash: hash,
    };

    this.ready = mkdir(config.session.dir, { recursive: true })
      .then(() => this.append(startRecord))
      .then(() => {
        log.info(`Session started → ${this.filePath}`);
      })
      .catch((err) => {
        log.error("Failed to initialize session log", err);
      });
  }

  async logTurn(opts: {
    user: string;
    assistant: string;
    emotion: string;
    motion: string;
    latency_ms: number;
    tokens_per_sec?: number;
    ttft_ms?: number;
  }): Promise<void> {
    await this.ready;
    this.turnCount++;
    const record: TurnRecord = {
      type: "turn",
      seq: this.turnCount,
      timestamp: new Date().toISOString(),
      ...opts,
    };
    await this.append(record).catch((err) =>
      log.error("Failed to write turn log", err),
    );
  }

  async end(): Promise<void> {
    await this.ready;
    const record: SessionEndRecord = {
      type: "session_end",
      session_id: this.sessionId,
      ended_at: new Date().toISOString(),
      turn_count: this.turnCount,
    };
    await this.append(record).catch((err) =>
      log.error("Failed to write session_end", err),
    );
    log.info(`Session ended (${this.turnCount} turns) → ${this.filePath}`);
  }

  private async append(record: SessionRecord): Promise<void> {
    await appendFile(this.filePath, JSON.stringify(record) + "\n", "utf-8");
  }
}
