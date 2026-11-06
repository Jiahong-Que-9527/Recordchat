"use client";

import { useState } from "react";
import {
  ChevronDown,
  Edit2,
  MessageSquareDashed,
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
        className="group flex w-full items-center justify-between gap-2 rounded-lg px-3 py-1.5 text-left transition-colors hover:bg-slate-200/60"
      >
        <span
          className={cn(
            "truncate",
            uppercase
              ? "text-[11px] font-semibold uppercase tracking-wider text-slate-500"
              : "text-sm font-medium text-slate-500"
          )}
        >
          {title}
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-slate-400 transition-all duration-300 group-hover:text-slate-600",
            open ? "" : "-rotate-90"
          )}
        />
      </button>
      {/* Smooth height collapse; `invisible` keeps closed content out of the
          tab order while still letting the close animation play. */}
      <div
        className={cn(
          "grid transition-all duration-300 ease-out",
          open
            ? "grid-rows-[1fr] opacity-100"
            : "grid-rows-[0fr] opacity-0 invisible"
        )}
      >
        <div className="min-h-0 overflow-hidden">
          <div className="mt-1">{children}</div>
        </div>
      </div>
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
        "rc-glass isolate relative flex h-full shrink-0 flex-col border-r border-r-slate-200/80 shadow-[6px_0_24px_-16px_rgba(15,23,42,0.16)]",
        collapsed ? "items-center" : "",
        className
      )}
    >
      {/* Decorative depth layer — azure glows echoing the ambient body wash. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background: [
            "radial-gradient(480px 280px at 0% 0%, rgba(11, 101, 254, 0.07), transparent 65%)",
            "radial-gradient(420px 300px at 100% 100%, rgba(11, 78, 253, 0.06), transparent 60%)",
            "linear-gradient(to bottom, rgba(255, 255, 255, 0.55) 0%, rgba(255, 255, 255, 0) 28%, rgba(230, 241, 253, 0.40) 100%)",
          ].join(", "),
        }}
      />

      <div
        className={cn(
          "flex w-full items-center border-b border-slate-200/70",
          collapsed
            ? "flex-col justify-center gap-1.5 px-2 pb-2.5 pt-3"
            : "h-14 justify-between px-4"
        )}
      >
        <div className="flex min-w-0 items-center gap-2.5">
          <RecordChatIcon size="sm" priority alt="RecordChat icon" />
          <span
            className={cn(
              "truncate text-[15px] font-semibold leading-none tracking-tight",
              collapsed ? "hidden" : ""
            )}
          >
            <span className="rc-gradient-text hover:animate-rc-shimmer">
              RecordChat
            </span>
          </span>
        </div>
        <button
          type="button"
          onClick={onToggleCollapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-200/70 hover:text-slate-900 active:scale-90"
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </button>
      </div>

      <div
        className={cn(
          "space-y-1 pb-4 pt-3",
          collapsed ? "px-2" : "px-3"
        )}
      >
        <button
          type="button"
          onClick={onNewChat}
          aria-label="New chat"
          title="New chat"
          className={cn(
            "rc-gradient-bg inline-flex h-9 items-center rounded-full text-sm font-medium text-white shadow-rc-glow transition duration-200 hover:brightness-110 hover:shadow-rc-lg active:scale-[0.97] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-ring focus-visible:ring-offset-2",
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
            "flex h-8 items-center rounded-lg text-sm font-medium text-slate-500 transition hover:bg-rose-50 hover:text-rose-600 active:scale-[0.98]",
            collapsed ? "w-8 justify-center px-0" : "w-full gap-2.5 px-3"
          )}
        >
          <Trash2 className="h-4 w-4 shrink-0" />
          <span className={collapsed ? "sr-only" : ""}>Delete all</span>
        </button>
      </div>

      <div
        className={cn(
          "rc-scroll-fade flex-1 overflow-y-auto py-3",
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
                    className="group relative block w-full rounded-lg px-3 py-2 text-left text-[13px] leading-6 text-slate-600 transition-all duration-200 hover:translate-x-1 hover:bg-white hover:text-slate-900 hover:shadow-rc-sm active:translate-x-0"
                  >
                    <span
                      aria-hidden
                      className="absolute left-0 top-1/2 h-0 w-[3px] -translate-y-1/2 rounded-full bg-gradient-to-b from-brand-light to-brand-deep transition-all duration-200 group-hover:h-4"
                    />
                    {question}
                  </button>
                ))}
              </div>
            </CollapsibleSection>

            <CollapsibleSection title="History" uppercase>
              <div className="rounded-xl border border-dashed border-slate-300/80 bg-white/50 px-3 py-4 text-center">
                <MessageSquareDashed
                  className="mx-auto h-5 w-5 text-slate-300"
                  aria-hidden
                />
                <p className="mt-1.5 text-xs leading-5 text-slate-400">
                  Your ONE Record conversations will appear here once you start
                  chatting.
                </p>
              </div>
            </CollapsibleSection>
          </div>
        )}
      </div>

      <div className="border-t border-slate-200/70 bg-white/40 p-2">
        <UserMenu collapsed={collapsed} />
      </div>
    </aside>
  );
}
