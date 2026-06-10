import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export function TypingIndicator({
  label = "Thinking...",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-2.5 animate-[recordchat-rise_280ms_ease-out]",
        className
      )}
    >
      <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-neutral-100 text-neutral-500">
        <Sparkles className="h-4 w-4" />
      </span>
      <span className="animate-pulse text-sm font-medium text-neutral-500">
        {label}
      </span>
    </div>
  );
}
