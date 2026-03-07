/**
 * Fastify HTTP server.
 *
 * Routes:
 *   POST /chat          — receive user message, return render event
 *   GET  /events        — SSE stream for UI (render/status/result)
 *   GET  /health        — health check
 */
import Fastify from "fastify";
import cors from "@fastify/cors";
import type { UIEvent } from "@avatar-agent/schema";
import { config, createLogger } from "@avatar-agent/utils";
import { ask, setModel, getCurrentModel } from "./brain.js";
import type { SessionLogger } from "./session.js";

const log = createLogger("server");

const MAX_SSE_CLIENTS = 3;

// SSE subscriber registry
type Subscriber = (event: UIEvent) => void;
const subscribers = new Set<Subscriber>();

export function broadcast(event: UIEvent) {
  for (const sub of subscribers) {
    try {
      sub(event);
    } catch {
      // subscriber already closed; will be removed on disconnect
    }
  }
}

export async function startServer(session?: SessionLogger) {
  const app = Fastify({ logger: false, bodyLimit: 8192 });

  await app.register(cors, {
    origin: false, // localhost only; no cross-origin
  });

  // ── Health ──────────────────────────────────────────────────────────────────
  app.get("/health", async (_req, reply) => {
    const model = getCurrentModel();
    let ramMB: number | undefined;
    try {
      const psRes = await fetch(`${config.ollama.baseUrl}/api/ps`);
      if (psRes.ok) {
        const ps = await psRes.json() as { models?: Array<{ model: string; size: number }> };
        const entry = ps.models?.find((m) => m.model === model);
        if (entry) ramMB = Math.round(entry.size / (1024 * 1024));
      }
    } catch {
      // Ollama not running or /api/ps unsupported — ignore
    }
    return reply.send({ ok: true, model, ramMB });
  });

  // ── Models ──────────────────────────────────────────────────────────────────
  app.get("/models", async (_req, reply) => {
    return reply.send({ current: getCurrentModel(), available: config.ollama.availableModels, backend: config.brainBackend });
  });

  app.post<{ Body: { model: string } }>("/model", {
    schema: {
      body: {
        type: "object",
        required: ["model"],
        properties: { model: { type: "string", minLength: 1 } },
      },
    },
  }, async (req, reply) => {
    const { model } = req.body;
    try {
      setModel(model);
      broadcast({ type: "status", state: "idle", message: `モデル切替: ${model}` });
      return reply.send({ ok: true, model });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return reply.status(400).send({ ok: false, error: msg });
    }
  });

  // ── SSE stream ──────────────────────────────────────────────────────────────
  app.get("/events", async (req, reply) => {
    if (subscribers.size >= MAX_SSE_CLIENTS) {
      return reply.status(429).send({ error: "Too many SSE clients" });
    }

    reply.raw.setHeader("Content-Type", "text/event-stream");
    reply.raw.setHeader("Cache-Control", "no-cache");
    reply.raw.setHeader("Connection", "keep-alive");
    reply.raw.flushHeaders?.();

    const send = (event: UIEvent) => {
      reply.raw.write(`data: ${JSON.stringify(event)}\n\n`);
    };

    subscribers.add(send);
    log.info(`SSE client connected (total: ${subscribers.size})`);

    // Send initial idle status
    send({ type: "status", state: "idle", message: "Ready" });

    req.raw.on("close", () => {
      subscribers.delete(send);
      log.info(`SSE client disconnected (total: ${subscribers.size})`);
    });

    // Keep connection open
    await new Promise<void>((resolve) => {
      req.raw.on("close", resolve);
    });
  });

  // ── Chat ────────────────────────────────────────────────────────────────────
  app.post<{ Body: { message: string } }>("/chat", {
    schema: {
      body: {
        type: "object",
        required: ["message"],
        properties: {
          message: { type: "string", minLength: 1, maxLength: 4000 },
        },
      },
    },
  }, async (req, reply) => {
    const { message } = req.body;

    // Notify UI: thinking
    broadcast({ type: "status", state: "running", message: "考え中..." });

    try {
      await ask(message, broadcast, session);
      broadcast({ type: "status", state: "idle", message: "Ready" });
      return reply.send({ ok: true });
    } catch (err) {
      log.error("Brain error", err);
      broadcast({
        type: "status",
        state: "error",
        message: "エラーが発生しました。もう一度お試しください。",
      });
      return reply.status(500).send({ ok: false, error: "Brain error" });
    }
  });

  const host = config.bridge.host;
  const port = config.bridge.port;

  if (host !== "127.0.0.1" && host !== "localhost") {
    log.warn(`Bridge bound to ${host} — consider using 127.0.0.1 for security`);
  }

  await app.listen({ host, port });
  log.info(`Bridge listening on http://${host}:${port}`);
}
