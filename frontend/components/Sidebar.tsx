"use client";

import { useState } from "react";
import {
  ChevronDown,
  Edit2,
  PanelLeftClose,
  PanelLeftOpen,
  Trash2,
} from "lucide-react";
import { RecordChatIcon } from "@/components/RecordChatIcon";
import { UserMenu } from "@/components/UserMenu";
import { EXAMPLE_QUESTIONS } from "@/lib/constants";
import { cn } from "@/lib/utils";

function CollapsibleSection({
  title,
  uppercase = false,
  defaultOpen = true,
  children,
}: {
  title: string;
  uppercase?: boolean;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className={cn(
          "flex w-full items-center justify-between gap-2 rounded-lg px-3 py-1.5 text-left transition hover:bg-slate-200/70",
          uppercase
            ? "text-[11px] font-semibold uppercase tracking-wider text-slate-500"
            : "text-sm font-medium text-slate-500"
        )}
      >
        <span className="truncate">{title}</span>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-slate-400 transition-transform",
            open ? "" : "-rotate-90"
          )}
        />
      </button>
      {open ? <div className="mt-1">{children}</div> : null}
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
        "rc-glass flex h-full shrink-0 flex-col border-r border-white/70",
        collapsed ? "items-center" : "",
        className
      )}
    >
      <div
        className={cn(
          "flex h-14 w-full items-center border-b border-slate-200/70",
          collapsed ? "justify-center px-2" : "justify-between px-4"
        )}
      >
        <div
          className={cn(
            "flex min-w-0 items-center gap-2.5",
            collapsed ? "hidden" : ""
          )}
        >
          <RecordChatIcon size="sm" priority alt="RecordChat icon" />
          <span className="truncate text-[15px] font-semibold leading-none tracking-tight">
            <span className="rc-gradient-text">RecordChat</span>
          </span>
        </div>
        <button
          type="button"
          onClick={onToggleCollapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-200/70 hover:text-slate-900"
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </button>
      </div>

      <div className={cn("space-y-1 pb-4 pt-3", collapsed ? "px-2" : "px-3")}>
        <button
          type="button"
          onClick={onNewChat}
          aria-label="New chat"
          title="New chat"
          className={cn(
            "rc-gradient-bg inline-flex h-9 items-center rounded-full text-sm font-medium text-white shadow-rc-glow transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-ring focus-visible:ring-offset-2",
            collapsed ? "w-9 justify-center px-0" : "w-full gap-2 px-4"
          )}
        >
          <Edit2 className="h-4 w-4 shrink-0" />
          <span className={collapsed ? "sr-only" : ""}>New chat</span>
        </button>
        <button
          type="button"
          aria-label="Delete all"
          title="Delete all"
          className={cn(
            "flex h-8 items-center rounded-lg text-sm font-medium text-slate-600 transition hover:bg-slate-200/70 hover:text-slate-900",
            collapsed ? "w-8 justify-center px-0" : "w-full gap-2.5 px-3"
          )}
        >
          <Trash2 className="h-4 w-4 shrink-0" />
          <span className={collapsed ? "sr-only" : ""}>Delete all</span>
        </button>
      </div>

      <div
        className={cn(
          "flex-1 overflow-y-auto py-3",
          collapsed ? "w-full px-2" : "px-3"
        )}
      >
        {collapsed ? null : (
          <div className="space-y-6">
            <CollapsibleSection title="Try asking">
              <div className="space-y-0.5">
                {EXAMPLE_QUESTIONS.map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => onPick(question)}
                    className="block w-full rounded-lg px-3 py-2 text-left text-[13px] leading-6 text-slate-600 transition hover:bg-white hover:text-slate-900 hover:shadow-rc-sm"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </CollapsibleSection>

            <CollapsibleSection title="History" uppercase>
              <p className="max-w-[190px] rounded-lg border border-dashed border-slate-300 bg-slate-100/60 px-3 py-3 text-xs leading-5 text-slate-500">
                Your ONE Record conversations will appear here once you start
                chatting.
              </p>
            </CollapsibleSection>
          </div>
        )}
      </div>

      <div className="border-t border-slate-200/70 p-2">
        <UserMenu collapsed={collapsed} />
      </div>
    </aside>
  );
}
