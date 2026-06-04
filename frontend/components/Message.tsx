import type { ChatResponse } from "@/lib/api";
import { JsonLdViewer } from "./JsonLdViewer";
import { Sources } from "./Sources";

export interface ChatTurn {
  role: "user" | "assistant";
  text: string;
  data?: ChatResponse;
}

export function Message({ turn }: { turn: ChatTurn }) {
  if (turn.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl bg-accent px-4 py-2 text-sm text-white">
          {turn.text}
        </div>
      </div>
    );
  }

  const data = turn.data;
  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] rounded-2xl border border-border bg-muted px-4 py-3">
        {data?.query_type ? (
          <span className="mb-2 inline-block rounded-full bg-white px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-500">
            {data.query_type.replace(/_/g, " ")}
          </span>
        ) : null}
        <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-800">
          {turn.text}
        </div>

        {data?.related_concepts?.length ? (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {data.related_concepts.map((c) => (
              <span
                key={c}
                className="rounded-md border border-border bg-white px-2 py-0.5 text-xs text-slate-600"
              >
                {c}
              </span>
            ))}
          </div>
        ) : null}

        {data?.structured_output ? (
          <JsonLdViewer data={data.structured_output} />
        ) : null}

        {data?.sources ? <Sources sources={data.sources} /> : null}
      </div>
    </div>
  );
}
