import { getMessageData, getMessageText, type RecordChatMessage } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { JsonLdViewer } from "./JsonLdViewer";
import { MarkdownAnswer } from "./MarkdownAnswer";
import { QueryTypeBadge } from "./QueryTypeBadge";
import { Sources } from "./Sources";

export function Message({ message }: { message: RecordChatMessage }) {
  const text = getMessageText(message);
  const data = getMessageData(message);
  const streaming = message.parts.some(
    (part) => part.type === "text" && part.state === "streaming"
  );

  if (message.role === "user") {
    return (
      <div className="flex justify-end animate-[recordchat-rise_260ms_ease-out]">
        <div className="max-w-[92%] rounded-[28px] bg-[linear-gradient(135deg,_#0f766e_0%,_#0891b2_52%,_#0f172a_100%)] px-4 py-3 text-sm text-white shadow-[0_22px_46px_rgba(8,145,178,0.20)] sm:max-w-[80%]">
          <div className="mb-2 flex items-center justify-between gap-3">
            <span className="text-[10px] font-semibold uppercase tracking-[0.22em] text-white/70">
              You
            </span>
            <span className="text-[10px] text-white/60">Prompt</span>
          </div>
          {text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start animate-[recordchat-rise_260ms_ease-out]">
      <div className="max-w-[96%] rounded-[30px] border border-white/80 bg-white/92 px-4 py-4 shadow-[0_22px_54px_rgba(15,23,42,0.08)] ring-1 ring-white/70 backdrop-blur sm:max-w-[88%] sm:px-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-slate-950 text-[11px] font-semibold uppercase tracking-[0.18em] text-white shadow-sm">
              RC
            </span>
            <div>
              <p className="text-sm font-semibold text-slate-900">RecordChat</p>
              <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">
                Grounded assistant response
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {data?.query_type ? <QueryTypeBadge queryType={data.query_type} /> : null}
            <Badge variant="outline" className="border-slate-200 bg-white text-slate-600">
              {streaming ? "Streaming" : "Complete"}
            </Badge>
            {data?.sources?.length ? (
              <Badge variant="outline" className="border-slate-200 bg-white text-slate-600">
                {data.sources.length} source{data.sources.length > 1 ? "s" : ""}
              </Badge>
            ) : null}
          </div>
        </div>
        <MarkdownAnswer text={text} />
        {streaming ? (
          <div className="mt-4 flex items-center gap-3 rounded-2xl border border-teal-100 bg-teal-50/70 px-3 py-2 text-xs text-teal-800">
            <span className="inline-block h-4 w-2 animate-pulse rounded-sm bg-teal-600 align-middle" />
            <span>Composing the answer and evidence trail…</span>
          </div>
        ) : null}

        {data?.related_concepts?.length ? (
          <div className="mt-5 rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-3">
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                Related Concepts
              </p>
              <span className="text-[10px] uppercase tracking-[0.18em] text-slate-400">
                Schema adjacency
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
            {data.related_concepts.map((c) => (
              <span
                key={c}
                className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700 shadow-sm"
              >
                {c}
              </span>
            ))}
          </div>
          </div>
        ) : null}

        <div className="mt-5 xl:hidden">
          {data?.structured_output ? <JsonLdViewer data={data.structured_output} /> : null}
          {data?.sources ? <Sources sources={data.sources} /> : null}
        </div>
      </div>
    </div>
  );
}
