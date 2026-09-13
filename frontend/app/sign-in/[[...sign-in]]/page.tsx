import Link from "next/link";
import { SignIn } from "@clerk/nextjs";
import { hasClerkPublishableKey } from "@/lib/authMode";

export default function SignInPage() {
  if (!hasClerkPublishableKey()) {
    return (
      <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-3 px-6">
        <h1 className="text-xl font-semibold">Sign in</h1>
        <p className="text-sm text-slate-600">
          Authentication is off in this environment. Open the chat without
          signing in.
        </p>
        <Link className="text-sm text-sky-700 underline" href="/">
          Back to RecordChat
        </Link>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <SignIn />
    </main>
  );
}
