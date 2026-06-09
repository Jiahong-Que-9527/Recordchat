import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

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

export async function POST(request: NextRequest): Promise<Response> {
  const payload = await request.json();
  const backendBase = getBackendBase(request);
  const upstream = await fetch(`${backendBase}/chat/stream`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(await upstream.text(), {
      status: upstream.status,
      headers: { "content-type": upstream.headers.get("content-type") ?? "text/plain" },
    });
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "content-type": "text/event-stream; charset=utf-8",
      "cache-control": "no-cache, no-transform",
      connection: "keep-alive",
    },
  });
}
