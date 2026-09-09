"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn, copyText } from "@/lib/utils";

function valueType(value: unknown): string {
  if (Array.isArray(value)) return `array · ${value.length}`;
  if (value === null) return "null";
  return typeof value;
}

function isScalar(value: unknown): boolean {
  const t = typeof value;
  return value === null || t === "string" || t === "number" || t === "boolean";
}

function formatScalar(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "string") return value;
  return String(value);
}

function valueToCopy(value: unknown): string {
  if (isScalar(value)) return formatScalar(value);
  return JSON.stringify(value, null, 2);
}

function CopyIconButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    if (await copyText(text)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    }
  }

  return (
    <button
      type="button"
      onClick={copy}
      aria-label={label}
      title={copied ? "Copied" : label}
      className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-slate-400 opacity-0 transition hover:bg-white/90 hover:text-accent focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-ring group-hover:opacity-100 [@media(hover:none)]:opacity-45"
    >
      {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
    </button>
  );
}

function FieldCard({ keyName, value }: { keyName: string; value: unknown }) {
  const isJsonLdMeta = keyName.startsWith("@");

  return (
    <article
      className={cn(
        "group rounded-xl border bg-white/80 p-3.5 shadow-rc-sm transition",
        isJsonLdMeta
          ? "border-accent-ring/80 bg-accent-weak/40"
          : "border-slate-200/90"
      )}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <span
          className={cn(
            "min-w-0 font-mono text-xs font-semibold",
            isJsonLdMeta ? "text-accent" : "text-slate-800"
          )}
        >
          {keyName}
        </span>
        <div className="flex shrink-0 items-center gap-1">
          <CopyIconButton
            text={valueToCopy(value)}
            label={`Copy ${keyName}`}
          />
          <Badge
            variant="outline"
            className="border-accent-ring/70 bg-white/90 text-[10px] uppercase tracking-wide text-slate-500"
          >
            {valueType(value)}
          </Badge>
        </div>
      </div>
      {isScalar(value) ? (
        <p className="break-all font-mono text-sm leading-6 text-slate-700">
          {formatScalar(value)}
        </p>
      ) : (
        <pre className="overflow-x-auto rounded-lg border border-slate-200/80 bg-slate-50/90 p-3 text-xs leading-relaxed text-slate-700">
          <code>{JSON.stringify(value, null, 2)}</code>
        </pre>
      )}
    </article>
  );
}

export function JsonLdViewer({
  data,
  mode,
}: {
  data: Record<string, unknown>;
  mode: "structured" | "raw";
}) {
  const serialized = JSON.stringify(data, null, 2);
  const entries = Object.entries(data);

  return mode === "structured" ? (
    <div className="space-y-2.5">
      {entries.map(([key, value]) => (
        <FieldCard key={key} keyName={key} value={value} />
      ))}
    </div>
  ) : (
    <div className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white/80 shadow-rc-sm">
      <div className="absolute right-2 top-2 z-10">
        <CopyIconButton text={serialized} label="Copy JSON-LD" />
      </div>
      <pre className="overflow-x-auto p-4 pt-9 text-xs leading-relaxed text-slate-700">
        <code>{serialized}</code>
      </pre>
    </div>
  );
}

export function JsonLdViewerToolbar({
  fieldCount,
  mode,
  onModeChange,
  data,
}: {
  fieldCount: number;
  mode: "structured" | "raw";
  onModeChange: (mode: "structured" | "raw") => void;
  data: Record<string, unknown>;
}) {
  const [copied, setCopied] = useState(false);
  const serialized = JSON.stringify(data, null, 2);

  async function copy() {
    if (await copyText(serialized)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    }
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <Badge
        variant="outline"
        className="border-accent-ring/70 bg-accent-weak/50 text-slate-600"
      >
        {fieldCount} top-level fields
      </Badge>

      <div className="flex items-center gap-2">
        <div className="inline-flex rounded-xl border border-slate-200/90 bg-white/70 p-1 shadow-rc-sm">
          {(["structured", "raw"] as const).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => onModeChange(option)}
              className={cn(
                "rounded-lg px-3 py-1 text-[11px] font-medium transition",
                mode === option
                  ? "rc-gradient-bg text-white shadow-rc-sm"
                  : "text-slate-500 hover:text-slate-800"
              )}
            >
              {option === "structured" ? "Structured" : "Raw"}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={copy}
          aria-label="Copy JSON-LD to clipboard"
          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200/90 bg-white/80 px-3 py-1.5 text-[11px] font-medium text-slate-600 shadow-rc-sm transition hover:border-accent-ring hover:text-accent"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5" />
              Copied
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              Copy
            </>
          )}
        </button>
      </div>
    </div>
  );
}
