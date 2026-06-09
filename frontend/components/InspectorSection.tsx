"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export function InspectorSection({
  title,
  caption,
  defaultOpen = true,
  children,
}: {
  title: string;
  caption?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section className="rounded-[28px] border border-slate-200 bg-white px-4 py-4 shadow-sm transition duration-200 hover:shadow-[0_12px_32px_rgba(15,23,42,0.06)]">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between gap-3 text-left"
      >
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
            {title}
          </p>
          {caption ? (
            <p className="mt-1 text-[11px] uppercase tracking-[0.18em] text-slate-400">
              {caption}
            </p>
          ) : null}
        </div>
        <span
          className={cn(
            "inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-slate-500 transition",
            open && "bg-slate-900 text-white"
          )}
        >
          <ChevronDown
            className={cn("h-4 w-4 transition-transform", open && "rotate-180")}
          />
        </span>
      </button>

      <div
        className={cn(
          "grid transition-[grid-template-rows,opacity,margin] duration-300 ease-out",
          open ? "mt-4 grid-rows-[1fr] opacity-100" : "mt-0 grid-rows-[0fr] opacity-0"
        )}
      >
        <div className="overflow-hidden">{children}</div>
      </div>
    </section>
  );
}
