"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { copyText } from "@/lib/utils";

export function JsonLdViewer({ data }: { data: Record<string, unknown> }) {
  const [copied, setCopied] = useState(false);
  const [mode, setMode] = useState<"structured" | "raw">("structured");
  const serialized = JSON.stringify(data, null, 2);
  const entries = Object.entries(data);

  async function copy() {
    if (await copyText(serialized)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    }
  }

  return (
    <div className="mt-3 overflow-hidden rounded-xl border border-slate-800 bg-slate-950 shadow-rc-md">
      <div className="border-b border-slate-800/90 px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <span className="text-sm font-semibold text-slate-200">JSON-LD Output</span>
            <div className="mt-2 flex items-center gap-2">
              <Badge variant="outline" className="border-slate-700 bg-slate-900 text-slate-300">
                {entries.length} top-level fields
              </Badge>
            </div>
          </div>
          <button
            type="button"
            onClick={copy}
            aria-label="Copy JSON-LD to clipboard"
            className="rounded-lg border border-slate-700 px-3 py-1 text-[11px] font-medium text-slate-200 transition hover:border-slate-500 hover:text-white"
          >
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
        <div className="mt-3 inline-flex rounded-lg border border-slate-800 bg-slate-900/80 p-1">
          {(["structured", "raw"] as const).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setMode(option)}
              className={`rounded-md px-3 py-1 text-[11px] font-medium transition ${
                mode === option
                  ? "bg-slate-100 text-slate-950"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {option === "structured" ? "Structured" : "Raw"}
            </button>
          ))}
        </div>
      </div>
      {mode === "structured" ? (
        <div className="space-y-3 p-4">
          {entries.map(([key, value]) => (
            <div
              key={key}
              className="rounded-lg border border-slate-800 bg-slate-900/80 p-3"
            >
              <div className="mb-2 flex items-center justify-between gap-3">
                <span className="font-mono text-[11px] font-semibold text-sky-300">
                  {key}
                </span>
                <span className="text-[10px] uppercase tracking-[0.18em] text-slate-500">
                  {Array.isArray(value)
                    ? `array(${value.length})`
                    : value === null
                      ? "null"
                      : typeof value}
                </span>
              </div>
              <pre className="overflow-x-auto text-xs leading-relaxed text-slate-200">
                <code>{JSON.stringify(value, null, 2)}</code>
              </pre>
            </div>
          ))}
        </div>
      ) : (
        <pre className="overflow-x-auto p-4 text-xs leading-relaxed text-slate-100">
          <code>{serialized}</code>
        </pre>
      )}
    </div>
  );
}
