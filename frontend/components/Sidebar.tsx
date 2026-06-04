"use client";

import { EXAMPLE_QUESTIONS, ONE_RECORD_CONCEPTS } from "@/lib/constants";

export function Sidebar({
  onPick,
  onNewChat,
}: {
  onPick: (q: string) => void;
  onNewChat: () => void;
}) {
  return (
    <aside className="flex h-full w-72 shrink-0 flex-col gap-6 border-r border-border bg-slate-50 p-4">
      <div>
        <h1 className="text-lg font-bold text-slate-900">RecordChat</h1>
        <p className="text-xs text-slate-500">IATA ONE Record assistant</p>
      </div>

      <button
        onClick={onNewChat}
        className="rounded-lg border border-border bg-white py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
      >
        + New Chat
      </button>

      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Example Questions
        </p>
        <div className="flex flex-col gap-1.5">
          {EXAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => onPick(q)}
              className="rounded-md px-2 py-1.5 text-left text-xs text-slate-600 hover:bg-slate-100"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
          ONE Record Concepts
        </p>
        <div className="flex flex-wrap gap-1.5">
          {ONE_RECORD_CONCEPTS.map((c) => (
            <button
              key={c}
              onClick={() => onPick(`What is ${c} in ONE Record?`)}
              className="rounded-md border border-border bg-white px-2 py-0.5 text-xs text-slate-600 hover:bg-slate-100"
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={() => onPick("Generate a JSON-LD example for a Piece.")}
        className="mt-auto rounded-md px-2 py-1.5 text-left text-xs text-accent hover:bg-slate-100"
      >
        ⚙ JSON-LD Generator
      </button>
    </aside>
  );
}
