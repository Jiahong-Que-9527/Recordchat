export function TypingIndicator({ label }: { label: string }) {
  return (
    <div className="inline-flex items-center gap-3 rounded-full border border-teal-200/80 bg-white/85 px-3 py-2.5 text-xs font-medium text-teal-900 shadow-[0_14px_34px_rgba(15,23,42,0.08)] ring-1 ring-white/70 backdrop-blur animate-[recordchat-rise_280ms_ease-out]">
      <span className="flex items-center gap-2">
        <span className="relative flex h-6 w-6 items-center justify-center rounded-full bg-teal-50">
          <span className="absolute inset-0 rounded-full border border-teal-200/80" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-teal-600 [animation-delay:-0.25s]" />
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-600 [animation-delay:-0.25s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-500 [animation-delay:-0.1s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-400" />
        </span>
      </span>
      <div className="flex flex-col">
        <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-teal-600">
          Live Response
        </span>
        <span>{label}</span>
      </div>
    </div>
  );
}
