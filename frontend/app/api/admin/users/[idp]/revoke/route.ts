import type { NextRequest } from "next/server";
import { createClerkClient } from "@clerk/nextjs/server";
import { jsonError, requireAdminContext } from "@/lib/backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ idp: string }> }
): Promise<Response> {
  const admin = await requireAdminContext(request);
  if ("response" in admin) {
    return admin.response;
  }
  const { idp } = await context.params;
  const secret = process.env.CLERK_SECRET_KEY?.trim();
  if (secret) {
    try {
      const clerk = createClerkClient({ secretKey: secret });
      await clerk.users.banUser(idp);
    } catch {
      /* local row still revoked */
    }
  }
  const upstream = await fetch(
    `${admin.backendBase}/internal/admin/users/${encodeURIComponent(idp)}/revoke`,
    {
      method: "POST",
      headers: { authorization: `Bearer ${admin.token}` },
      cache: "no-store",
    }
  );
  if (!upstream.ok && upstream.status === 404) {
    return jsonError("not_found", 404);
  }
  return new Response(await upstream.text(), {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "application/json",
    },
  });
}
