export function JsonLdViewer({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="mt-3 rounded-lg border border-border bg-slate-950">
      <div className="flex items-center justify-between border-b border-slate-800 px-3 py-1.5">
        <span className="text-xs font-medium text-slate-400">JSON-LD example (illustrative)</span>
      </div>
      <pre className="overflow-x-auto p-3 text-xs leading-relaxed text-slate-100">
        <code>{JSON.stringify(data, null, 2)}</code>
      </pre>
    </div>
  );
}
