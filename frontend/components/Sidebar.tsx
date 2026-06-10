"use client";

import { useState } from "react";
import {
  ChevronDown,
  Edit2,
  PanelLeftClose,
  PanelLeftOpen,
  Trash2,
} from "lucide-react";
import Image from "next/image";
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
          "flex w-full items-center justify-between gap-2 rounded-md px-3 py-1.5 text-left transition hover:bg-neutral-200/60",
          uppercase
            ? "text-[11px] font-medium uppercase tracking-wider text-neutral-500"
            : "text-sm font-medium text-neutral-500"
        )}
      >
        <span className="truncate">{title}</span>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 transition-transform",
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
        "flex h-full shrink-0 flex-col border-r border-neutral-200 bg-neutral-50",
        collapsed ? "items-center" : "",
        className
      )}
    >
      <div
        className={cn(
          "flex h-12 w-full items-center",
          collapsed ? "justify-center px-2" : "justify-between px-4"
        )}
      >
        <div
          className={cn(
            "flex min-w-0 items-center gap-2",
            collapsed ? "hidden" : ""
          )}
        >
          <Image
            src="/recordchat-mark.svg"
            alt=""
            width={24}
            height={24}
            className="h-6 w-6 shrink-0"
            priority
          />
          <span className="truncate text-sm font-semibold leading-none tracking-normal">
            <span className="text-blue-600">Record</span>
            <span className="text-amber-500">Chat</span>
          </span>
        </div>
        <button
          type="button"
          onClick={onToggleCollapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="inline-flex h-8 w-8 items-center justify-center rounded-md text-neutral-500 transition hover:bg-neutral-200 hover:text-neutral-900"
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </button>
      </div>

      <div className={cn("space-y-1 pb-5 pt-1", collapsed ? "px-2" : "px-2")}>
        <button
          type="button"
          onClick={onNewChat}
          aria-label="New chat"
          title="New chat"
          className={cn(
            "flex h-8 items-center rounded-full border border-neutral-300 bg-neutral-50 text-sm font-medium text-neutral-950 transition hover:bg-white",
            collapsed ? "w-8 justify-center px-0" : "w-full gap-2.5 px-3"
          )}
        >
          <Edit2 className="h-4 w-4 shrink-0 text-neutral-700" />
          <span className={collapsed ? "sr-only" : ""}>New chat</span>
        </button>
        <button
          type="button"
          aria-label="Delete all"
          title="Delete all"
          className={cn(
            "flex h-8 items-center rounded-md text-sm font-medium text-neutral-950 transition hover:bg-neutral-200",
            collapsed ? "w-8 justify-center px-0" : "w-full gap-2.5 px-3"
          )}
        >
          <Trash2 className="h-4 w-4 shrink-0 text-neutral-700" />
          <span className={collapsed ? "sr-only" : ""}>Delete all</span>
        </button>
      </div>

      <div
        className={cn(
          "flex-1 overflow-y-auto py-3",
          collapsed ? "w-full px-2" : "px-4"
        )}
      >
        {collapsed ? null : (
          <div className="space-y-6">
            <CollapsibleSection title="Try asking">
              <div className="space-y-1">
                {EXAMPLE_QUESTIONS.map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => onPick(question)}
                    className="block w-full rounded-md px-3 py-2 text-left text-sm leading-6 text-slate-600 transition hover:bg-neutral-200 hover:text-neutral-950"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </CollapsibleSection>

            <CollapsibleSection title="History" uppercase>
              <p className="max-w-[190px] px-3 text-sm leading-5 text-neutral-500">
                Your ONE Record conversations will appear here once you start chatting.
              </p>
            </CollapsibleSection>
          </div>
        )}
      </div>

      <div className="border-t border-neutral-200 p-2">
        <button
          type="button"
          className={cn(
            "flex h-10 w-full items-center rounded-md text-sm text-neutral-950 transition hover:bg-neutral-200",
            collapsed ? "justify-center px-0" : "gap-2.5 px-3"
          )}
        >
          <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#363500] text-[10px] font-semibold text-white">
            G
          </div>
          {collapsed ? null : (
            <>
              <span className="flex-1 text-left text-sm font-medium">Guest</span>
              <ChevronDown className="h-4 w-4 text-neutral-400" />
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
