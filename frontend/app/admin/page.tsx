"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";

type UserRow = {
  idp_user_id: string;
  email_prefix: string;
  role: string;
  plan: string;
  status: string;
  quota: number;
  used_today: number;
  daily_quota: number | null;
};

type Usage = {
  day?: string;
  dau?: number;
  request_count?: number;
  estimated_usd?: number;
  rate_limited_count?: number;
};

export default function AdminPage() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [error, setError] = useState("");
  const [passwordOnce, setPasswordOnce] = useState("");
  const [email, setEmail] = useState("");
  const [plan, setPlan] = useState("trial");

  const load = useCallback(async () => {
    setError("");
    const [userRes, usageRes] = await Promise.all([
      fetch("/api/admin/users", { cache: "no-store" }),
      fetch("/api/admin/usage", { cache: "no-store" }),
    ]);
    if (userRes.status === 403) {
      setError("Admins only.");
      return;
    }
    if (!userRes.ok) {
      setError("Could not load users.");
      return;
    }
    setUsers((await userRes.json()) as UserRow[]);
    if (usageRes.ok) {
      setUsage((await usageRes.json()) as Usage);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setPasswordOnce("");
    const res = await fetch("/api/admin/users", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, plan }),
    });
    const body = (await res.json()) as { temporary_password?: string; error?: string };
    if (!res.ok) {
      setError(body.error || "Create failed");
      return;
    }
    setPasswordOnce(body.temporary_password || "");
    setEmail("");
    await load();
  }

  async function revoke(idp: string) {
    await fetch(`/api/admin/users/${encodeURIComponent(idp)}/revoke`, {
      method: "POST",
    });
    await load();
  }

  async function promote(idp: string, next: string) {
    await fetch(`/api/admin/users/${encodeURIComponent(idp)}/plan`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ plan: next }),
    });
    await load();
  }

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-10 text-sm text-slate-700">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900">Admin</h1>
        <Link className="text-sky-700 underline" href="/">
          Back to chat
        </Link>
      </div>
      {error ? (
        <p className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-rose-700">
          {error}
        </p>
      ) : null}
      {usage ? (
        <p className="mb-4 text-xs text-slate-500">
          Today {usage.day}: {usage.dau ?? 0} users, {usage.request_count ?? 0}{" "}
          requests, ${Number(usage.estimated_usd || 0).toFixed(4)} est.,{" "}
          {usage.rate_limited_count ?? 0} rate-limits. No question text.
        </p>
      ) : null}
      <form onSubmit={onCreate} className="mb-6 flex flex-wrap items-end gap-2">
        <label className="flex flex-col gap-1">
          Email
          <input
            className="rounded-lg border border-slate-200 px-3 py-2"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            type="email"
            required
          />
        </label>
        <label className="flex flex-col gap-1">
          Plan
          <select
            className="rounded-lg border border-slate-200 px-3 py-2"
            value={plan}
            onChange={(event) => setPlan(event.target.value)}
          >
            <option value="trial">trial</option>
            <option value="user">user</option>
          </select>
        </label>
        <button
          type="submit"
          className="rounded-lg bg-sky-700 px-4 py-2 text-white"
        >
          Create account
        </button>
      </form>
      {passwordOnce ? (
        <p className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-amber-900">
          Temporary password (shown once):{" "}
          <code className="break-all">{passwordOnce}</code>
        </p>
      ) : null}
      <ul className="space-y-2">
        {users.map((user) => (
          <li
            key={user.idp_user_id}
            className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2"
          >
            <div>
              <div className="font-medium text-slate-900">
                {user.email_prefix || user.idp_user_id}
              </div>
              <div className="text-xs text-slate-500">
                {user.role} · {user.plan} · {user.status} · {user.used_today}/
                {user.quota}
              </div>
            </div>
            <div className="flex gap-2">
              {user.plan === "trial" ? (
                <button
                  type="button"
                  className="text-xs underline"
                  onClick={() => void promote(user.idp_user_id, "user")}
                >
                  Promote
                </button>
              ) : (
                <button
                  type="button"
                  className="text-xs underline"
                  onClick={() => void promote(user.idp_user_id, "trial")}
                >
                  To trial
                </button>
              )}
              {user.status !== "revoked" ? (
                <button
                  type="button"
                  className="text-xs text-rose-700 underline"
                  onClick={() => void revoke(user.idp_user_id)}
                >
                  Revoke
                </button>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
