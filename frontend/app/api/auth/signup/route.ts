import type { NextRequest } from "next/server";
import {
  getBackendBase,
  jsonError,
  setSessionCookieHeader,
} from "@/lib/backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: NextRequest): Promise<Response> {
  const body = await request.text();
  const upstream = await fetch(`${getBackendBase(request)}/internal/auth/signup`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
    cache: "no-store",
  });
  const text = await upstream.text();
  if (!upstream.ok) {
    return new Response(text, {
      status: upstream.status,
      headers: { "content-type": "application/json" },
    });
  }
  let parsed: { session_token?: string };
  try {
    parsed = JSON.parse(text) as { session_token?: string };
  } catch {
    return jsonError("unavailable", 503);
  }
  if (!parsed.session_token) {
    return jsonError("unavailable", 503);
  }
  return new Response(text, {
    status: 200,
    headers: {
      "content-type": "application/json",
      "set-cookie": setSessionCookieHeader(parsed.session_token, request),
    },
  });
}
