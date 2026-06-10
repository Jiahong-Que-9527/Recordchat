"use client";

import { Edit2, Trash2, ChevronDown } from "lucide-react";
import Image from "next/image";

export function Sidebar({
  onNewChat,
}: {
  onNewChat: () => void;
}) {
  return (
    <aside className="flex h-full w-full shrink-0 flex-col bg-slate-100 xl:sticky xl:top-0 xl:h-screen">
      <div className="flex h-14 items-center justify-between px-5">
        <div className="flex min-w-0 items-center gap-2">
          <Image
            src="/recordchat-mark.svg"
            alt=""
            width={28}
            height={28}
            className="h-7 w-7 shrink-0"
            priority
          />
          <span className="truncate text-[15px] font-semibold leading-none tracking-normal">
            <span className="text-blue-600">Record</span>
            <span className="text-amber-500">Chat</span>
          </span>
        </div>
        <button
          type="button"
          onClick={onNewChat}
          aria-label="New chat"
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-200"
        >
          <Edit2 className="h-4 w-4" />
        </button>
      </div>

      {/* Actions */}
      <div className="px-2 py-1 space-y-0.5">
        <button
          type="button"
          onClick={onNewChat}
          className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-slate-700 transition hover:bg-slate-200"
        >
          <Edit2 className="h-4 w-4 shrink-0 text-slate-500" />
          New chat
        </button>
        <button
          type="button"
          className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-slate-700 transition hover:bg-slate-200"
        >
          <Trash2 className="h-4 w-4 shrink-0 text-slate-500" />
          Delete all
        </button>
      </div>

      {/* History */}
      <div className="flex-1 overflow-y-auto px-2 py-3">
        <p className="mb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          History
        </p>
      </div>

      {/* User section */}
      <div className="border-t border-slate-200 p-2">
        <button
          type="button"
          className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-slate-700 transition hover:bg-slate-200"
        >
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-400 text-xs font-semibold text-white">
            G
          </div>
          <span className="flex-1 text-left text-sm">Guest</span>
          <ChevronDown className="h-4 w-4 text-slate-400" />
        </button>
      </div>
    </aside>
  );
}
