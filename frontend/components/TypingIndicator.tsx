import { RecordChatIcon } from "@/components/RecordChatIcon";
import { cn } from "@/lib/utils";

function Dot({ delay }: { delay: string }) {
  return (
    <span
      aria-hidden="true"
      className="rc-gradient-bg h-1.5 w-1.5 rounded-full"
      style={{
        animation: `recordchat-dot 1.2s ${delay} ease-in-out infinite`,
      }}
    />
  );
}

export function TypingIndicator({
  label = "Thinking",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div
      role="status"
      aria-label={label}
      className={cn(
        "flex items-center gap-2.5 animate-[recordchat-rise_280ms_ease-out]",
        className
      )}
    >
      <RecordChatIcon size="sm" />
      <span className="flex items-center gap-1.5 text-sm font-medium text-slate-500">
        <span className="flex items-center gap-1">
          <Dot delay="0s" />
          <Dot delay="0.15s" />
          <Dot delay="0.3s" />
        </span>
        <span className="ml-1">{label}</span>
      </span>
    </div>
  );
}
