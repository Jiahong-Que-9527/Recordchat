"use client";

import { useState } from "react";
import { Braces, Check, ChevronDown, Copy, RefreshCw } from "lucide-react";
import { getMessageData, getMessageText, type RecordChatMessage } from "@/lib/api";
import { JsonLdViewer } from "./JsonLdViewer";
import { MarkdownAnswer } from "./MarkdownAnswer";
import { QueryTypeBadge } from "./QueryTypeBadge";

function ActionButton({
  onClick,
  label,
  children,
}: {
  onClick: () => void;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
    >
      {children}
    </button>
  );
}

export function Message({
  message,
  isLast = false,
  loading = false,
  onRegenerate,
}: {
  message: RecordChatMessage;
  isLast?: boolean;
  loading?: boolean;
  onRegenerate?: () => void;
}) {
  const text = getMessageText(message);
  const data = getMessageData(message);
  const streaming = message.parts.some(
    (part) => part.type === "text" && part.state === "streaming"
  );
  const [copied, setCopied] = useState(false);

  async function copy() {
    if (!text) return;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  if (message.role === "user") {
    return (
      <div className="flex justify-end animate-[recordchat-rise_220ms_ease-out]">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-accent px-4 py-2.5 text-sm leading-6 text-white shadow-rc-sm">
          {text}
        </div>
      </div>
    );
  }

  return (
    <div className="group flex justify-start animate-[recordchat-rise_220ms_ease-out]">
      <div className="w-full max-w-full">
        <div className="mb-2 flex items-center gap-2">
          <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-accent-weak text-[10px] font-semibold text-accent">
            RC
          </span>
          <span className="text-sm font-semibold text-slate-800">RecordChat</span>
          {data?.query_type ? <QueryTypeBadge queryType={data.query_type} /> : null}
        </div>

        <div className="rounded-2xl rounded-tl-md border border-slate-200 bg-white px-4 py-3.5 shadow-rc-sm">
          <MarkdownAnswer text={text} streaming={streaming} />

          {streaming ? (
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
              <span className="inline-block h-3.5 w-1.5 animate-pulse rounded-sm bg-accent" />
              <span>Composing…</span>
            </div>
          ) : (
            <div className="mt-2 flex items-center gap-0.5 opacity-60 transition group-hover:opacity-100 focus-within:opacity-100">
              <ActionButton onClick={copy} label={copied ? "Copied" : "Copy answer"}>
                {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              </ActionButton>
              {isLast && !loading && onRegenerate ? (
                <ActionButton onClick={onRegenerate} label="Regenerate answer">
                  <RefreshCw className="h-3.5 w-3.5" />
                </ActionButton>
              ) : null}
            </div>
          )}
        </div>

        {!streaming && data?.structured_output ? (
          <details className="group/jsonld mt-2 rounded-xl border border-slate-200 bg-white shadow-rc-sm">
            <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-2.5 text-sm font-medium text-slate-700 [&::-webkit-details-marker]:hidden">
              <Braces className="h-4 w-4 text-slate-400" />
              Structured output (JSON-LD)
              <ChevronDown className="ml-auto h-4 w-4 text-slate-400 transition group-open/jsonld:rotate-180" />
            </summary>
            <div className="px-4 pb-4 pt-0">
              <JsonLdViewer data={data.structured_output} />
            </div>
          </details>
        ) : null}
      </div>
    </div>
  );
}
