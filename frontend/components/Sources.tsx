import type { Source } from "@/lib/api";

export function Sources({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return (
    <div className="mt-3">
      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Sources
      </p>
      <ul className="space-y-1">
        {sources.map((s) => (
          <li key={s.chunk_id} className="text-xs text-slate-600">
            <span className="font-medium text-slate-700">{s.source_name}</span>
            {s.section_title ? ` — ${s.section_title}` : ""}
            {s.source_url ? (
              <>
                {" "}
                <a
                  href={s.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-accent underline"
                >
                  link
                </a>
              </>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
