"use client";

import { useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
} from "@/components/ai-elements/conversation";
import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
} from "@/components/ai-elements/prompt-input";
import { SuggestionList } from "@/components/ai-elements/suggestion-list";
import { InspectorPanel } from "@/components/InspectorPanel";
import { Sidebar } from "@/components/Sidebar";
import { Message } from "@/components/Message";
import { TypingIndicator } from "@/components/TypingIndicator";
import { Badge } from "@/components/ui/badge";
import { getMessageData, type RecordChatMessage } from "@/lib/api";

export default function Home() {
  const [input, setInput] = useState("");
  const {
    messages,
    sendMessage,
    setMessages,
    status,
    error,
  } = useChat<RecordChatMessage>({
    transport: new DefaultChatTransport<RecordChatMessage>({
      api: "/api/chat",
    }),
  });
  const loading = status === "submitted" || status === "streaming";
  const streamingStatus =
    status === "submitted"
      ? "RecordChat is preparing retrieval…"
      : status === "streaming"
        ? "RecordChat is streaming…"
        : "";
  const latestAssistantMessage = [...messages]
    .reverse()
    .find((message) => message.role === "assistant");
  const latestAssistantData = latestAssistantMessage
    ? getMessageData(latestAssistantMessage)
    : undefined;

  function ask(message: string) {
    const q = message.trim();
    if (!q || loading) {
      return;
    }

    setInput("");
    sendMessage({ text: q });
  }

  return (
    <main className="flex min-h-screen flex-col bg-[radial-gradient(circle_at_top_left,_rgba(13,148,136,0.12),_transparent_28%),linear-gradient(180deg,_#f7fbfb_0%,_#eef4f3_100%)] lg:flex-row">
      <Sidebar
        onPick={ask}
        onNewChat={() => {
          setMessages([]);
          setInput("");
        }}
      />

      <section className="flex min-h-0 flex-1 flex-col gap-4 px-3 py-3 sm:px-4 sm:py-4">
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
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="hidden sm:inline-flex">
                useChat + AI SDK
              </Badge>
              <div className="rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-medium text-teal-800">
                {loading ? streamingStatus || "Streaming…" : "Ready"}
              </div>
            </div>
          </div>
        </div>

        <Conversation className="min-h-0">
          <ConversationContent watch={messages}>
            {messages.length === 0 ? (
              <>
                <ConversationEmptyState />
                <SuggestionList onPick={ask} />
              </>
            ) : (
              messages.map((message) => (
                <Message key={message.id} message={message} />
              ))
            )}
            {loading ? (
              <TypingIndicator label={streamingStatus || "Streaming…"} />
            ) : null}
            {error ? (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                Could not reach the RecordChat backend. Check the frontend proxy,
                backend server, and `/ingest` state. Details: {error.message}
              </div>
            ) : null}
            <div className="xl:hidden">
              <InspectorPanel latest={latestAssistantData} loading={loading} className="overflow-hidden rounded-[28px] border bg-white/80 shadow-[0_16px_48px_rgba(15,23,42,0.08)]" />
            </div>
          </ConversationContent>
        </Conversation>

        <div className="bg-transparent px-1 pb-1">
          <PromptInput
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
          >
            <PromptInputTextarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about ONE Record concepts, ontology, or NE:ONE implementation…"
            />
            <PromptInputToolbar>
              <div className="text-xs text-slate-500">
                Grounded on official ONE Record, ontology, and NE:ONE sources.
              </div>
              <PromptInputSubmit isLoading={loading} disabled={!input.trim()} />
            </PromptInputToolbar>
          </PromptInput>
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
