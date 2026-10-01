import type { NextRequest } from "next/server";
import { getBackendBase, jsonError, sessionCookieValue } from "@/lib/backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: NextRequest): Promise<Response> {
  const token = sessionCookieValue(request);
  if (!token) {
    return jsonError("unauthorized", 401);
  }
  const body = await request.text();
  const upstream = await fetch(
    `${getBackendBase(request)}/internal/auth/change-password`,
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-session-token": token,
      },
      body,
      cache: "no-store",
    }
  );
  return new Response(await upstream.text(), {
    status: upstream.status,
    headers: { "content-type": "application/json" },
  });
}
