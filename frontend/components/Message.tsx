"use client";

import { memo, useState } from "react";
import {
  Braces,
  Check,
  Copy,
  Maximize2,
  Pencil,
  RefreshCw,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  X,
} from "lucide-react";
import { getMessageData, getMessageText, type RecordChatMessage } from "@/lib/api";
import { cn, copyText } from "@/lib/utils";
import { MarkdownAnswer } from "./MarkdownAnswer";
import { Sources } from "./Sources";
import { TypingIndicator } from "./TypingIndicator";

// Title shown on the structured-output artifact card / canvas header. Prefer the
// JSON-LD @type when present, otherwise fall back to a generic label.
export function canvasTitle(data: Record<string, unknown>): string {
  const type = data["@type"];
  if (typeof type === "string" && type.trim()) {
    return type.split(/[#/]/).pop() || type;
  }
  return "Structured output";
}

// A short, one-glance peek at the structured output for the artifact card —
// the first few non-empty lines of pretty-printed JSON.
function canvasPreview(data: Record<string, unknown>): string {
  return JSON.stringify(data, null, 2)
    .split("\n")
    .slice(0, 3)
    .join("\n");
}

function ActionButton({
  onClick,
  label,
  active = false,
  children,
}: {
  onClick: () => void;
  label: string;
  active?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      aria-pressed={active}
      title={label}
      className={cn(
        "inline-flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-600",
        active && "bg-slate-100 text-slate-700"
      )}
    >
      {children}
    </button>
  );
}

// Touch devices (mobile/tablet) can't hover, so action rows are always visible
// below xl; on desktop they stay hidden until the message is hovered (or a
// button inside is focused for keyboard users).
const ACTION_ROW_CLASS =
  "flex items-center gap-0.5 opacity-100 transition xl:opacity-0 group-hover:opacity-100 focus-within:opacity-100";

function AssistantAvatar() {
  return (
    <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-neutral-100 text-neutral-500">
      <Sparkles className="h-4 w-4" />
    </span>
  );
}

function MetadataLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
      {children}
    </p>
  );
}

function MessageComponent({
  message,
  isLast = false,
  loading = false,
  onRegenerate,
  onEdit,
  onToggleCanvas,
  activeCanvasId,
}: {
  message: RecordChatMessage;
  isLast?: boolean;
  loading?: boolean;
  onRegenerate?: () => void;
  onEdit?: (messageId: string, text: string) => void;
  onToggleCanvas?: (
    messageId: string,
    title: string,
    data: Record<string, unknown>
  ) => void;
  activeCanvasId?: string | null;
}) {
  const text = getMessageText(message);
  const data = getMessageData(message);
  const streaming = message.parts.some(
    (part) => part.type === "text" && part.state === "streaming"
  );
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(text);

  async function copy() {
    if (await copyText(text)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    }
  }

  if (message.role === "user") {
    if (editing) {
      function submitEdit() {
        const next = draft.trim();
        if (!next || !onEdit) return;
        setEditing(false);
        onEdit(message.id, next);
      }

      return (
        <div className="flex justify-end animate-[recordchat-rise_220ms_ease-out]">
          <div className="w-full max-w-[85%]">
            <textarea
              value={draft}
              autoFocus
              rows={Math.min(Math.max(draft.split("\n").length, 2), 8)}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  submitEdit();
                }
                if (event.key === "Escape") {
                  setEditing(false);
                  setDraft(text);
                }
              }}
              className="w-full resize-none rounded-2xl border border-neutral-300 bg-white px-4 py-2.5 text-sm leading-6 text-neutral-900 shadow-rc-sm outline-none focus-visible:border-accent-ring focus-visible:ring-2 focus-visible:ring-accent-ring"
            />
            <div className="mt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setEditing(false);
                  setDraft(text);
                }}
                className="rounded-lg border border-neutral-200 bg-white px-3 py-1 text-xs font-medium text-neutral-600 transition hover:bg-neutral-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={submitEdit}
                disabled={!draft.trim()}
                className="rounded-lg bg-accent px-3 py-1 text-xs font-semibold text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="group flex flex-col items-end gap-1 animate-[recordchat-rise_220ms_ease-out]">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-accent-soft px-4 py-2.5 text-sm leading-6 text-slate-800">
          {text}
        </div>
        <div className={ACTION_ROW_CLASS}>
          {onEdit ? (
            <ActionButton
              onClick={() => {
                setDraft(text);
                setEditing(true);
              }}
              label="Edit message"
            >
              <Pencil className="h-3.5 w-3.5" />
            </ActionButton>
          ) : null}
          <ActionButton onClick={copy} label={copied ? "Copied" : "Copy message"}>
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          </ActionButton>
        </div>
      </div>
    );
  }

  if (streaming && !text.trim()) {
    return (
      <div className="animate-[recordchat-rise_220ms_ease-out]">
        <TypingIndicator label="Thinking..." />
      </div>
    );
  }

  const showMetadata = !streaming && data;

  return (
    <div className="group flex gap-3 animate-[recordchat-rise_220ms_ease-out]">
      <AssistantAvatar />
      <div className="min-w-0 flex-1">
        <MarkdownAnswer text={text} streaming={streaming} />

        {showMetadata && data.structured_output ? (
          (() => {
            const output = data.structured_output;
            const canvasOpen = activeCanvasId === message.id;
            return (
              <button
                type="button"
                aria-expanded={canvasOpen}
                onClick={() =>
                  onToggleCanvas?.(message.id, canvasTitle(output), output)
                }
                className={cn(
                  "mt-4 flex w-full items-stretch gap-3 rounded-xl border px-3 py-3 text-left transition",
                  canvasOpen
                    ? "border-accent bg-accent-weak"
                    : "border-accent-ring bg-accent-weak/50 hover:bg-accent-weak"
                )}
              >
                <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-accent shadow-rc-sm">
                  <Braces className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-semibold text-neutral-900">
                    {canvasTitle(output)}
                  </span>
                  <span className="block text-xs text-neutral-500">
                    Structured output (JSON-LD) ·{" "}
                    {canvasOpen ? "Click to close" : "Click to open"}
                  </span>
                  <pre className="mt-1.5 max-h-12 overflow-hidden whitespace-pre-wrap break-all font-mono text-[10px] leading-4 text-neutral-400">
                    {canvasPreview(output)}
                  </pre>
                </span>
                {canvasOpen ? (
                  <X className="h-4 w-4 shrink-0 text-neutral-400" />
                ) : (
                  <Maximize2 className="h-4 w-4 shrink-0 text-neutral-400" />
                )}
              </button>
            );
          })()
        ) : null}

        {showMetadata && data.sources.length > 0 ? (
          <div className="mt-4">
            <MetadataLabel>Sources</MetadataLabel>
            <Sources sources={data.sources} />
          </div>
        ) : null}

        {showMetadata && data.related_concepts.length > 0 ? (
          <div className="mt-4">
            <MetadataLabel>Related concepts</MetadataLabel>
            <div className="flex flex-wrap gap-2">
              {data.related_concepts.map((concept) => (
                <span
                  key={concept}
                  className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600"
                >
                  {concept}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        {!streaming ? (
          <div className={cn(ACTION_ROW_CLASS, "mt-3")}>
            <ActionButton onClick={copy} label={copied ? "Copied" : "Copy answer"}>
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            </ActionButton>
            <ActionButton
              onClick={() => setFeedback((current) => (current === "up" ? null : "up"))}
              label="Good response"
              active={feedback === "up"}
            >
              <ThumbsUp className="h-3.5 w-3.5" />
            </ActionButton>
            <ActionButton
              onClick={() => setFeedback((current) => (current === "down" ? null : "down"))}
              label="Bad response"
              active={feedback === "down"}
            >
              <ThumbsDown className="h-3.5 w-3.5" />
            </ActionButton>
            {isLast && !loading && onRegenerate ? (
              <ActionButton onClick={onRegenerate} label="Regenerate answer">
                <RefreshCw className="h-3.5 w-3.5" />
              </ActionButton>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}

// Memoised so completed messages don't re-render on every streamed token of a
// later message. Relies on stable `onRegenerate` / `onEdit` references.
export const Message = memo(MessageComponent);
