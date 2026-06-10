import { ExternalLink } from "lucide-react";
import type { Source } from "@/lib/api";

function SourceChip({ source, index }: { source: Source; index: number }) {
  const className =
    "inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 transition";
  const inner = (
    <>
      <span className="inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-slate-800 px-1 text-[10px] font-semibold text-white">
        {index + 1}
      </span>
      <span className="max-w-[22rem] truncate">{source.source_name}</span>
      {source.source_url ? <ExternalLink className="h-3 w-3 shrink-0 text-slate-400" /> : null}
    </>
  );

  // Prefer the section title as the hover tooltip when present.
  const title = source.section_title ?? source.source_name;

  if (source.source_url) {
    return (
      <a
        href={source.source_url}
        target="_blank"
        rel="noreferrer"
        title={title}
        className={`${className} hover:border-accent-ring hover:text-accent`}
      >
        {inner}
      </a>
    );
  }

  return (
    <span title={title} className={className}>
      {inner}
    </span>
  );
}

export function Sources({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {sources.map((source, index) => (
        <SourceChip key={source.chunk_id} source={source} index={index} />
      ))}
    </div>
  );
}
