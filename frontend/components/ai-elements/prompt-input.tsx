"use client";

import type * as React from "react";
import { ArrowUp, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

export function PromptInput({
  children,
  className,
  onSubmit,
}: {
  children: React.ReactNode;
  className?: string;
  onSubmit: React.FormEventHandler<HTMLFormElement>;
}) {
  return (
    <form
      onSubmit={onSubmit}
      className={cn(
        "rc-glass mx-auto flex w-full max-w-[864px] flex-col gap-2 rounded-2xl p-3 shadow-rc-md transition focus-within:border-accent-ring/90 focus-within:shadow-rc-glow",
        className
      )}
    >
      {children}
    </form>
  );
}

export function PromptInputTextarea(
  props: React.TextareaHTMLAttributes<HTMLTextAreaElement> & {
    onSubmitShortcut?: () => void;
  }
) {
  const { onSubmitShortcut, onKeyDown, ...rest } = props;
  return (
    <Textarea
      {...rest}
      rows={3}
      aria-label="Message RecordChat"
      className="min-h-[92px] resize-none border-none bg-transparent px-2 py-2 text-[15px] leading-7 text-slate-800 shadow-none placeholder:text-slate-400 focus-visible:ring-0"
      onKeyDown={(event) => {
        onKeyDown?.(event);
        if (event.defaultPrevented) {
          return;
        }
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          onSubmitShortcut?.();
        }
      }}
    />
  );
}

export function PromptInputToolbar({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex items-center justify-between gap-3 px-1 pt-1", className)}>
      {children}
    </div>
  );
}

export function PromptInputSubmit({
  isLoading,
  disabled,
  onStop,
}: {
  isLoading: boolean;
  disabled?: boolean;
  onStop?: () => void;
}) {
  if (isLoading) {
    return (
      <Button
        type="button"
        size="icon"
        variant="secondary"
        onClick={onStop}
        aria-label="Stop generating"
        className="h-8 w-8 rounded-full border-slate-200 bg-white text-slate-700 shadow-rc-sm hover:bg-slate-50"
      >
        <Square className="h-3.5 w-3.5 fill-current" />
      </Button>
    );
  }

  return (
    <Button
      type="submit"
      size="icon"
      disabled={disabled}
      aria-label="Send message"
      className="rc-gradient-bg h-8 w-8 rounded-full text-white shadow-rc-glow transition hover:brightness-110 disabled:bg-slate-100 disabled:text-slate-300 disabled:shadow-none"
    >
      <ArrowUp className="h-4 w-4" />
    </Button>
  );
}
