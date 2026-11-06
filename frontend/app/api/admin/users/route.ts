import type { NextRequest } from "next/server";
import { jsonError, requireAdminContext } from "@/lib/backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: NextRequest): Promise<Response> {
  const admin = await requireAdminContext(request);
  if ("response" in admin) {
    return admin.response;
  }
  const upstream = await fetch(`${admin.backendBase}/internal/admin/users`, {
    headers: { authorization: `Bearer ${admin.token}` },
    cache: "no-store",
  });
  return new Response(await upstream.text(), {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "application/json",
    },
  });
}

export async function POST(request: NextRequest): Promise<Response> {
  const admin = await requireAdminContext(request);
  if ("response" in admin) {
    return admin.response;
  }
  const body = (await request.json()) as { email?: string; plan?: string };
  const email = (body.email || "").trim().toLowerCase();
  const plan = body.plan === "user" ? "user" : "trial";
  if (!email || !email.includes("@")) {
    return jsonError("invalid_email", 400);
  }
  const recorded = await fetch(`${admin.backendBase}/internal/admin/users`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${admin.token}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({ email, plan }),
    cache: "no-store",
  });
  return new Response(await recorded.text(), {
    status: recorded.status,
    headers: { "content-type": "application/json" },
  });
}
