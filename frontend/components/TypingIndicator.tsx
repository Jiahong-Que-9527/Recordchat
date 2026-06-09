export function TypingIndicator({ label }: { label: string }) {
  return (
    <div className="inline-flex items-center gap-3 rounded-full border border-teal-200/70 bg-teal-50/80 px-3 py-2 text-xs font-medium text-teal-800 shadow-sm">
      <span className="flex items-center gap-1.5">
        <span className="h-2 w-2 animate-bounce rounded-full bg-teal-600 [animation-delay:-0.25s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-teal-500 [animation-delay:-0.1s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-teal-400" />
      </span>
      <span>{label}</span>
    </div>
  );
}
