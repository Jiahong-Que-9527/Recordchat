import type { Source } from "@/lib/api";

export function Sources({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return (
    <div className="mt-3">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
          Sources
        </p>
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-600">
          {sources.length}
        </span>
      </div>
      <ul className="space-y-2">
        {sources.map((s) => (
          <li
            key={s.chunk_id}
            className="rounded-2xl border border-slate-200 bg-slate-50/70 px-3 py-3 text-xs text-slate-600"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-semibold text-slate-800">{s.source_name}</p>
                {s.section_title ? (
                  <p className="mt-1 text-[11px] leading-5 text-slate-500">{s.section_title}</p>
                ) : null}
                <p className="mt-2 text-[10px] uppercase tracking-[0.18em] text-slate-400">
                  {s.chunk_id}
                </p>
              </div>
              {s.source_url ? (
                <a
                  href={s.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="shrink-0 rounded-full border border-teal-200 bg-white px-3 py-1 text-[11px] font-medium text-teal-800 transition hover:bg-teal-50"
                >
                  Open
                </a>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
