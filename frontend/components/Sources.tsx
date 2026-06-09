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
      <ul className="space-y-2.5">
        {sources.map((s, index) => (
          <li
            key={s.chunk_id}
            className="group rounded-[22px] border border-slate-200/80 bg-gradient-to-br from-white to-slate-50/80 px-3 py-3 text-xs text-slate-600 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-teal-200 hover:shadow-[0_16px_36px_rgba(15,23,42,0.08)]"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="mb-2 flex items-center gap-2">
                  <span className="inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-slate-900 px-1.5 text-[10px] font-semibold text-white">
                    {index + 1}
                  </span>
                  <p className="font-semibold text-slate-800">{s.source_name}</p>
                </div>
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
                  className="shrink-0 rounded-full border border-teal-200 bg-white px-3 py-1 text-[11px] font-medium text-teal-800 transition group-hover:border-teal-300 group-hover:bg-teal-50"
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
