"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export function AuthControls() {
  const router = useRouter();
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    fetch("/api/me", { cache: "no-store" })
      .then((res) => setSignedIn(res.ok))
      .catch(() => setSignedIn(false));
  }, []);

  if (!signedIn) {
    return (
      <Link href="/sign-in" className="text-xs text-slate-600 underline">
        Sign in
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Link href="/account" className="hidden text-xs text-slate-600 underline sm:inline">
        Account
      </Link>
      <Link href="/admin" className="hidden text-xs text-slate-600 underline sm:inline">
        Admin
      </Link>
      <button
        type="button"
        className="text-xs text-slate-600 underline"
        onClick={async () => {
          await fetch("/api/auth/logout", { method: "POST" });
          router.push("/sign-in");
        }}
      >
        Sign out
      </button>
    </div>
  );
}
