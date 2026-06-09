import type { ChatResponse } from "@/lib/api";
import { JsonLdViewer } from "./JsonLdViewer";
import { QueryTypeBadge } from "./QueryTypeBadge";
import { Sources } from "./Sources";

export function InspectorPanel({
  latest,
  loading,
  className = "",
}: {
  latest?: ChatResponse;
  loading: boolean;
  className?: string;
}) {
  return (
    <aside className={`w-full shrink-0 border-black/5 bg-white/70 ${className}`}>
      <div className="border-b border-black/5 px-5 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-teal-700">
          Conversation Inspector
        </p>
        <h3 className="mt-1 text-lg font-semibold text-slate-900">
          Sources, relationships, and structured output
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5">
        {!latest ? (
          <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50/70 px-5 py-6 text-sm leading-6 text-slate-500">
            Ask a question to pin grounded metadata here. This panel will surface
            the latest query type, source citations, related concepts, and JSON-LD
            output when available.
          </div>
        ) : (
          <div className="space-y-5">
            <section className="rounded-3xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                Query Type
              </p>
              <div className="mt-3">
                <QueryTypeBadge queryType={latest.query_type} />
              </div>
            </section>

            <section className="rounded-3xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                Related Concepts
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {latest.related_concepts.length ? (
                  latest.related_concepts.map((concept) => (
                    <span
                      key={concept}
                      className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-700"
                    >
                      {concept}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-slate-500">
                    No related concepts surfaced for the latest answer.
                  </span>
                )}
              </div>
            </section>

            <section className="rounded-3xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                Sources
              </p>
              <Sources sources={latest.sources} />
            </section>

            {latest.structured_output ? (
              <section className="rounded-3xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                  Structured Output
                </p>
                <JsonLdViewer data={latest.structured_output} />
              </section>
            ) : null}
          </div>
        )}
      </div>

      <div className="border-t border-black/5 px-5 py-3 text-xs text-slate-500">
        {loading
          ? "Streaming answer metadata will land here when generation completes."
          : "Inspector updates after each assistant answer."}
      </div>
    </aside>
  );
}
