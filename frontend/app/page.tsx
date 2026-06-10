"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Edit2, Menu } from "lucide-react";
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
import { ModelPicker } from "@/components/ModelPicker";
import { Sidebar } from "@/components/Sidebar";
import { Message, canvasTitle } from "@/components/Message";
import { TypingIndicator } from "@/components/TypingIndicator";
import { Canvas } from "@/components/Canvas";
import { cn } from "@/lib/utils";
import { getMessageData, type ChatModel, type RecordChatMessage } from "@/lib/api";

type CanvasState = {
  messageId: string;
  title: string;
  data: Record<string, unknown>;
};

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message.trim();
  }

  return "";
}

export default function Home() {
  const [input, setInput] = useState("");
  const [selectedModel, setSelectedModel] = useState<ChatModel>("deepseek-v4-flash");
  const selectedModelRef = useRef<ChatModel>(selectedModel);
  selectedModelRef.current = selectedModel;
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [canvas, setCanvas] = useState<CanvasState | null>(null);
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

  const lastMessageId = messages[messages.length - 1]?.id;
  const userTurnCount = messages.filter((m) => m.role === "user").length;
  const errorDetail = error ? getErrorMessage(error) : "";
  // While waiting for the first token there is no assistant bubble yet, so show
  // a standalone "Thinking…" indicator. Once streaming starts the assistant
  // <Message> renders its own indicator / streamed text.
  const showConversationIndicator = status === "submitted";

  function ask(message: string) {
    const q = message.trim();
    if (!q || loading) {
      return;
    }
    setInput("");
    sendMessage({ text: q });
  }

  // Stable references so memoised <Message> components don't re-render each
  // token. `messagesRef` lets the edit handler read the latest list without
  // depending on it (which would change identity every render).
  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  const handleRegenerate = useCallback(() => {
    regenerate();
  }, [regenerate]);

  // Edit-and-resend: drop the edited turn and everything after it, then send
  // the revised question — the assistant answer is regenerated from there.
  const handleEditMessage = useCallback(
    (messageId: string, text: string) => {
      const index = messagesRef.current.findIndex((m) => m.id === messageId);
      if (index === -1) {
        return;
      }
      setMessages(messagesRef.current.slice(0, index));
      sendMessage({ text });
    },
    [sendMessage, setMessages]
  );

  // Toggle from the artifact card: open this message's output, or close it if
  // it is already the one on screen.
  const handleToggleCanvas = useCallback(
    (messageId: string, title: string, data: Record<string, unknown>) => {
      setCanvas((current) =>
        current?.messageId === messageId ? null : { messageId, title, data }
      );
    },
    []
  );

  // Auto-open the canvas when a finished answer carries structured output.
  // Tracked per message id so manually closing it doesn't re-trigger.
  const autoOpenedRef = useRef<string | null>(null);
  useEffect(() => {
    if (loading) {
      return;
    }
    const latestAssistant = [...messages]
      .reverse()
      .find((message) => message.role === "assistant");
    if (!latestAssistant || autoOpenedRef.current === latestAssistant.id) {
      return;
    }
    const output = getMessageData(latestAssistant)?.structured_output;
    if (output) {
      autoOpenedRef.current = latestAssistant.id;
      setCanvas({
        messageId: latestAssistant.id,
        title: canvasTitle(output),
        data: output,
      });
    }
  }, [messages, loading]);

  return (
    <main className="h-dvh overflow-hidden bg-neutral-50">
      <div
        className={cn(
          "grid h-full w-full grid-cols-1",
          canvas
            ? sidebarCollapsed
              ? "xl:grid-cols-[48px_minmax(0,1fr)_minmax(0,1fr)]"
              : "xl:grid-cols-[260px_minmax(0,1fr)_minmax(0,1fr)]"
            : sidebarCollapsed
              ? "xl:grid-cols-[48px_minmax(0,1fr)]"
              : "xl:grid-cols-[260px_minmax(0,1fr)]"
        )}
      >
        {/* Desktop sidebar — a static grid column from xl up. */}
        <Sidebar
          className="hidden w-full xl:flex xl:sticky xl:top-0 xl:h-screen"
          collapsed={sidebarCollapsed}
          onPick={ask}
          onToggleCollapsed={() => setSidebarCollapsed((value) => !value)}
          onNewChat={() => {
            setMessages([]);
            setInput("");
          }}
        />

        <section className="relative flex h-full flex-col overflow-hidden bg-neutral-50 px-4 pb-4 pt-3 sm:px-6">
          {/* Mobile/tablet top bar — opens the sidebar drawer. */}
          <header className="mb-2 flex items-center justify-between gap-2 xl:hidden">
            <button
              type="button"
              onClick={() => setMobileSidebarOpen(true)}
              aria-label="Open menu"
              className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-neutral-200 bg-white text-neutral-600 transition hover:bg-neutral-100"
            >
              <Menu className="h-5 w-5" />
            </button>
            <span className="text-sm font-semibold leading-none">
              <span className="text-blue-600">Record</span>
              <span className="text-amber-500">Chat</span>
            </span>
            <button
              type="button"
              onClick={() => {
                setMessages([]);
                setInput("");
              }}
              aria-label="New chat"
              className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-neutral-200 bg-white text-neutral-600 transition hover:bg-neutral-100"
            >
              <Edit2 className="h-4 w-4" />
            </button>
          </header>

          <Conversation className="min-h-0 flex-1">
            {messages.length === 0 ? (
              <div className="flex min-h-0 flex-1 flex-col overflow-hidden px-4 pb-6 pt-[30vh] sm:px-6 xl:px-8">
                <div className="mx-auto flex h-full w-full max-w-3xl flex-col">
                  <ConversationEmptyState />
                  <div className="min-h-40 flex-1" />
                  <SuggestionList onPick={ask} />
                </div>
              </div>
            ) : (
              <ConversationContent watch={messages} newTurnKey={userTurnCount}>
                {messages.map((message) => (
                  <Message
                    key={message.id}
                    message={message}
                    isLast={message.id === lastMessageId}
                    loading={loading}
                    onRegenerate={handleRegenerate}
                    onEdit={handleEditMessage}
                    onToggleCanvas={handleToggleCanvas}
                    activeCanvasId={canvas?.messageId ?? null}
                  />
                ))}
                {showConversationIndicator ? <TypingIndicator /> : null}
                {error ? (
                  <div className="flex flex-col gap-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                    <span>
                      Could not complete the RecordChat request.{" "}
                      {errorDetail ? `${errorDetail} ` : ""}Check the frontend
                      proxy, backend server, and{" "}
                      <code className="rounded bg-rose-100 px-1">/ingest</code> state.
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
            )}
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

        {/* Canvas — desktop split column */}
        {canvas ? (
          <Canvas
            title={canvas.title}
            data={canvas.data}
            onClose={() => setCanvas(null)}
            className="hidden border-l border-neutral-200 xl:flex"
          />
        ) : null}
      </div>

      {/* Sidebar — mobile/tablet slide-over drawer */}
      {mobileSidebarOpen ? (
        <div className="fixed inset-0 z-50 xl:hidden">
          <div
            className="absolute inset-0 bg-slate-900/40"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full shadow-rc-md animate-[recordchat-slide-left_220ms_ease-out]">
            <Sidebar
              className="h-full w-[min(300px,85vw)]"
              collapsed={false}
              onToggleCollapsed={() => setMobileSidebarOpen(false)}
              onPick={(question) => {
                setMobileSidebarOpen(false);
                ask(question);
              }}
              onNewChat={() => {
                setMobileSidebarOpen(false);
                setMessages([]);
                setInput("");
              }}
            />
          </div>
        </div>
      ) : null}

      {/* Canvas — mobile/tablet slide-over drawer */}
      {canvas ? (
        <div className="fixed inset-0 z-50 xl:hidden">
          <div
            className="absolute inset-0 bg-slate-900/40"
            onClick={() => setCanvas(null)}
          />
          <div className="absolute right-0 top-0 h-full w-[min(640px,95vw)] shadow-rc-md">
            <Canvas
              title={canvas.title}
              data={canvas.data}
              onClose={() => setCanvas(null)}
              className="h-full"
            />
          </div>
        </div>
      ) : null}
    </main>
  );
}
