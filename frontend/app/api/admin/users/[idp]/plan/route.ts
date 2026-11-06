import type { NextRequest } from "next/server";
import { requireAdminContext } from "@/lib/backend";

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
  const body = await request.text();
  const upstream = await fetch(
    `${admin.backendBase}/internal/admin/users/${encodeURIComponent(idp)}/plan`,
    {
      method: "POST",
      headers: {
        authorization: `Bearer ${admin.token}`,
        "content-type": "application/json",
      },
      body,
      cache: "no-store",
    }
  );
  return new Response(await upstream.text(), {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "application/json",
    },
  });
}
