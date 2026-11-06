import type { NextRequest } from "next/server";
import { isAuthEnforced } from "@/lib/authMode";
import {
  ensureUser,
  getBackendBase,
  jsonError,
  requireAuthedContext,
} from "@/lib/backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: NextRequest): Promise<Response> {
  if (!isAuthEnforced()) {
    return jsonError("unauthorized", 401);
  }
  const identity = await requireAuthedContext(request);
  if ("response" in identity) {
    return identity.response;
  }
  const backendBase = getBackendBase(request);
  const ensured = await ensureUser(backendBase, identity.token, identity.email);
  if (!ensured.ok) {
    return new Response(await ensured.text(), { status: ensured.status });
  }
  const me = await fetch(`${backendBase}/internal/users/me`, {
    headers: { authorization: `Bearer ${identity.token}` },
    cache: "no-store",
  });
  return new Response(await me.text(), {
    status: me.status,
    headers: { "content-type": me.headers.get("content-type") ?? "application/json" },
  });
}
