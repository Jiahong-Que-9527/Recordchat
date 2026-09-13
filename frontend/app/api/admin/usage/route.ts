import type { NextRequest } from "next/server";
import { requireAdminContext } from "@/lib/backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: NextRequest): Promise<Response> {
  const admin = await requireAdminContext(request);
  if ("response" in admin) {
    return admin.response;
  }
  const upstream = await fetch(`${admin.backendBase}/internal/admin/usage`, {
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
