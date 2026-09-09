"use client";

import { useState } from "react";
import { Braces, X } from "lucide-react";
import { JsonLdViewer, JsonLdViewerToolbar } from "./JsonLdViewer";
import { cn } from "@/lib/utils";

export function CanvasToggleButton({
  open,
  onClick,
  className,
}: {
  open: boolean;
  onClick: () => void;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={open ? "Close JSON-LD panel" : "Open JSON-LD panel"}
      aria-pressed={open}
      title={open ? "Close JSON-LD panel" : "Open JSON-LD panel"}
      className={cn(
        "inline-flex h-8 w-8 items-center justify-center rounded-xl border text-slate-500 shadow-rc-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-ring focus-visible:ring-offset-2",
        open
          ? "border-accent-ring bg-accent-weak text-accent"
          : "border-slate-200/90 bg-white/80 hover:border-accent-ring hover:text-accent",
        className
      )}
    >
      <Braces className="h-4 w-4" />
    </button>
  );
}

function CanvasEmptyState({ onAskExample }: { onAskExample?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <span className="rc-gradient-bg inline-flex h-12 w-12 items-center justify-center rounded-2xl text-white shadow-rc-sm">
        <Braces className="h-5 w-5" />
      </span>
      <p className="mt-4 text-sm font-medium text-slate-700">No JSON-LD output yet</p>
      <p className="mt-2 max-w-[240px] text-xs leading-5 text-slate-500">
        Structured JSON-LD from assistant answers will appear here. You can keep
        this panel open while you chat.
      </p>
      {onAskExample ? (
        <button
          type="button"
          onClick={onAskExample}
          className="mt-5 rounded-xl border border-accent-ring/80 bg-accent-weak/50 px-3 py-2 text-xs font-medium text-accent transition hover:bg-accent-weak"
        >
          Try: Generate a JSON-LD example for a Piece
        </button>
      ) : null}
    </div>
  );
}

export function Canvas({
  title,
  data,
  onClose,
  onAskExample,
  className = "",
}: {
  title: string;
  data: Record<string, unknown> | null;
  onClose: () => void;
  onAskExample?: () => void;
  className?: string;
}) {
  const [mode, setMode] = useState<"structured" | "raw">("structured");
  const entries = data ? Object.entries(data) : [];
  const hasData = data !== null && entries.length > 0;

  return (
    <aside
      className={cn(
        "rc-glass flex h-full min-h-0 flex-col border-l border-white/70 animate-[recordchat-slide-right_260ms_ease-out]",
        className
      )}
    >
      <header className="shrink-0 border-b border-slate-200/70 px-5 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-3">
            <span className="rc-gradient-bg inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-white shadow-rc-sm">
              <Braces className="h-4 w-4" />
            </span>
            <div className="min-w-0 pt-0.5">
              <h3 className="truncate text-base font-semibold text-slate-900">
                {hasData ? title : "JSON-LD Output"}
              </h3>
              <p className="mt-0.5 text-xs text-slate-500">
                Structured output · JSON-LD
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close canvas"
            title="Close"
            className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-slate-400 transition hover:bg-white/80 hover:text-slate-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {hasData ? (
          <div className="mt-4">
            <JsonLdViewerToolbar
              fieldCount={entries.length}
              mode={mode}
              onModeChange={setMode}
              data={data}
            />
          </div>
        ) : null}
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
        {hasData && data ? (
          <JsonLdViewer data={data} mode={mode} />
        ) : (
          <CanvasEmptyState onAskExample={onAskExample} />
        )}
      </div>
    </aside>
  );
}
