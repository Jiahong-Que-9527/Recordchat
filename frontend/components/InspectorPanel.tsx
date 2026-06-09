import type { ChatResponse } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { InspectorSection } from "./InspectorSection";
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
  const sourceCount = latest?.sources.length ?? 0;
  const conceptCount = latest?.related_concepts.length ?? 0;
  const hasStructuredOutput = Boolean(latest?.structured_output);

  return (
    <aside className={`w-full shrink-0 bg-[linear-gradient(180deg,_rgba(255,255,255,0.90)_0%,_rgba(244,247,246,0.92)_100%)] ${className}`}>
      <div className="border-b border-black/5 px-5 py-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-teal-700">
              Conversation Inspector
            </p>
            <h3 className="mt-1 text-lg font-semibold text-slate-900">
              Evidence, schema links, and structured output
            </h3>
          </div>
          <Badge variant="outline" className="border-slate-200 bg-white text-slate-600">
            {loading ? "Live" : "Pinned"}
          </Badge>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5">
        {!latest ? (
          <div className="rounded-[28px] border border-dashed border-slate-200 bg-white/80 px-5 py-6 text-sm leading-6 text-slate-500 shadow-sm">
            Ask a question to pin grounded metadata here. This panel will surface
            the latest query type, source citations, related concepts, and JSON-LD
            output when available.
          </div>
        ) : (
          <div className="space-y-5">
            <section className="grid grid-cols-3 gap-3">
              <div className="rounded-[24px] border border-slate-200 bg-white px-3 py-3 shadow-sm">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                  Sources
                </p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">{sourceCount}</p>
              </div>
              <div className="rounded-[24px] border border-slate-200 bg-white px-3 py-3 shadow-sm">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                  Concepts
                </p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">{conceptCount}</p>
              </div>
              <div className="rounded-[24px] border border-slate-200 bg-white px-3 py-3 shadow-sm">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                  JSON-LD
                </p>
                <p className="mt-2 text-sm font-semibold text-slate-900">
                  {hasStructuredOutput ? "Available" : "None"}
                </p>
              </div>
            </section>

            <InspectorSection title="Query Type" caption="Routing decision" defaultOpen>
              <QueryTypeBadge queryType={latest.query_type} />
            </InspectorSection>

            <InspectorSection
              title="Related Concepts"
              caption="Neighbor graph"
              defaultOpen={conceptCount > 0}
            >
              <div className="mt-3 flex flex-wrap gap-2">
                {latest.related_concepts.length ? (
                  latest.related_concepts.map((concept) => (
                    <span
                      key={concept}
                      className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700"
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
            </InspectorSection>

            <InspectorSection
              title="Sources"
              caption="Grounding stack"
              defaultOpen
            >
              <Sources sources={latest.sources} />
            </InspectorSection>

            {latest.structured_output ? (
              <InspectorSection
                title="Structured Output"
                caption="Developer view"
                defaultOpen
              >
                <JsonLdViewer data={latest.structured_output} />
              </InspectorSection>
            ) : null}
          </div>
        )}
      </div>

      <div className="border-t border-black/5 px-5 py-3 text-xs text-slate-500">
        {loading
          ? "Evidence cards will settle after the current assistant turn finishes streaming."
          : "Inspector pins the latest assistant answer and its grounding metadata."}
      </div>
    </aside>
  );
}
