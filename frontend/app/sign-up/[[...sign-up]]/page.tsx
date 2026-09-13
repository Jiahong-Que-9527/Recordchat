"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function SignUpPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const res = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const body = (await res.json()) as { error?: string };
    if (!res.ok) {
      if (body.error === "email_taken") {
        setError("That email is already registered.");
      } else if (body.error === "password_too_short") {
        setError("Use at least 10 characters.");
      } else {
        setError("Could not create the account.");
      }
      return;
    }
    router.push("/");
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6">
      <h1 className="text-xl font-semibold">Create an account</h1>
      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
        <input
          className="rounded-lg border border-slate-200 px-3 py-2"
          type="password"
          placeholder="Password (10+ characters)"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
          minLength={10}
        />
        {error ? <p className="text-sm text-rose-700">{error}</p> : null}
        <button className="rounded-lg bg-sky-700 px-4 py-2 text-white" type="submit">
          Sign up
        </button>
      </form>
      <p className="text-sm text-slate-600">
        Already have an account?{" "}
        <Link className="text-sky-700 underline" href="/sign-in">
          Sign in
        </Link>
      </p>
    </main>
  );
}
