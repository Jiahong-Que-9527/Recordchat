import type { NextRequest } from "next/server";
import { CHAT_MODELS } from "@/lib/api";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type IncomingMessage = {
  role?: string;
  parts?: Array<{ type?: string; text?: string }>;
};

const ALLOWED_MODELS = new Set<string>(CHAT_MODELS);

function getBackendBase(request: NextRequest): string {
  const internal = process.env.INTERNAL_API_BASE_URL?.trim();
  if (internal) {
    return internal.replace(/\/$/, "");
  }

  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }

  const forwardedProto = request.headers.get("x-forwarded-proto");
  const protocol =
    forwardedProto ?? request.nextUrl.protocol.replace(/:$/, "") ?? "http";
  const host = request.nextUrl.hostname || "127.0.0.1";
  return `${protocol}://${host}:8000`;
}

function extractLatestUserMessage(messages: IncomingMessage[]): string {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    if (message?.role !== "user") {
      continue;
    }

    const text = (message.parts ?? [])
      .filter((part) => part.type === "text" && typeof part.text === "string")
      .map((part) => part.text?.trim() ?? "")
      .filter(Boolean)
      .join("\n");

    if (text) {
      return text;
    }
  }

  return "";
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
  const message = extractLatestUserMessage(
    Array.isArray(payload?.messages) ? payload.messages : []
  );
  const model =
    typeof payload?.model === "string" && ALLOWED_MODELS.has(payload.model)
      ? payload.model
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

  const backendBase = getBackendBase(request);
  const upstream = await fetch(`${backendBase}/chat/stream`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ message, model }),
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
