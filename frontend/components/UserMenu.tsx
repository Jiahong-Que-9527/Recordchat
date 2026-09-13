"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronDown, LogOut, Shield, UserRound } from "lucide-react";
import { cn } from "@/lib/utils";

type Me = {
  email_prefix?: string;
  role?: string;
  plan?: string;
  quota?: number;
  used_today?: number;
};

function initials(prefix?: string): string {
  if (!prefix) {
    return "?";
  }
  const local = prefix.split("@")[0]?.replace(/\*/g, "") || prefix;
  const letters = local.replace(/[^a-zA-Z0-9]/g, "").slice(0, 2);
  return (letters || "?").toUpperCase();
}

export function UserMenu({ collapsed }: { collapsed: boolean }) {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/me", { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) {
          return null;
        }
        return (await res.json()) as Me;
      })
      .then((data) => {
        setMe(data);
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, []);

  useEffect(() => {
    function onDocClick(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  const signedIn = Boolean(me);
  const isAdmin = me?.role === "admin";
  const label = signedIn ? me?.email_prefix || "Account" : "Sign in";
  const glyph = signedIn ? initials(me?.email_prefix) : "?";

  async function signOut() {
    setOpen(false);
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/sign-in");
  }

  return (
    <div ref={rootRef} className="relative">
      {open ? (
        <div
          className={cn(
            "absolute bottom-full z-50 mb-2 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-rc-md",
            collapsed ? "left-0 w-56" : "inset-x-0"
          )}
        >
          {signedIn ? (
            <>
              <div className="border-b border-slate-100 px-3 py-2">
                <p className="truncate text-sm font-medium text-slate-900">
                  {me?.email_prefix}
                </p>
                <p className="text-[11px] text-slate-500">
                  {me?.plan === "user" ? "User" : "Trial"}
                  {me?.quota != null
                    ? ` · ${me.used_today ?? 0} / ${me.quota} today`
                    : null}
                </p>
              </div>
              <Link
                href="/account"
                className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                onClick={() => setOpen(false)}
              >
                <UserRound className="h-4 w-4 text-slate-400" />
                Account
              </Link>
              {isAdmin ? (
                <Link
                  href="/admin"
                  className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                  onClick={() => setOpen(false)}
                >
                  <Shield className="h-4 w-4 text-slate-400" />
                  Manage users
                </Link>
              ) : null}
              <Link
                href="/privacy"
                className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                onClick={() => setOpen(false)}
              >
                Privacy
              </Link>
              <button
                type="button"
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
                onClick={() => void signOut()}
              >
                <LogOut className="h-4 w-4 text-slate-400" />
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/sign-in"
                className="block px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                onClick={() => setOpen(false)}
              >
                Sign in
              </Link>
              <Link
                href="/sign-up"
                className="block px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                onClick={() => setOpen(false)}
              >
                Create account
              </Link>
            </>
          )}
        </div>
      ) : null}

      <button
        type="button"
        onClick={() => loaded && setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={label}
        title={label}
        className={cn(
          "flex h-10 w-full items-center rounded-lg text-sm text-slate-700 transition hover:bg-slate-200/70",
          collapsed ? "justify-center px-0" : "gap-2.5 px-3"
        )}
      >
        <span className="rc-gradient-bg inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold text-white shadow-rc-sm">
          {glyph}
        </span>
        {collapsed ? null : (
          <>
            <span className="min-w-0 flex-1 truncate text-left text-sm font-medium">
              {label}
            </span>
            <ChevronDown
              className={cn(
                "h-4 w-4 shrink-0 text-slate-400 transition-transform",
                open ? "rotate-180" : ""
              )}
            />
          </>
        )}
      </button>
    </div>
  );
}
