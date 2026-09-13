import Link from "next/link";
import { SignUp } from "@clerk/nextjs";
import { hasClerkPublishableKey } from "@/lib/authMode";

export default function SignUpPage() {
  if (!hasClerkPublishableKey()) {
    return (
      <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-3 px-6">
        <h1 className="text-xl font-semibold">Create an account</h1>
        <p className="text-sm text-slate-600">
          Sign-up is disabled while AUTH_MODE is off. Open the chat directly.
        </p>
        <Link className="text-sm text-sky-700 underline" href="/">
          Back to RecordChat
        </Link>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <SignUp />
    </main>
  );
}
