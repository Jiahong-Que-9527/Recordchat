import type { ChatResponse } from "@/lib/api";
import { JsonLdViewer } from "./JsonLdViewer";
import { MarkdownAnswer } from "./MarkdownAnswer";
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
        <div className="max-w-[92%] rounded-[24px] bg-gradient-to-br from-teal-700 to-cyan-700 px-4 py-3 text-sm text-white shadow-[0_18px_40px_rgba(8,145,178,0.18)] sm:max-w-[80%]">
          {turn.text}
        </div>
      </div>
    );
  }

  const data = turn.data;
  return (
    <div className="flex justify-start">
      <div className="max-w-[96%] rounded-[28px] border border-white/70 bg-white/90 px-4 py-4 shadow-[0_18px_48px_rgba(15,23,42,0.08)] backdrop-blur sm:max-w-[88%] sm:px-5">
        {data?.query_type ? (
          <div className="mb-3">
            <QueryTypeBadge queryType={data.query_type} />
          </div>
        ) : null}
        <MarkdownAnswer text={turn.text} />
        {turn.streaming ? (
          <span className="mt-3 inline-block h-4 w-2 animate-pulse rounded-sm bg-teal-600 align-middle" />
        ) : null}

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
