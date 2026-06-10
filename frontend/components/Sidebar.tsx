"use client";

import { Edit2, Trash2, ChevronDown } from "lucide-react";
import Image from "next/image";

export function Sidebar({
  onNewChat,
}: {
  onNewChat: () => void;
}) {
  return (
    <aside className="flex h-full w-full shrink-0 flex-col border-r border-neutral-200 bg-neutral-50 xl:sticky xl:top-0 xl:h-screen">
      <div className="flex h-12 items-center justify-between px-4">
        <div className="flex min-w-0 items-center gap-2">
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
          onClick={onNewChat}
          aria-label="New chat"
          className="inline-flex h-8 w-8 items-center justify-center rounded-md text-neutral-500 transition hover:bg-neutral-200 hover:text-neutral-900"
        >
          <Edit2 className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-1 px-2 pb-5 pt-1">
        <button
          type="button"
          onClick={onNewChat}
          className="flex h-8 w-full items-center gap-2.5 rounded-full border border-neutral-300 bg-neutral-50 px-3 text-sm font-medium text-neutral-950 transition hover:bg-white"
        >
          <Edit2 className="h-4 w-4 shrink-0 text-neutral-700" />
          New chat
        </button>
        <button
          type="button"
          className="flex h-8 w-full items-center gap-2.5 rounded-md px-3 text-sm font-medium text-neutral-950 transition hover:bg-neutral-200"
        >
          <Trash2 className="h-4 w-4 shrink-0 text-neutral-700" />
          Delete all
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3">
        <p className="mb-3 text-[11px] font-medium uppercase tracking-wider text-neutral-500">
          History
        </p>
        <p className="max-w-[190px] text-sm leading-5 text-neutral-500">
          Your ONE Record conversations will appear here once you start chatting.
        </p>
      </div>

      <div className="border-t border-neutral-200 p-2">
        <button
          type="button"
          className="flex h-10 w-full items-center gap-2.5 rounded-md px-3 text-sm text-neutral-950 transition hover:bg-neutral-200"
        >
          <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#363500] text-[10px] font-semibold text-white">
            G
          </div>
          <span className="flex-1 text-left text-sm font-medium">Guest</span>
          <ChevronDown className="h-4 w-4 text-neutral-400" />
        </button>
      </div>
    </aside>
  );
}
