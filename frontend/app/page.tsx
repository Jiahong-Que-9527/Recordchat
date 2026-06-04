"use client";

import { useRef, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Message, type ChatTurn } from "@/components/Message";
import { sendChat } from "@/lib/api";

export default function Home() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  function scrollToEnd() {
    requestAnimationFrame(() =>
      endRef.current?.scrollIntoView({ behavior: "smooth" })
    );
  }

  async function ask(message: string) {
    const q = message.trim();
    if (!q || loading) return;
    setInput("");
    setTurns((t) => [...t, { role: "user", text: q }]);
    setLoading(true);
    scrollToEnd();
    try {
      const data = await sendChat(q);
      setTurns((t) => [
        ...t,
        { role: "assistant", text: data.answer, data },
      ]);
    } catch (e) {
      setTurns((t) => [
        ...t,
        {
          role: "assistant",
          text:
            "Could not reach the RecordChat backend. Is it running on " +
            (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000") +
            "? Did you run /ingest?",
        },
      ]);
    } finally {
      setLoading(false);
      scrollToEnd();
    }
  }

  return (
    <main className="flex h-screen">
      <Sidebar onPick={ask} onNewChat={() => setTurns([])} />

      <section className="flex flex-1 flex-col">
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="mx-auto flex max-w-3xl flex-col gap-4">
            {turns.length === 0 ? (
              <div className="mt-20 text-center text-slate-400">
                <p className="text-2xl font-semibold text-slate-600">
                  Ask about IATA ONE Record
                </p>
                <p className="mt-2 text-sm">
                  Concepts, the data model, JSON-LD, the API, and how logistics
                  objects relate. Pick an example on the left to start.
                </p>
              </div>
            ) : (
              turns.map((t, i) => <Message key={i} turn={t} />)
            )}
            {loading ? (
              <div className="text-sm text-slate-400">RecordChat is thinking…</div>
            ) : null}
            <div ref={endRef} />
          </div>
        </div>

        <div className="border-t border-border bg-white px-6 py-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
            className="mx-auto flex max-w-3xl gap-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about ONE Record…"
              className="flex-1 rounded-lg border border-border px-4 py-2 text-sm outline-none focus:border-accent"
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-accent px-5 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              Send
            </button>
          </form>
        </div>
      </section>
    </main>
  );
}
