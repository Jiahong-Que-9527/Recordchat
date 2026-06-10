"use client";

import { ArrowUpRight } from "lucide-react";
import { EXAMPLE_QUESTIONS } from "@/lib/constants";

export function SuggestionList({
  onPick,
}: {
  onPick: (question: string) => void;
}) {
  return (
    <div className="mx-auto mt-8 grid w-full max-w-2xl grid-cols-1 gap-2.5 sm:grid-cols-2">
      {EXAMPLE_QUESTIONS.slice(0, 4).map((question) => (
        <button
          key={question}
          type="button"
          onClick={() => onPick(question)}
          className="group flex items-start justify-between gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-left text-sm leading-5 text-slate-600 shadow-rc-sm transition hover:border-accent-ring hover:bg-accent-weak"
        >
          <span>{question}</span>
          <ArrowUpRight className="mt-0.5 h-4 w-4 shrink-0 text-slate-300 transition group-hover:text-accent" />
        </button>
      ))}
    </div>
  );
}
