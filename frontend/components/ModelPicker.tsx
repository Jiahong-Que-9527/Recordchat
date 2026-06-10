"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { Check, ChevronDown } from "lucide-react";
import { CHAT_MODELS, type ChatModel } from "@/lib/api";
import { cn } from "@/lib/utils";

const MODEL_LABELS: Record<ChatModel, string> = {
  "deepseek-v4-flash": "DeepSeek V4 Flash",
  "deepseek-v4-pro": "DeepSeek V4 Pro",
};

export function ModelPicker({
  value,
  onChange,
  disabled,
}: {
  value: ChatModel;
  onChange: (value: ChatModel) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Select model"
        onClick={() => setOpen((current) => !current)}
        className={cn(
          "relative inline-flex h-8 items-center gap-2 rounded-full border border-neutral-200 bg-neutral-100 pl-3 pr-8 text-xs font-semibold text-neutral-900 transition hover:bg-neutral-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-ring focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-60",
          open && "border-neutral-300 bg-white shadow-rc-sm"
        )}
      >
        <Image
          src="/deepseek-mark.svg"
          alt=""
          width={16}
          height={12}
          className="h-3.5 w-4"
        />
        {MODEL_LABELS[value]}
        <ChevronDown
          aria-hidden="true"
          className={cn(
            "pointer-events-none absolute right-3 top-1/2 h-3 w-3 -translate-y-1/2 text-neutral-500 transition-transform",
            open && "rotate-180"
          )}
        />
      </button>

      {open ? (
        <div
          role="listbox"
          aria-label="Model options"
          className="absolute bottom-full left-0 z-50 mb-2 min-w-[220px] overflow-hidden rounded-xl border border-neutral-200 bg-white p-1 shadow-rc-md animate-[recordchat-rise_180ms_ease-out]"
        >
          {CHAT_MODELS.map((model) => {
            const selected = model === value;

            return (
              <button
                key={model}
                type="button"
                role="option"
                aria-selected={selected}
                onClick={() => {
                  onChange(model);
                  setOpen(false);
                }}
                className={cn(
                  "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-xs font-medium text-neutral-800 transition hover:bg-neutral-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-ring",
                  selected && "bg-neutral-100"
                )}
              >
                <Image
                  src="/deepseek-mark.svg"
                  alt=""
                  width={16}
                  height={12}
                  className="h-3.5 w-4 shrink-0"
                />
                <span className="flex-1">{MODEL_LABELS[model]}</span>
                {selected ? (
                  <Check aria-hidden="true" className="h-3.5 w-3.5 shrink-0 text-neutral-600" />
                ) : (
                  <span aria-hidden="true" className="h-3.5 w-3.5 shrink-0" />
                )}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
