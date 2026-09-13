"use client";

import Link from "next/link";
import { SignedIn, UserButton } from "@clerk/nextjs";

export function AuthControls() {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    return null;
  }

  return (
    <SignedIn>
      <div className="flex items-center gap-2">
        <Link
          href="/account"
          className="hidden text-xs text-slate-600 underline sm:inline"
        >
          Account
        </Link>
        <Link
          href="/admin"
          className="hidden text-xs text-slate-600 underline sm:inline"
        >
          Admin
        </Link>
        <UserButton />
      </div>
    </SignedIn>
  );
}
