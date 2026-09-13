"use client";

import { useState } from "react";
import {
  ChevronDown,
  PanelLeftClose,
  PanelLeftOpen,
  SquarePen,
  Trash2,
} from "lucide-react";
import { RecordChatIcon } from "@/components/RecordChatIcon";
import { UserMenu } from "@/components/UserMenu";
import { EXAMPLE_QUESTIONS } from "@/lib/constants";
import { cn } from "@/lib/utils";

function CollapsibleSection({
  title,
  defaultOpen = true,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="px-0.5">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex w-full items-center justify-between rounded-md px-2 py-1 text-left text-[11px] font-medium uppercase tracking-[0.08em] text-slate-400 transition hover:text-slate-600"
      >
        <span className="truncate">{title}</span>
        <ChevronDown
          className={cn(
            "h-3.5 w-3.5 shrink-0 transition-transform duration-150",
            open ? "" : "-rotate-90"
          )}
        />
      </button>
      {open ? <div className="mt-0.5">{children}</div> : null}
    </section>
  );
}

export function Sidebar({
  onNewChat,
  onPick,
  collapsed,
  onToggleCollapsed,
  className,
}: {
  onNewChat: () => void;
  onPick: (question: string) => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
  className?: string;
}) {
  return (
    <aside
      className={cn(
        "flex h-full min-h-0 shrink-0 flex-col border-r border-slate-200/80 bg-[rgb(247_250_253/0.92)] backdrop-blur-xl",
        collapsed ? "items-center" : "",
        className
      )}
    >
      <div
        className={cn(
          "flex h-12 w-full shrink-0 items-center",
          collapsed ? "justify-center px-1.5" : "justify-between px-3"
        )}
      >
        <div
          className={cn(
            "flex min-w-0 items-center gap-2",
            collapsed ? "hidden" : ""
          )}
        >
          <RecordChatIcon
            size="sm"
            priority
            alt="RecordChat icon"
            className="shadow-none"
          />
          <span className="truncate text-[14px] font-semibold tracking-tight">
            <span className="rc-gradient-text">RecordChat</span>
          </span>
        </div>
        <button
          type="button"
          onClick={onToggleCollapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-200/60 hover:text-slate-700"
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </button>
      </div>

      <div className={cn("shrink-0 pb-2 pt-1", collapsed ? "px-1.5" : "px-2.5")}>
        <button
          type="button"
          onClick={onNewChat}
          aria-label="New chat"
          title="New chat"
          className={cn(
            "inline-flex h-9 items-center rounded-xl border border-slate-200/90 bg-white/80 text-sm font-medium text-slate-800 shadow-rc-sm transition hover:border-slate-300 hover:bg-white hover:text-slate-950",
            collapsed ? "w-9 justify-center px-0" : "w-full gap-2 px-3"
          )}
        >
          <SquarePen className="h-4 w-4 shrink-0 text-accent" />
          <span className={collapsed ? "sr-only" : ""}>New chat</span>
        </button>
        <button
          type="button"
          aria-label="Delete all"
          title="Delete all"
          className={cn(
            "mt-1 inline-flex h-8 items-center rounded-lg text-[13px] font-medium text-slate-500 transition hover:bg-slate-200/50 hover:text-slate-800",
            collapsed ? "w-9 justify-center px-0" : "w-full gap-2 px-3"
          )}
        >
          <Trash2 className="h-3.5 w-3.5 shrink-0" />
          <span className={collapsed ? "sr-only" : ""}>Clear chats</span>
        </button>
      </div>

      <div
        className={cn(
          "min-h-0 flex-1 overflow-y-auto py-1",
          collapsed ? "w-full px-1.5" : "px-2"
        )}
      >
        {collapsed ? null : (
          <div className="space-y-5 pb-3">
            <CollapsibleSection title="Try asking">
              <div className="space-y-0.5">
                {EXAMPLE_QUESTIONS.map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => onPick(question)}
                    className="block w-full rounded-lg px-2.5 py-1.5 text-left text-[13px] leading-5 text-slate-600 transition hover:bg-white/90 hover:text-slate-900"
                  >
                    <span className="line-clamp-2">{question}</span>
                  </button>
                ))}
              </div>
            </CollapsibleSection>

            <CollapsibleSection title="History" defaultOpen={false}>
              <p className="px-2.5 py-1.5 text-[12px] leading-5 text-slate-400">
                Conversations stay in this browser. Nothing is listed here yet.
              </p>
            </CollapsibleSection>
          </div>
        )}
      </div>

      <div
        className={cn(
          "shrink-0 border-t border-slate-200/70",
          collapsed ? "p-1.5" : "p-2"
        )}
      >
        <UserMenu collapsed={collapsed} />
      </div>
    </aside>
  );
}
