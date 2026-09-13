import { randomBytes } from "crypto";
import type { NextRequest } from "next/server";
import { createClerkClient } from "@clerk/nextjs/server";
import {
  emailHash,
  emailPrefix,
  jsonError,
  requireAdminContext,
} from "@/lib/backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function temporaryPassword(): string {
  return randomBytes(18).toString("base64url").slice(0, 24);
}

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
  const secret = process.env.CLERK_SECRET_KEY?.trim();
  if (!secret) {
    return jsonError("unavailable", 503);
  }
  const password = temporaryPassword();
  const clerk = createClerkClient({ secretKey: secret });
  let created: { id: string };
  try {
    created = await clerk.users.createUser({
      emailAddress: [email],
      password,
      skipPasswordChecks: false,
    });
    await clerk.users.updateUserMetadata(created.id, {
      publicMetadata: { must_reset_password: true },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "clerk_failed";
    return jsonError("unavailable", 502, { detail: message });
  }
  const recorded = await fetch(`${admin.backendBase}/internal/admin/users`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${admin.token}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      idp_user_id: created.id,
      email_hash: emailHash(email),
      email_prefix: emailPrefix(email),
      plan,
    }),
    cache: "no-store",
  });
  if (!recorded.ok) {
    return new Response(await recorded.text(), { status: recorded.status });
  }
  const row = (await recorded.json()) as Record<string, unknown>;
  return Response.json({
    ...row,
    temporary_password: password,
  });
}
