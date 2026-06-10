"use client";

import { useCallback, useRef, useState } from "react";
import { PanelRight, PanelRightOpen, X } from "lucide-react";
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
import { ModelPicker } from "@/components/ModelPicker";
import { Sidebar } from "@/components/Sidebar";
import { Message } from "@/components/Message";
import { TypingIndicator } from "@/components/TypingIndicator";
import {
  getMessageData,
  type ChatModel,
  type RecordChatMessage,
} from "@/lib/api";

export default function Home() {
  const [input, setInput] = useState("");
  const [selectedModel, setSelectedModel] = useState<ChatModel>("deepseek-v4-fast");
  const selectedModelRef = useRef<ChatModel>(selectedModel);
  selectedModelRef.current = selectedModel;
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [desktopInspectorOpen, setDesktopInspectorOpen] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const {
    messages,
    sendMessage,
    setMessages,
    regenerate,
    stop,
    status,
    error,
  } = useChat<RecordChatMessage>({
    transport: new DefaultChatTransport<RecordChatMessage>({
      api: "/api/chat",
      body: () => ({ model: selectedModelRef.current }),
    }),
  });
  const loading = status === "submitted" || status === "streaming";
  const streamingStatus =
    status === "submitted"
      ? "Preparing retrieval…"
      : status === "streaming"
        ? "Streaming…"
        : "";

  const latestAssistantMessage = [...messages]
    .reverse()
    .find((message) => message.role === "assistant");
  const latestAssistantData = latestAssistantMessage
    ? getMessageData(latestAssistantMessage)
    : undefined;
  const lastMessageId = messages[messages.length - 1]?.id;
  const userTurnCount = messages.filter((m) => m.role === "user").length;

  function ask(message: string) {
    const q = message.trim();
    if (!q || loading) {
      return;
    }
    setInput("");
    sendMessage({ text: q });
  }

  // Stable reference so memoised <Message> components don't re-render each token.
  const handleRegenerate = useCallback(() => {
    regenerate();
  }, [regenerate]);

  return (
    <main className="h-screen overflow-hidden bg-neutral-50">
      <div
        className={`grid h-full w-full grid-cols-1 ${
          desktopInspectorOpen
            ? sidebarCollapsed
              ? "xl:grid-cols-[48px_minmax(0,1fr)_340px]"
              : "xl:grid-cols-[260px_minmax(0,1fr)_340px]"
            : sidebarCollapsed
              ? "xl:grid-cols-[48px_minmax(0,1fr)]"
              : "xl:grid-cols-[260px_minmax(0,1fr)]"
        }`}
      >
        <Sidebar
          collapsed={sidebarCollapsed}
          onPick={ask}
          onToggleCollapsed={() => setSidebarCollapsed((value) => !value)}
          onNewChat={() => {
            setMessages([]);
            setInput("");
          }}
        />

        <section className="relative flex h-full flex-col overflow-hidden bg-neutral-50 px-4 pb-4 pt-3 sm:px-6">
          {/* Floating inspector toggle — only visible when there's something to
              open (mobile drawer, or a collapsed desktop inspector). */}
          <div className="absolute right-3 top-3 z-20 flex gap-2">
            <button
              type="button"
              onClick={() => setInspectorOpen(true)}
              aria-label="Open inspector"
              title="Inspector"
              className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-neutral-200 bg-neutral-100 text-neutral-600 transition hover:bg-neutral-200 xl:hidden"
            >
              <PanelRight className="h-4 w-4" />
            </button>
            {!desktopInspectorOpen ? (
              <button
                type="button"
                onClick={() => setDesktopInspectorOpen(true)}
                aria-label="Show inspector"
                title="Show inspector"
                className="hidden h-8 items-center gap-1.5 rounded-md border border-neutral-200 bg-neutral-100 px-2.5 text-xs font-medium text-neutral-600 transition hover:bg-neutral-200 xl:inline-flex"
              >
                <PanelRightOpen className="h-4 w-4" />
                Inspector
              </button>
            ) : null}
          </div>

          <Conversation className="min-h-0 flex-1">
            <ConversationContent watch={messages} newTurnKey={userTurnCount}>
              {messages.length === 0 ? (
                <div className="flex min-h-full flex-col pb-6 pt-[30vh]">
                  <ConversationEmptyState />
                  <div className="min-h-40 flex-1" />
                  <SuggestionList onPick={ask} />
                </div>
              ) : (
                messages.map((message) => (
                  <Message
                    key={message.id}
                    message={message}
                    isLast={message.id === lastMessageId}
                    loading={loading}
                    onRegenerate={handleRegenerate}
                  />
                ))
              )}
              {loading ? (
                <TypingIndicator label={streamingStatus || "Streaming…"} />
              ) : null}
              {error ? (
                <div className="flex flex-col gap-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  <span>
                    Could not reach the RecordChat backend. Check the frontend proxy,
                    backend server, and <code className="rounded bg-rose-100 px-1">/ingest</code> state.
                  </span>
                  <button
                    type="button"
                    onClick={() => regenerate()}
                    className="self-start rounded-lg border border-rose-300 bg-white px-3 py-1 text-xs font-medium text-rose-700 transition hover:bg-rose-100"
                  >
                    Retry
                  </button>
                </div>
              ) : null}
            </ConversationContent>
          </Conversation>

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
              onSubmitShortcut={() => ask(input)}
            />
            <PromptInputToolbar>
              <ModelPicker
                value={selectedModel}
                onChange={setSelectedModel}
                disabled={loading}
              />
              <PromptInputSubmit
                isLoading={loading}
                disabled={!input.trim()}
                onStop={() => stop()}
              />
            </PromptInputToolbar>
          </PromptInput>
        </section>

        {/* Desktop inspector — collapsible to the right */}
        {desktopInspectorOpen ? (
          <InspectorPanel
            latest={latestAssistantData}
            loading={loading}
            onCollapse={() => setDesktopInspectorOpen(false)}
            className="hidden overflow-hidden border-l border-neutral-200 xl:flex xl:h-full xl:flex-col"
          />
        ) : null}
      </div>

      {/* Mobile inspector drawer */}
      {inspectorOpen ? (
        <div className="fixed inset-0 z-50 xl:hidden">
          <div
            className="absolute inset-0 bg-slate-900/40"
            onClick={() => setInspectorOpen(false)}
          />
          <div className="absolute right-0 top-0 flex h-full w-[min(380px,90vw)] flex-col bg-white shadow-rc-md animate-[recordchat-rise_220ms_ease-out]">
            <button
              type="button"
              onClick={() => setInspectorOpen(false)}
              aria-label="Close inspector"
              className="absolute right-3 top-3 z-10 inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100"
            >
              <X className="h-4 w-4" />
            </button>
            <InspectorPanel
              latest={latestAssistantData}
              loading={loading}
              className="flex h-full min-h-0 flex-col"
            />
          </div>
        </div>
      ) : null}
    </main>
  );
}
