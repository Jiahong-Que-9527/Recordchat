import type { QueryType } from "@/lib/api";

// Two tones only: "generative" intents get the accent tint, everything else
// stays neutral. Keeps the surface calm instead of an 8-colour rainbow.
const GENERATIVE: ReadonlySet<QueryType> = new Set([
  "jsonld_generation",
  "synthetic_data_generation",
]);

export function QueryTypeBadge({ queryType }: { queryType: QueryType }) {
  const generative = GENERATIVE.has(queryType);
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${
        generative
          ? "border-accent-ring bg-accent-weak text-accent"
          : "border-slate-200 bg-slate-50 text-slate-600"
      }`}
    >
      {queryType.replace(/_/g, " ")}
    </span>
  );
}
