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
import { ask } from "./brain.js";

const log = createLogger("server");

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

export async function startServer() {
  const app = Fastify({ logger: false });

  await app.register(cors, {
    origin: false, // localhost only; no cross-origin
  });

  // ── Health ──────────────────────────────────────────────────────────────────
  app.get("/health", async (_req, reply) => {
    return reply.send({ ok: true });
  });

  // ── SSE stream ──────────────────────────────────────────────────────────────
  app.get("/events", async (req, reply) => {
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
      const renderEvent = await ask(message, broadcast);
      broadcast(renderEvent);
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
  await app.listen({ host, port });
  log.info(`Bridge listening on http://${host}:${port}`);
}
