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
        "mx-auto flex w-full max-w-4xl flex-col gap-3 rounded-[28px] border border-white/70 bg-white/85 p-3 shadow-[0_18px_48px_rgba(15,23,42,0.08)] backdrop-blur sm:p-4",
        className
      )}
    >
      {children}
    </form>
  );
}

export function PromptInputTextarea(
  props: React.TextareaHTMLAttributes<HTMLTextAreaElement>
) {
  return (
    <Textarea
      {...props}
      rows={3}
      className="min-h-[92px] resize-none border-none bg-transparent px-2 py-1 shadow-none focus-visible:ring-0"
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
    <div className={cn("flex items-center justify-between gap-3", className)}>
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
      className="rounded-2xl"
    >
      {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
    </Button>
  );
}
