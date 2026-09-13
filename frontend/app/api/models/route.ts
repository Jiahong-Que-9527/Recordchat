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

const FLASH = "deepseek-v4-flash";

export async function GET(request: NextRequest): Promise<Response> {
  const backendBase = getBackendBase(request);
  const upstream = await fetch(`${backendBase}/models`, { cache: "no-store" });
  const text = await upstream.text();
  if (!upstream.ok) {
    return new Response(text, { status: upstream.status });
  }

  if (!isAuthEnforced()) {
    return new Response(text, {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }

  const identity = await requireAuthedContext();
  if ("response" in identity) {
    return identity.response;
  }
  const ensured = await ensureUser(backendBase, identity.token, identity.email);
  if (!ensured.ok) {
    return new Response(await ensured.text(), { status: ensured.status });
  }
  let plan = "trial";
  try {
    const body = (await ensured.json()) as { plan?: string };
    plan = body.plan || "trial";
  } catch {
    plan = "trial";
  }

  let parsed: { models?: string[]; default?: string } = {};
  try {
    parsed = JSON.parse(text) as { models?: string[]; default?: string };
  } catch {
    return jsonError("unavailable", 503);
  }
  if (plan === "trial") {
    parsed = {
      models: [FLASH],
      default: FLASH,
    };
  }
  return Response.json(parsed);
}
