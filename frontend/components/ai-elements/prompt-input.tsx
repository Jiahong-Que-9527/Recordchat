"use client";

import type * as React from "react";
import { ArrowUp, Loader2 } from "lucide-react";
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
        "mx-auto flex w-full max-w-4xl flex-col gap-3 rounded-[30px] border border-white/80 bg-[linear-gradient(180deg,_rgba(255,255,255,0.94)_0%,_rgba(247,250,249,0.92)_100%)] p-3 shadow-[0_22px_54px_rgba(15,23,42,0.10)] ring-1 ring-white/70 backdrop-blur sm:p-4",
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
      className="min-h-[92px] resize-none border-none bg-transparent px-2 py-1 text-[15px] leading-7 shadow-none focus-visible:ring-0"
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
    <div className={cn("flex items-center justify-between gap-3 border-t border-slate-200/80 pt-3", className)}>
      {children}
    </div>
  );
}

export function PromptInputSubmit({
  isLoading,
  disabled,
}: {
  isLoading: boolean;
  disabled?: boolean;
}) {
  return (
    <Button
      type="submit"
      size="icon"
      disabled={disabled || isLoading}
      className="rounded-2xl shadow-[0_14px_30px_rgba(15,118,110,0.25)]"
    >
      {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
    </Button>
  );
}
