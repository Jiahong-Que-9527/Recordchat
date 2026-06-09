"use client";

import { Braces, Plus } from "lucide-react";
import Image from "next/image";
import { EXAMPLE_QUESTIONS, ONE_RECORD_CONCEPTS } from "@/lib/constants";
import { Button } from "@/components/ui/button";

export function Sidebar({
  onPick,
  onNewChat,
}: {
  onPick: (q: string) => void;
  onNewChat: () => void;
}) {
  return (
    <aside className="flex w-full shrink-0 flex-col gap-5 rounded-2xl border border-slate-200 bg-white p-4 shadow-rc-sm xl:sticky xl:top-4 xl:h-[calc(100vh-2rem)]">
      <div className="flex items-center px-1">
        <Image
          src="/recordchat-logo.png"
          alt="RecordChat"
          width={44}
          height={44}
          className="h-11 w-auto object-contain"
          priority
        />
      </div>

      <Button onClick={onNewChat} className="w-full gap-2">
        <Plus className="h-4 w-4" />
        New chat
      </Button>

      <div>
        <p className="mb-2 text-xs font-semibold text-slate-500">Try asking</p>
        <div className="flex gap-1.5 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible">
          {EXAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => onPick(q)}
              className="min-w-[220px] rounded-lg px-2.5 py-2 text-left text-xs leading-5 text-slate-600 transition hover:bg-slate-100 lg:min-w-0"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="mb-2 text-xs font-semibold text-slate-500">Concepts</p>
        <div className="flex flex-wrap gap-1.5">
          {ONE_RECORD_CONCEPTS.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => onPick(`What is ${c} in ONE Record?`)}
              className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-700 transition hover:border-accent-ring hover:bg-accent-weak hover:text-accent"
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={() => onPick("Generate a JSON-LD example for a Piece.")}
        className="mt-auto inline-flex items-center gap-2 rounded-xl border border-accent-ring bg-accent-weak px-3 py-2 text-left text-xs font-medium text-accent transition hover:bg-accent/10"
      >
        <Braces className="h-4 w-4" />
        JSON-LD generator
      </button>
    </aside>
  );
}
