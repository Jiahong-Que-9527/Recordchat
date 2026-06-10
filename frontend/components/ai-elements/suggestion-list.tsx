"use client";

import { EXAMPLE_QUESTIONS } from "@/lib/constants";

export function SuggestionList({
  onPick,
}: {
  onPick: (question: string) => void;
}) {
  return (
    <div className="mx-auto mt-8 grid w-full max-w-[864px] grid-cols-1 gap-2.5 sm:grid-cols-2">
      {EXAMPLE_QUESTIONS.slice(0, 4).map((question) => (
        <button
          key={question}
          type="button"
          onClick={() => onPick(question)}
          className="group flex h-14 items-center justify-center gap-2 rounded-xl border border-neutral-200 bg-neutral-50 px-4 text-center text-sm leading-5 text-neutral-600 transition hover:bg-white hover:text-neutral-950"
        >
          <span>{question}</span>
        </button>
      ))}
    </div>
  );
}
