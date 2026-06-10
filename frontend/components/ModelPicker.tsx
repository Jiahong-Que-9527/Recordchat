"use client";

import { Search, SlidersHorizontal } from "lucide-react";
import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
import { CHAT_MODELS, type ChatModel } from "@/lib/api";
import { cn } from "@/lib/utils";

const MODEL_LABELS: Record<ChatModel, string> = {
  "deepseek-v4-fast": "DeepSeek V4 Fast",
  "deepseek-v4-pro": "DeepSeek V4 Pro",
};

export function ModelPicker({
  value,
  onChange,
  disabled,
}: {
  value: ChatModel;
  onChange: (model: ChatModel) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const rootRef = useRef<HTMLDivElement>(null);
  const filteredModels = useMemo(
    () =>
      CHAT_MODELS.filter((model) =>
        MODEL_LABELS[model].toLowerCase().includes(query.trim().toLowerCase())
      ),
    [query]
  );

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, []);

  return (
    <div ref={rootRef} className="relative">
      {open ? (
        <div className="absolute bottom-10 left-0 z-30 w-[280px] rounded-2xl border border-neutral-200 bg-white p-2 shadow-[0_18px_42px_rgba(15,23,42,0.14)]">
          <label className="flex h-9 items-center gap-2 rounded-full border border-neutral-200 bg-neutral-50 px-3 text-neutral-400">
            <Search className="h-4 w-4" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search models..."
              className="min-w-0 flex-1 bg-transparent text-sm text-neutral-900 outline-none placeholder:text-neutral-400"
            />
          </label>

          <div className="px-3 pb-2 pt-4 text-xs font-medium text-neutral-500">
            Available
          </div>
          <div className="space-y-1">
            {filteredModels.map((model) => (
              <button
                key={model}
                type="button"
                onClick={() => {
                  onChange(model);
                  setOpen(false);
                  setQuery("");
                }}
                className={cn(
                  "flex h-9 w-full items-center gap-2 rounded-lg px-3 text-left text-sm transition hover:bg-neutral-100",
                  value === model ? "bg-neutral-100 text-neutral-950" : "text-neutral-700"
                )}
              >
                <Image
                  src="/deepseek-mark.svg"
                  alt=""
                  width={16}
                  height={12}
                  className="h-3.5 w-4 shrink-0 text-neutral-950"
                />
                <span className="flex-1">{MODEL_LABELS[model]}</span>
                <SlidersHorizontal className="h-3.5 w-3.5 text-neutral-500" />
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        disabled={disabled}
        className="inline-flex h-8 items-center gap-2 rounded-full bg-neutral-100 px-3 text-xs font-semibold text-neutral-900 transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:text-neutral-400"
      >
        <Image
          src="/deepseek-mark.svg"
          alt=""
          width={16}
          height={12}
          className="h-3.5 w-4"
        />
        {MODEL_LABELS[value]}
      </button>
    </div>
  );
}
