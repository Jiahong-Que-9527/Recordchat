import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { SESSION_COOKIE } from "@/lib/sessionCookie";

const PUBLIC_PREFIXES = [
  "/sign-in",
  "/sign-up",
  "/privacy",
  "/api/auth/login",
  "/api/auth/signup",
];

function isPublic(pathname: string): boolean {
  if (PUBLIC_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))) {
    return true;
  }
  if (pathname.startsWith("/_next") || pathname.startsWith("/recordchat")) {
    return true;
  }
  return false;
}

export default function middleware(request: NextRequest) {
  const enforced =
    (process.env.AUTH_MODE || "").trim().toLowerCase() === "enforced";
  if (!enforced) {
    return NextResponse.next();
  }
  const { pathname } = request.nextUrl;
  if (isPublic(pathname)) {
    return NextResponse.next();
  }
  if (!request.cookies.get(SESSION_COOKIE)?.value) {
    const url = request.nextUrl.clone();
    url.pathname = "/sign-in";
    url.search = "";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
