"use client";

import { FormEvent, Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

function AccountForm() {
  const router = useRouter();
  const params = useSearchParams();
  const force = params.get("force") === "1";
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function onChange(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    const res = await fetch("/api/auth/change-password", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
    if (!res.ok) {
      setError("Could not change the password.");
      return;
    }
    setMessage("Password updated.");
    if (force) {
      router.push("/");
    }
  }

  async function onLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/sign-in");
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6">
      <h1 className="text-xl font-semibold">Account</h1>
      {force ? (
        <p className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Set your own password before chatting. The temporary password was
          only for the first sign-in.
        </p>
      ) : null}
      <form onSubmit={onChange} className="flex flex-col gap-3">
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          type="password"
          placeholder="Current password"
          value={currentPassword}
          onChange={(event) => setCurrentPassword(event.target.value)}
          required
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          type="password"
          placeholder="New password (10+ characters)"
          value={newPassword}
          onChange={(event) => setNewPassword(event.target.value)}
          required
          minLength={10}
        />
        {error ? <p className="text-sm text-rose-700">{error}</p> : null}
        {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
        <button className="rounded-lg bg-sky-700 px-4 py-2 text-white" type="submit">
          Update password
        </button>
      </form>
      <button className="text-left text-sm text-slate-600 underline" type="button" onClick={() => void onLogout()}>
        Sign out
      </button>
      <Link className="text-sm text-sky-700 underline" href="/">
        Back to chat
      </Link>
    </main>
  );
}

export default function AccountPage() {
  return (
    <Suspense>
      <AccountForm />
    </Suspense>
  );
}
