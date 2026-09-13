import { createHash } from "crypto";
import type { NextRequest } from "next/server";
import { auth, currentUser } from "@clerk/nextjs/server";
import { isAuthEnforced } from "@/lib/authMode";
import { signInternalJwt } from "@/lib/internalJwt";

export function getBackendBase(request: NextRequest): string {
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

export function jsonError(
  error: string,
  status: number,
  extra?: Record<string, unknown>
): Response {
  return new Response(JSON.stringify({ error, ...extra }), {
    status,
    headers: { "content-type": "application/json" },
  });
}

export function emailHash(email: string): string {
  const pepper =
    process.env.EMAIL_HASH_PEPPER?.trim() ||
    process.env.INTERNAL_AUTH_SECRET?.trim() ||
    "";
  return createHash("sha256")
    .update(`${email.trim().toLowerCase()}${pepper}`)
    .digest("hex");
}

export function emailPrefix(email: string): string {
  const trimmed = email.trim().toLowerCase();
  const at = trimmed.indexOf("@");
  if (at <= 0) {
    return "***";
  }
  const local = trimmed.slice(0, at);
  const domain = trimmed.slice(at);
  return `${local.slice(0, 2)}***${domain}`;
}

export type AuthedContext = {
  userId: string;
  email: string;
  mustResetPassword: boolean;
  token: string;
};

export async function requireAuthedContext(): Promise<
  AuthedContext | { response: Response }
> {
  if (!isAuthEnforced()) {
    return { response: jsonError("unauthorized", 401) };
  }
  const secret = process.env.INTERNAL_AUTH_SECRET?.trim() || "";
  if (secret.length < 32) {
    return { response: jsonError("unavailable", 503, { retry_after_seconds: 60 }) };
  }
  const { userId } = await auth();
  if (!userId) {
    return { response: jsonError("unauthorized", 401) };
  }
  const user = await currentUser();
  const email =
    user?.primaryEmailAddress?.emailAddress ||
    user?.emailAddresses?.[0]?.emailAddress ||
    "";
  const mustResetPassword =
    user?.publicMetadata?.must_reset_password === true;
  const ttl = Number(process.env.INTERNAL_JWT_TTL_SECONDS || "90");
  const token = signInternalJwt({
    sub: userId,
    emailHash: email ? emailHash(email) : "",
    secret,
    ttlSeconds: Number.isFinite(ttl) ? ttl : 90,
  });
  return { userId, email, mustResetPassword, token };
}

export async function ensureUser(
  backendBase: string,
  token: string,
  email: string
): Promise<Response> {
  return fetch(`${backendBase}/internal/users/ensure`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${token}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({ email_prefix: email ? emailPrefix(email) : "" }),
    cache: "no-store",
  });
}
