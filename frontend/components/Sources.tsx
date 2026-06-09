import type { Source } from "@/lib/api";

export function Sources({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return (
    <ul className="space-y-2">
      {sources.map((s, index) => (
        <li
          key={s.chunk_id}
          className="group rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-xs text-slate-600 shadow-rc-sm transition hover:border-accent-ring"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-slate-800 px-1.5 text-[10px] font-semibold text-white">
                  {index + 1}
                </span>
                <p className="truncate font-medium text-slate-800">{s.source_name}</p>
              </div>
              {s.section_title ? (
                <p className="mt-1.5 text-[11px] leading-5 text-slate-500">{s.section_title}</p>
              ) : null}
            </div>
            {s.source_url ? (
              <a
                href={s.source_url}
                target="_blank"
                rel="noreferrer"
                className="shrink-0 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-accent transition hover:border-accent-ring hover:bg-accent-weak"
              >
                Open
              </a>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}
