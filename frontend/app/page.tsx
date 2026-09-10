"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Edit2, Menu } from "lucide-react";
import { Canvas, CanvasToggleButton } from "@/components/Canvas";
import { RecordChatIcon } from "@/components/RecordChatIcon";
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
import { GenerationModePicker } from "@/components/GenerationModePicker";
import { ModelPicker } from "@/components/ModelPicker";
import { Sidebar } from "@/components/Sidebar";
import { Message, canvasTitle } from "@/components/Message";
import { TypingIndicator } from "@/components/TypingIndicator";
import { cn } from "@/lib/utils";
import {
  getMessageData,
  type ChatModel,
  type RecordChatMessage,
  type SyntheticMode,
} from "@/lib/api";

type CanvasState = {
  messageId: string;
  title: string;
  data: Record<string, unknown>;
};

function findLatestStructuredOutput(
  messages: RecordChatMessage[]
): CanvasState | null {
  for (const message of [...messages].reverse()) {
    if (message.role !== "assistant") continue;
    const output = getMessageData(message)?.structured_output;
    if (output) {
      return {
        messageId: message.id,
        title: canvasTitle(output),
        data: output,
      };
    }
  }
  return null;
}

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
  // Default to local templates so synthetic prompts open the JSON-LD panel
  // without requiring RecordForge. Switch to RecordForge for the workflow path.
  const [syntheticMode, setSyntheticMode] = useState<SyntheticMode>("local");
  const syntheticModeRef = useRef<SyntheticMode>(syntheticMode);
  syntheticModeRef.current = syntheticMode;
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [canvasOpen, setCanvasOpen] = useState(false);
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
      body: () => ({
        model: selectedModelRef.current,
        synthetic_mode: syntheticModeRef.current,
      }),
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
      if (canvasOpen && canvas?.messageId === messageId) {
        setCanvasOpen(false);
        return;
      }
      setCanvas({ messageId, title, data });
      setCanvasOpen(true);
    },
    [canvas, canvasOpen]
  );

  const handleToggleCanvasPanel = useCallback(() => {
    if (canvasOpen) {
      setCanvasOpen(false);
      return;
    }
    const latest = findLatestStructuredOutput(messagesRef.current);
    if (latest) {
      setCanvas(latest);
    }
    setCanvasOpen(true);
  }, [canvasOpen]);

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
      setCanvasOpen(true);
    }
  }, [messages, loading]);

  return (
    <main className="h-dvh overflow-hidden bg-transparent">
      <div
        className={cn(
          "grid h-full w-full grid-cols-1",
          canvasOpen
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

        <section className="relative flex h-full flex-col overflow-hidden bg-transparent px-4 pb-4 pt-3 sm:px-6">
          {/* Mobile/tablet top bar — opens the sidebar drawer. */}
          <header className="mb-2 flex items-center justify-between gap-2 xl:hidden">
            <button
              type="button"
              onClick={() => setMobileSidebarOpen(true)}
              aria-label="Open menu"
              className="rc-glass inline-flex h-9 w-9 items-center justify-center rounded-xl text-slate-600 shadow-rc-sm transition hover:text-slate-900"
            >
              <Menu className="h-4 w-4" />
            </button>
            <span className="flex items-center gap-2 text-sm font-semibold leading-none tracking-tight">
              <RecordChatIcon size="sm" alt="RecordChat" />
              <span className="rc-gradient-text">RecordChat</span>
            </span>
            <div className="flex items-center gap-2">
              <CanvasToggleButton
                open={canvasOpen}
                onClick={handleToggleCanvasPanel}
                className="h-9 w-9"
              />
              <button
                type="button"
                onClick={() => {
                  setMessages([]);
                  setInput("");
                }}
                aria-label="New chat"
                className="rc-glass inline-flex h-9 w-9 items-center justify-center rounded-xl text-slate-600 shadow-rc-sm transition hover:text-slate-900"
              >
                <Edit2 className="h-4 w-4" />
              </button>
            </div>
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
                    activeCanvasId={
                      canvasOpen ? (canvas?.messageId ?? null) : null
                    }
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
              <div className="flex flex-wrap items-center gap-2">
                <ModelPicker
                  value={selectedModel}
                  onChange={setSelectedModel}
                  disabled={loading}
                />
                <GenerationModePicker
                  value={syntheticMode}
                  onChange={setSyntheticMode}
                  disabled={loading}
                />
                <CanvasToggleButton
                  open={canvasOpen}
                  onClick={handleToggleCanvasPanel}
                />
              </div>
              <PromptInputSubmit
                isLoading={loading}
                disabled={!input.trim()}
                onStop={() => stop()}
              />
            </PromptInputToolbar>
          </PromptInput>

          {/* Comfort hints — keyboard shortcuts + grounding note. */}
          <p className="mx-auto mt-2.5 flex max-w-[864px] items-center justify-center gap-3 text-center text-[11px] leading-none text-slate-400">
            <span className="inline-flex items-center gap-1.5">
              <kbd className="rc-kbd">Enter</kbd>
              to send
            </span>
            <span className="inline-flex items-center gap-1.5">
              <kbd className="rc-kbd">Shift</kbd>
              +
              <kbd className="rc-kbd">Enter</kbd>
              for newline
            </span>
            <span aria-hidden="true" className="h-1 w-1 rounded-full bg-slate-300" />
            <span>Answers are grounded and cited</span>
          </p>
        </section>

        {/* Canvas — desktop split column */}
        {canvasOpen ? (
          <Canvas
            title={canvas?.title ?? "Structured Output"}
            data={canvas?.data ?? null}
            onClose={() => setCanvasOpen(false)}
            onAskExample={() => ask("Generate a JSON-LD example for a Piece.")}
            className="hidden xl:flex"
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
      {canvasOpen ? (
        <div className="fixed inset-0 z-50 xl:hidden">
          <div
            className="absolute inset-0 bg-slate-900/40"
            onClick={() => setCanvasOpen(false)}
          />
          <div className="absolute right-0 top-0 h-full w-[min(640px,95vw)] shadow-rc-md">
            <Canvas
              title={canvas?.title ?? "Structured Output"}
              data={canvas?.data ?? null}
              onClose={() => setCanvasOpen(false)}
              onAskExample={() => {
                setCanvasOpen(false);
                ask("Generate a JSON-LD example for a Piece.");
              }}
              className="h-full"
            />
          </div>
        </div>
      ) : null}
    </main>
  );
}
