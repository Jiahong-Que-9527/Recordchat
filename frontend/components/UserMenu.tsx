"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronUp, Info, LogOut, Shield, UserRound } from "lucide-react";
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

function MenuItem({
  href,
  onClick,
  icon,
  children,
  danger = false,
}: {
  href?: string;
  onClick?: () => void;
  icon: React.ReactNode;
  children: React.ReactNode;
  danger?: boolean;
}) {
  const className = cn(
    "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-[13px] transition",
    danger
      ? "text-rose-700 hover:bg-rose-50"
      : "text-slate-700 hover:bg-slate-100"
  );
  if (href) {
    return (
      <Link href={href} className={className} onClick={onClick}>
        {icon}
        {children}
      </Link>
    );
  }
  return (
    <button type="button" className={className} onClick={onClick}>
      {icon}
      {children}
    </button>
  );
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
  const planLabel = me?.plan === "user" ? "User" : "Trial";

  async function signOut() {
    setOpen(false);
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/sign-in");
  }

  return (
    <div ref={rootRef} className="relative">
      {open ? (
        <div
          role="menu"
          className={cn(
            "absolute bottom-full z-50 mb-1.5 overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-1 shadow-rc-lg ring-1 ring-black/[0.03]",
            collapsed ? "left-0 w-60" : "inset-x-0"
          )}
        >
          {signedIn ? (
            <>
              <div className="px-2.5 py-2">
                <p className="truncate text-[13px] font-medium text-slate-900">
                  {me?.email_prefix}
                </p>
                <p className="mt-0.5 text-[11px] text-slate-500">
                  {planLabel}
                  {me?.quota != null
                    ? ` · ${me.used_today ?? 0}/${me.quota} today`
                    : null}
                </p>
              </div>
              <div className="my-1 h-px bg-slate-100" />
              <MenuItem
                href="/account"
                icon={<UserRound className="h-4 w-4 text-slate-400" />}
                onClick={() => setOpen(false)}
              >
                Account
              </MenuItem>
              {isAdmin ? (
                <MenuItem
                  href="/admin"
                  icon={<Shield className="h-4 w-4 text-slate-400" />}
                  onClick={() => setOpen(false)}
                >
                  Manage users
                </MenuItem>
              ) : null}
              <MenuItem
                href="/privacy"
                onClick={() => setOpen(false)}
                icon={<Info className="h-4 w-4 text-slate-400" />}
              >
                Privacy
              </MenuItem>
              <div className="my-1 h-px bg-slate-100" />
              <MenuItem
                danger
                icon={<LogOut className="h-4 w-4" />}
                onClick={() => void signOut()}
              >
                Sign out
              </MenuItem>
            </>
          ) : (
            <>
              <MenuItem href="/sign-in" onClick={() => setOpen(false)} icon={<UserRound className="h-4 w-4 text-slate-400" />}>
                Sign in
              </MenuItem>
              <MenuItem href="/sign-up" onClick={() => setOpen(false)} icon={<span className="inline-block w-4" />}>
                Create account
              </MenuItem>
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
          "flex w-full items-center rounded-xl text-sm text-slate-700 transition",
          open ? "bg-white shadow-rc-sm" : "hover:bg-white/80",
          collapsed ? "h-10 justify-center px-0" : "h-11 gap-2.5 px-2"
        )}
      >
        <span className="rc-gradient-bg inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold tracking-wide text-white">
          {glyph}
        </span>
        {collapsed ? null : (
          <>
            <span className="min-w-0 flex-1 text-left">
              <span className="block truncate text-[13px] font-medium leading-4 text-slate-900">
                {label}
              </span>
              {signedIn ? (
                <span className="mt-0.5 block truncate text-[11px] leading-4 text-slate-400">
                  {planLabel}
                </span>
              ) : null}
            </span>
            <ChevronUp
              className={cn(
                "h-4 w-4 shrink-0 text-slate-400 transition-transform duration-150",
                open ? "" : "rotate-180"
              )}
            />
          </>
        )}
      </button>
    </div>
  );
}
