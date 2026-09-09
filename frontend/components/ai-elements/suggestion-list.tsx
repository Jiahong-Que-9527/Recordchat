"use client";

import { ArrowUpRight } from "lucide-react";
import { RecordChatIcon } from "@/components/RecordChatIcon";
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
          className="group rc-glass flex min-h-[60px] items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm leading-5 text-slate-600 shadow-rc-sm transition hover:-translate-y-0.5 hover:border-accent-ring/80 hover:text-slate-900 hover:shadow-rc-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-ring focus-visible:ring-offset-2"
        >
          <RecordChatIcon
            size="md"
            className="transition group-hover:shadow-rc-glow"
          />
          <span className="flex-1">{question}</span>
          <ArrowUpRight className="h-4 w-4 shrink-0 text-slate-300 transition group-hover:text-accent" />
        </button>
      ))}
    </div>
  );
}
