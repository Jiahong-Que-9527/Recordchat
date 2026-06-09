import type { QueryType } from "@/lib/api";

const QUERY_TYPE_STYLES: Record<QueryType, string> = {
  concept_explanation: "border-sky-200 bg-sky-50 text-sky-800",
  relationship_question: "border-amber-200 bg-amber-50 text-amber-800",
  api_question: "border-indigo-200 bg-indigo-50 text-indigo-800",
  implementation_question: "border-emerald-200 bg-emerald-50 text-emerald-800",
  ontology_question: "border-fuchsia-200 bg-fuchsia-50 text-fuchsia-800",
  synthetic_data_generation: "border-cyan-200 bg-cyan-50 text-cyan-800",
  jsonld_generation: "border-slate-300 bg-slate-100 text-slate-800",
  general_question: "border-slate-200 bg-white text-slate-700",
};

export function QueryTypeBadge({ queryType }: { queryType: QueryType }) {
  return (
    <span
      className={`inline-flex rounded-full border px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] ${QUERY_TYPE_STYLES[queryType]}`}
    >
      {queryType.replace(/_/g, " ")}
    </span>
  );
}
