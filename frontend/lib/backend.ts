import type { NextRequest } from "next/server";
import { isAuthEnforced } from "@/lib/authMode";
import { signInternalJwt } from "@/lib/internalJwt";
import { SESSION_COOKIE } from "@/lib/sessionCookie";

export { SESSION_COOKIE };

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

export function sessionCookieValue(request: NextRequest): string {
  return request.cookies.get(SESSION_COOKIE)?.value || "";
}

export function setSessionCookieHeader(token: string, request: NextRequest): string {
  const proto = (
    request.headers.get("x-forwarded-proto") ||
    request.nextUrl.protocol.replace(/:$/, "")
  ).toLowerCase();
  const parts = [
    `${SESSION_COOKIE}=${token}`,
    "Path=/",
    "HttpOnly",
    "SameSite=Lax",
    "Max-Age=604800",
  ];
  if (proto === "https") {
    parts.push("Secure");
  }
  return parts.join("; ");
}

export function clearSessionCookieHeader(): string {
  return `${SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0`;
}

type SessionUser = {
  idp_user_id: string;
  email_prefix?: string;
  role?: string;
  plan?: string;
  must_reset_password?: boolean;
};

export type AuthedContext = {
  userId: string;
  email: string;
  mustResetPassword: boolean;
  token: string;
  sessionToken: string;
};

export async function requireAuthedContext(
  request: NextRequest
): Promise<AuthedContext | { response: Response }> {
  if (!isAuthEnforced()) {
    return { response: jsonError("unauthorized", 401) };
  }
  const secret = process.env.INTERNAL_AUTH_SECRET?.trim() || "";
  if (secret.length < 32) {
    return { response: jsonError("unavailable", 503, { retry_after_seconds: 60 }) };
  }
  const sessionToken = sessionCookieValue(request);
  if (!sessionToken) {
    return { response: jsonError("unauthorized", 401) };
  }
  const backendBase = getBackendBase(request);
  const session = await fetch(`${backendBase}/internal/auth/session`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ session_token: sessionToken }),
    cache: "no-store",
  });
  if (!session.ok) {
    return { response: jsonError("unauthorized", 401) };
  }
  const body = (await session.json()) as {
    user?: SessionUser;
    must_reset_password?: boolean;
  };
  const userId = body.user?.idp_user_id;
  if (!userId) {
    return { response: jsonError("unauthorized", 401) };
  }
  const ttl = Number(process.env.INTERNAL_JWT_TTL_SECONDS || "90");
  const token = signInternalJwt({
    sub: userId,
    emailHash: "",
    secret,
    ttlSeconds: Number.isFinite(ttl) ? ttl : 90,
  });
  return {
    userId,
    email: "",
    mustResetPassword: Boolean(body.must_reset_password),
    token,
    sessionToken,
  };
}

export async function ensureUser(
  backendBase: string,
  token: string,
  _email: string
): Promise<Response> {
  return fetch(`${backendBase}/internal/users/ensure`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${token}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({ email_prefix: "" }),
    cache: "no-store",
  });
}

export async function requireAdminContext(request: NextRequest): Promise<
  | { token: string; backendBase: string; userId: string }
  | { response: Response }
> {
  const identity = await requireAuthedContext(request);
  if ("response" in identity) {
    return identity;
  }
  const backendBase = getBackendBase(request);
  const ensured = await ensureUser(backendBase, identity.token, identity.email);
  if (!ensured.ok) {
    return {
      response: new Response(await ensured.text(), { status: ensured.status }),
    };
  }
  const me = (await ensured.json()) as { role?: string };
  if (me.role !== "admin") {
    return { response: jsonError("forbidden", 403) };
  }
  return { token: identity.token, backendBase, userId: identity.userId };
}
