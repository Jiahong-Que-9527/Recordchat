import { PanelRightClose } from "lucide-react";
import type { ChatResponse } from "@/lib/api";
import { InspectorSection } from "./InspectorSection";
import { QueryTypeBadge } from "./QueryTypeBadge";
import { Sources } from "./Sources";

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-center shadow-rc-sm">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export function InspectorPanel({
  latest,
  loading,
  className = "",
  onCollapse,
}: {
  latest?: ChatResponse;
  loading: boolean;
  className?: string;
  onCollapse?: () => void;
}) {
  const sourceCount = latest?.sources.length ?? 0;
  const conceptCount = latest?.related_concepts.length ?? 0;
  const hasStructuredOutput = Boolean(latest?.structured_output);

  return (
    <aside className={`w-full shrink-0 bg-white xl:sticky xl:top-4 xl:h-[calc(100vh-2rem)] ${className}`}>
      <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
        <div className="flex items-center gap-2">
          {onCollapse ? (
            <button
              type="button"
              onClick={onCollapse}
              aria-label="Collapse inspector"
              title="Collapse inspector"
              className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
            >
              <PanelRightClose className="h-4 w-4" />
            </button>
          ) : null}
          <h3 className="text-sm font-semibold text-slate-800">Inspector</h3>
        </div>
        <span className="text-xs text-slate-500">
          {loading ? "Updating…" : latest ? "Latest answer" : "Idle"}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5">
        {!latest ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm leading-6 text-slate-500">
            Ask a question to pin grounded metadata here — query type, source
            citations, related concepts, and JSON-LD output.
          </div>
        ) : (
          <div className="space-y-4">
            <section className="grid grid-cols-3 gap-2">
              <Stat label="Sources" value={sourceCount} />
              <Stat label="Concepts" value={conceptCount} />
              <Stat label="JSON-LD" value={<span className="text-sm">{hasStructuredOutput ? "Yes" : "—"}</span>} />
            </section>

            <InspectorSection title="Query type" defaultOpen>
              <QueryTypeBadge queryType={latest.query_type} />
            </InspectorSection>

            <InspectorSection
              title="Related concepts"
              defaultOpen={conceptCount > 0}
            >
              <div className="flex flex-wrap gap-2">
                {latest.related_concepts.length ? (
                  latest.related_concepts.map((concept) => (
                    <span
                      key={concept}
                      className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700"
                    >
                      {concept}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-slate-500">
                    No related concepts for the latest answer.
                  </span>
                )}
              </div>
            </InspectorSection>

            <InspectorSection title="Sources" caption={`${sourceCount} cited`} defaultOpen>
              <Sources sources={latest.sources} />
            </InspectorSection>
          </div>
        )}
      </div>
    </aside>
  );
}
