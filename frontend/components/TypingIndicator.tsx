export function TypingIndicator({ label }: { label: string }) {
  return (
    <div className="inline-flex items-center gap-2.5 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-600 shadow-rc-sm animate-[recordchat-rise_280ms_ease-out]">
      <span className="flex items-center gap-1">
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-accent [animation-delay:-0.25s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-accent/70 [animation-delay:-0.1s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-accent/40" />
      </span>
      <span>{label}</span>
    </div>
  );
}
