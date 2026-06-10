"use client";

import { Braces, X } from "lucide-react";
import { JsonLdViewer } from "./JsonLdViewer";

export function Canvas({
  title,
  data,
  onClose,
  className = "",
}: {
  title: string;
  data: Record<string, unknown>;
  onClose: () => void;
  className?: string;
}) {
  return (
    <aside
      className={`flex h-full min-h-0 flex-col bg-white animate-[recordchat-slide-right_260ms_ease-out] ${className}`}
    >
      <div className="flex h-12 shrink-0 items-center justify-between gap-3 border-b border-neutral-200 px-4">
        <div className="flex min-w-0 items-center gap-2.5">
          <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent-weak text-accent">
            <Braces className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <h3 className="truncate text-sm font-semibold text-neutral-900">{title}</h3>
            <p className="text-[11px] leading-none text-neutral-500">
              Structured output (JSON-LD)
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close canvas"
          title="Close"
          className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-neutral-400 transition hover:bg-neutral-100 hover:text-neutral-700"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-4">
        <JsonLdViewer data={data} />
      </div>
    </aside>
  );
}
