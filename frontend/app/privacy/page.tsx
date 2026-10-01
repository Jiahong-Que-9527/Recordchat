import Link from "next/link";

export default function PrivacyPage() {
  return (
    <main className="mx-auto min-h-screen max-w-2xl px-6 py-12 text-sm leading-6 text-slate-700">
      <h1 className="mb-4 text-2xl font-semibold text-slate-900">Privacy</h1>
      <p className="mb-3">
        RecordChat is an independent, citation-first assistant for IATA ONE
        Record. It is not an official IATA product.
      </p>
      <p className="mb-3">
        Trial chat messages stay in your browser. The service does not store
        conversation bodies. Diagnostic logs keep a hash and length of your
        question, not the question text, unless an operator briefly enables a
        local debug flag.
      </p>
      <p className="mb-3">
        Trial accounts have a daily question quota so model-API costs stay
        bounded. Operators can see anonymized usage counts, not your wording.
      </p>
      <p className="mb-6">
        You can change your password and sign out from your account page.
      </p>
      <Link className="text-sky-700 underline" href="/">
        Back to RecordChat
      </Link>
    </main>
  );
}
