import type { ChatResponse } from "@/lib/api";
import { JsonLdViewer } from "./JsonLdViewer";
import { QueryTypeBadge } from "./QueryTypeBadge";
import { Sources } from "./Sources";

export interface ChatTurn {
  role: "user" | "assistant";
  text: string;
  data?: ChatResponse;
  streaming?: boolean;
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
      <div className="max-w-[85%] rounded-[28px] border border-white/70 bg-white/85 px-5 py-4 shadow-[0_18px_48px_rgba(15,23,42,0.08)] backdrop-blur">
        {data?.query_type ? (
          <div className="mb-3">
            <QueryTypeBadge queryType={data.query_type} />
          </div>
        ) : null}
        <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-800">
          {turn.text}
          {turn.streaming ? <span className="ml-1 inline-block h-4 w-2 animate-pulse rounded-sm bg-teal-600 align-middle" /> : null}
        </div>

        {data?.related_concepts?.length ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {data.related_concepts.map((c) => (
              <span
                key={c}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-700"
              >
                {c}
              </span>
            ))}
          </div>
        ) : null}

        <div className="mt-4 xl:hidden">
          {data?.structured_output ? <JsonLdViewer data={data.structured_output} /> : null}
          {data?.sources ? <Sources sources={data.sources} /> : null}
        </div>
      </div>
    </div>
  );
}
