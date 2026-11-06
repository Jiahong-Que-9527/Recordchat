import type { NextRequest } from "next/server";
import {
  clearSessionCookieHeader,
  getBackendBase,
  sessionCookieValue,
} from "@/lib/backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: NextRequest): Promise<Response> {
  const token = sessionCookieValue(request);
  if (token) {
    await fetch(`${getBackendBase(request)}/internal/auth/logout`, {
      method: "POST",
      headers: { "x-session-token": token },
      cache: "no-store",
    });
  }
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: {
      "content-type": "application/json",
      "set-cookie": clearSessionCookieHeader(),
    },
  });
}
