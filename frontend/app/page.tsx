"use client";

import { startTransition, useEffect, useRef, useState } from "react";
import { InspectorPanel } from "@/components/InspectorPanel";
import { Sidebar } from "@/components/Sidebar";
import { Message, type ChatTurn } from "@/components/Message";
import { TypingIndicator } from "@/components/TypingIndicator";
import { streamChat, type ChatResponse } from "@/lib/api";

export default function Home() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingStatus, setStreamingStatus] = useState<string>("");
  const endRef = useRef<HTMLDivElement>(null);
  const latestAssistantData = [...turns]
    .reverse()
    .find((turn) => turn.role === "assistant" && turn.data)?.data;

  function scrollToEnd() {
    requestAnimationFrame(() =>
      endRef.current?.scrollIntoView({ behavior: "smooth" })
    );
  }

  useEffect(() => {
    scrollToEnd();
  }, [turns]);

  async function ask(message: string) {
    const q = message.trim();
    if (!q || loading) return;
    setInput("");
    const assistantIndex = turns.length + 1;
    setTurns((t) => [
      ...t,
      { role: "user", text: q },
      { role: "assistant", text: "", streaming: true },
    ]);
    setLoading(true);
    setStreamingStatus("RecordChat is streaming…");
    scrollToEnd();
    try {
      await streamChat(q, {
        onToken(text) {
          startTransition(() => {
            setTurns((current) =>
              current.map((turn, index) =>
                index === assistantIndex
                  ? { ...turn, text: `${turn.text}${text}`, streaming: true }
                  : turn
              )
            );
          });
          scrollToEnd();
        },
        onMetadata(data: ChatResponse) {
          startTransition(() => {
            setTurns((current) =>
              current.map((turn, index) =>
                index === assistantIndex
                  ? { ...turn, text: data.answer, data, streaming: false }
                  : turn
              )
            );
          });
        },
      });
    } catch (e) {
      setTurns((current) =>
        current.map((turn, index) =>
          index === assistantIndex
            ? {
                role: "assistant",
                text:
                  "Could not reach the RecordChat backend. Is it running on " +
                  (process.env.NEXT_PUBLIC_API_BASE_URL ?? "the expected backend address") +
                  "? Did you run /ingest, or configure the frontend proxy route?",
                streaming: false,
              }
            : turn
        )
      );
    } finally {
      setLoading(false);
      setStreamingStatus("");
      scrollToEnd();
    }
  }

  return (
    <main className="flex min-h-screen flex-col bg-[radial-gradient(circle_at_top_left,_rgba(13,148,136,0.12),_transparent_28%),linear-gradient(180deg,_#f7fbfb_0%,_#eef4f3_100%)] lg:flex-row">
      <Sidebar
        onPick={ask}
        onNewChat={() => {
          setTurns([]);
          setStreamingStatus("");
        }}
      />

      <section className="flex min-h-0 flex-1 flex-col">
        <div className="border-b border-black/5 bg-white/70 px-4 py-4 backdrop-blur sm:px-6">
          <div className="mx-auto flex max-w-4xl items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-teal-700">
                ONE Record Grounded Chat
              </p>
              <h2 className="text-lg font-semibold text-slate-900 sm:text-xl">
                Streaming answers, cited sources, and implementation guidance
              </h2>
            </div>
            <div className="rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-medium text-teal-800">
              {loading ? streamingStatus || "Streaming…" : "Ready"}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-5 sm:px-6 sm:py-6">
          <div className="mx-auto flex max-w-4xl flex-col gap-4">
            {turns.length === 0 ? (
              <div className="mt-8 rounded-[28px] border border-white/70 bg-white/80 px-6 py-10 text-center shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur sm:mt-20 sm:px-8 sm:py-12">
                <p className="text-2xl font-semibold text-slate-800 sm:text-3xl">
                  Ask RecordChat about IATA ONE Record
                </p>
                <p className="mt-3 text-sm leading-6 text-slate-500">
                  Stream answers from the broadened official and NE:ONE source pack.
                  Concepts, ontology relationships, JSON-LD, API behavior, and
                  implementation support all land in the same chat surface.
                </p>
              </div>
            ) : (
              turns.map((t, i) => <Message key={i} turn={t} />)
            )}
            {loading ? (
              <TypingIndicator label={streamingStatus || "Streaming…"} />
            ) : null}
            <div className="xl:hidden">
              <InspectorPanel latest={latestAssistantData} loading={loading} className="overflow-hidden rounded-[28px] border bg-white/80 shadow-[0_16px_48px_rgba(15,23,42,0.08)]" />
            </div>
            <div ref={endRef} />
          </div>
        </div>

        <div className="border-t border-black/5 bg-white/80 px-4 py-4 backdrop-blur sm:px-6">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
            className="mx-auto flex max-w-4xl flex-col gap-3 sm:flex-row"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about ONE Record concepts, ontology, or NE:ONE implementation…"
              className="flex-1 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-2xl bg-teal-700 px-5 py-3 text-sm font-medium text-white transition hover:bg-teal-800 disabled:opacity-50 sm:min-w-[132px]"
            >
              {loading ? "Streaming…" : "Send"}
            </button>
          </form>
        </div>
      </section>

      <InspectorPanel
        latest={latestAssistantData}
        loading={loading}
        className="hidden w-[360px] border-l xl:flex xl:flex-col"
      />
    </main>
  );
}
