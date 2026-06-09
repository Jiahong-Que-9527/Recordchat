"use client";

import Image from "next/image";
import { EXAMPLE_QUESTIONS, ONE_RECORD_CONCEPTS } from "@/lib/constants";

export function Sidebar({
  onPick,
  onNewChat,
}: {
  onPick: (q: string) => void;
  onNewChat: () => void;
}) {
  return (
    <aside className="flex w-full shrink-0 flex-col gap-6 border-b border-border bg-slate-50/90 p-4 backdrop-blur lg:h-full lg:w-72 lg:border-b-0 lg:border-r">
      <div className="flex items-center gap-3">
        <Image
          src="/recordchat-logo.png"
          alt="RecordChat"
          width={40}
          height={40}
          className="h-10 w-10 shrink-0 rounded-lg object-contain"
          priority
        />
        <div className="min-w-0">
          <h1 className="text-lg font-bold text-slate-900">RecordChat</h1>
          <p className="text-xs text-slate-500">IATA ONE Record assistant</p>
        </div>
      </div>

      <button
        onClick={onNewChat}
        className="rounded-lg border border-border bg-white py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
      >
        + New Chat
      </button>

      <div className="lg:block">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Example Questions
        </p>
        <div className="flex gap-1.5 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible">
          {EXAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => onPick(q)}
              className="min-w-[220px] rounded-xl px-3 py-2 text-left text-xs text-slate-600 transition hover:bg-slate-100 lg:min-w-0"
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
        className="rounded-xl px-3 py-2 text-left text-xs text-accent transition hover:bg-slate-100 lg:mt-auto"
      >
        ⚙ JSON-LD Generator
      </button>
    </aside>
  );
}
