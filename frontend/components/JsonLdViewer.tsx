"use client";

import { useState } from "react";

export function JsonLdViewer({ data }: { data: Record<string, unknown> }) {
  const [copied, setCopied] = useState(false);
  const serialized = JSON.stringify(data, null, 2);

  async function copy() {
    await navigator.clipboard.writeText(serialized);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  return (
    <div className="mt-3 overflow-hidden rounded-3xl border border-slate-800 bg-slate-950 shadow-[0_12px_40px_rgba(15,23,42,0.28)]">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2">
        <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
          JSON-LD Output
        </span>
        <button
          type="button"
          onClick={copy}
          className="rounded-full border border-slate-700 px-3 py-1 text-[11px] font-medium text-slate-200 transition hover:border-slate-500 hover:text-white"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 text-xs leading-relaxed text-slate-100">
        <code>{serialized}</code>
      </pre>
    </div>
  );
}
