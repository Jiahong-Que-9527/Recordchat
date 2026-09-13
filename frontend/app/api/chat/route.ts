import type { NextRequest } from "next/server";
import { CHAT_MODELS, SYNTHETIC_MODES } from "@/lib/api";
import { isAuthEnforced } from "@/lib/authMode";
import {
  ensureUser,
  getBackendBase,
  jsonError,
  requireAuthedContext,
} from "@/lib/backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type IncomingMessage = {
  role?: string;
  parts?: Array<{ type?: string; text?: string }>;
};

const ALLOWED_MODELS = new Set<string>(CHAT_MODELS);
const ALLOWED_SYNTHETIC_MODES = new Set<string>(SYNTHETIC_MODES);
const MAX_MESSAGE_CHARS = Number(process.env.CHAT_MAX_MESSAGE_CHARS || "4000");
const MAX_HISTORY_TURNS = Number(process.env.CHAT_MAX_HISTORY_TURNS || "6");
const IP_CHAT_PER_HOUR = 60;
const ipWindows = new Map<string, { start: number; count: number }>();

function clientIp(request: NextRequest): string {
  const cf = request.headers.get("cf-connecting-ip");
  if (cf) {
    return cf.trim();
  }
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) {
    return forwarded.split(",")[0]?.trim() || "unknown";
  }
  return "unknown";
}

function allowIp(ip: string): boolean {
  const now = Date.now();
  const windowMs = 60 * 60 * 1000;
  const rec = ipWindows.get(ip);
  if (!rec || now - rec.start > windowMs) {
    ipWindows.set(ip, { start: now, count: 1 });
    return true;
  }
  if (rec.count >= IP_CHAT_PER_HOUR) {
    return false;
  }
  rec.count += 1;
  return true;
}

function messageText(message: IncomingMessage): string {
  return (message.parts ?? [])
    .filter((part) => part.type === "text" && typeof part.text === "string")
    .map((part) => part.text?.trim() ?? "")
    .filter(Boolean)
    .join("\n");
}

function extractLatestUserMessage(messages: IncomingMessage[]): string {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    if (message?.role !== "user") {
      continue;
    }

    const text = messageText(message);
    if (text) {
      return text;
    }
  }

  return "";
}

/** Prior turns for follow-up rewrite (#30). Excludes the current user message. */
function extractHistory(
  messages: IncomingMessage[],
  currentMessage: string,
  limit = MAX_HISTORY_TURNS
): Array<{ role: "user" | "assistant"; content: string }> {
  const history: Array<{ role: "user" | "assistant"; content: string }> = [];
  let skippedCurrent = false;

  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    const role = message?.role;
    if (role !== "user" && role !== "assistant") {
      continue;
    }
    const text = messageText(message);
    if (!text) {
      continue;
    }
    if (!skippedCurrent && role === "user" && text === currentMessage) {
      skippedCurrent = true;
      continue;
    }
    history.push({ role, content: text });
    if (history.length >= limit) {
      break;
    }
  }

  return history.reverse();
}

function parseSseEvent(raw: string): {
  event: string | null;
  data: Record<string, unknown> | null;
} | null {
  const lines = raw
    .split("\n")
    .map((line) => line.trimEnd())
    .filter(Boolean);
  const event = lines.find((line) => line.startsWith("event: "))?.slice(7) ?? null;
  const dataLine = lines.find((line) => line.startsWith("data: "))?.slice(6);

  if (!dataLine) {
    return null;
  }

  try {
    return {
      event,
      data: JSON.parse(dataLine) as Record<string, unknown>,
    };
  } catch {
    return null;
  }
}

function sseChunk(payload: Record<string, unknown> | "[DONE]"): string {
  return `data: ${typeof payload === "string" ? payload : JSON.stringify(payload)}\n\n`;
}

export async function POST(request: NextRequest): Promise<Response> {
  const payload = await request.json();
  const incomingMessages = Array.isArray(payload?.messages)
    ? (payload.messages as IncomingMessage[])
    : [];
  const message = extractLatestUserMessage(incomingMessages);
  const history = extractHistory(incomingMessages, message);
  const model =
    typeof payload?.model === "string" && ALLOWED_MODELS.has(payload.model)
      ? payload.model
      : undefined;
  const syntheticMode =
    typeof payload?.synthetic_mode === "string" &&
    ALLOWED_SYNTHETIC_MODES.has(payload.synthetic_mode)
      ? payload.synthetic_mode
      : undefined;

  if (!message) {
    return new Response(
      JSON.stringify({ error: "No user message found in request body." }),
      {
        status: 400,
        headers: { "content-type": "application/json" },
      }
    );
  }

  if (message.length > MAX_MESSAGE_CHARS || history.some((item) => item.content.length > MAX_MESSAGE_CHARS)) {
    return jsonError("payload_too_large", 400);
  }

  const backendBase = getBackendBase(request);
  const headers: Record<string, string> = { "content-type": "application/json" };
  const requestId = crypto.randomUUID();
  headers["x-request-id"] = requestId;

  if (isAuthEnforced()) {
    if (!allowIp(clientIp(request))) {
      return jsonError("rate_limited", 429, { retry_after_seconds: 3600 });
    }
    const identity = await requireAuthedContext();
    if ("response" in identity) {
      return identity.response;
    }
    if (identity.mustResetPassword) {
      return jsonError("password_change_required", 403);
    }
    const ensured = await ensureUser(backendBase, identity.token, identity.email);
    if (!ensured.ok) {
      return new Response(await ensured.text(), {
        status: ensured.status,
        headers: {
          "content-type": ensured.headers.get("content-type") ?? "application/json",
        },
      });
    }
    headers.authorization = `Bearer ${identity.token}`;
  }

  const upstream = await fetch(`${backendBase}/chat/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      message,
      model,
      ...(history.length > 0 ? { history } : {}),
      ...(syntheticMode ? { synthetic_mode: syntheticMode } : {}),
    }),
    cache: "no-store",
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(await upstream.text(), {
      status: upstream.status,
      headers: { "content-type": upstream.headers.get("content-type") ?? "text/plain" },
    });
  }

  const encoder = new TextEncoder();
  const reader = upstream.body.getReader();
  const messageId = crypto.randomUUID();
  const textId = crypto.randomUUID();

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      controller.enqueue(
        encoder.encode(sseChunk({ type: "start", messageId }))
      );
      controller.enqueue(encoder.encode(sseChunk({ type: "start-step" })));
      controller.enqueue(
        encoder.encode(sseChunk({ type: "text-start", id: textId }))
      );

      const decoder = new TextDecoder();
      let buffer = "";
      let closed = false;

      try {
        while (true) {
          const { value, done } = await reader.read();
          buffer += decoder.decode(value ?? new Uint8Array(), {
            stream: !done,
          });

          let boundary = buffer.indexOf("\n\n");
          while (boundary !== -1) {
            const rawEvent = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            const parsed = parseSseEvent(rawEvent);

            if (parsed?.event === "token") {
              const text = parsed.data?.text;
              if (typeof text === "string" && text) {
                controller.enqueue(
                  encoder.encode(
                    sseChunk({ type: "text-delta", id: textId, delta: text })
                  )
                );
              }
            }

            if (parsed?.event === "metadata" && parsed.data) {
              controller.enqueue(
                encoder.encode(
                  sseChunk({
                    type: "data-recordchat",
                    data: parsed.data,
                  })
                )
              );
            }

            boundary = buffer.indexOf("\n\n");
          }

          if (done) {
            break;
          }
        }

        controller.enqueue(encoder.encode(sseChunk({ type: "text-end", id: textId })));
        controller.enqueue(encoder.encode(sseChunk({ type: "finish-step" })));
        controller.enqueue(encoder.encode(sseChunk({ type: "finish" })));
        controller.enqueue(encoder.encode(sseChunk("[DONE]")));
        closed = true;
        controller.close();
      } catch (error) {
        controller.enqueue(
          encoder.encode(
            sseChunk({
              type: "error",
              errorText:
                error instanceof Error
                  ? error.message
                  : "Failed to process RecordChat stream.",
            })
          )
        );
        controller.enqueue(encoder.encode(sseChunk("[DONE]")));
        closed = true;
        controller.close();
      } finally {
        if (!closed) {
          reader.releaseLock();
        }
      }
    },
  });

  return new Response(stream, {
    status: upstream.status,
    headers: {
      "content-type": "text/event-stream; charset=utf-8",
      "cache-control": "no-cache, no-transform",
      connection: "keep-alive",
      "x-vercel-ai-ui-message-stream": "v1",
    },
  });
}
