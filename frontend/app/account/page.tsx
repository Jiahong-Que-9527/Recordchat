import Link from "next/link";
import { UserProfile } from "@clerk/nextjs";
import { hasClerkPublishableKey } from "@/lib/authMode";

export default async function AccountPage({
  searchParams,
}: {
  searchParams: Promise<{ force?: string }>;
}) {
  const params = await searchParams;
  const force = params?.force === "1";

  if (!hasClerkPublishableKey()) {
    return (
      <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-3 px-6">
        <h1 className="text-xl font-semibold">Account</h1>
        <p className="text-sm text-slate-600">
          Account settings are unavailable while authentication is off.
        </p>
        <Link className="text-sm text-sky-700 underline" href="/">
          Back to RecordChat
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-4 px-4 py-8">
      {force ? (
        <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Set your own password before chatting. The temporary password was
          only for the first sign-in.
        </p>
      ) : null}
      <Link className="text-sm text-sky-700 underline" href="/">
        Back to chat
      </Link>
      <UserProfile />
    </main>
  );
}
