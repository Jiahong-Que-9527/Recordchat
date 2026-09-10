"use client";

import { Braces, Workflow } from "lucide-react";
import type { SyntheticMode } from "@/lib/api";
import { cn } from "@/lib/utils";

const OPTIONS: Array<{
  value: SyntheticMode;
  label: string;
  hint: string;
  icon: typeof Braces;
}> = [
  {
    value: "local",
    label: "Local JSON-LD",
    hint: "RecordChat templates · no RecordForge",
    icon: Braces,
  },
  {
    value: "recordforge",
    label: "RecordForge",
    hint: "Workflow connector · HTTP when configured",
    icon: Workflow,
  },
];

export function GenerationModePicker({
  value,
  onChange,
  disabled,
}: {
  value: SyntheticMode;
  onChange: (value: SyntheticMode) => void;
  disabled?: boolean;
}) {
  return (
    <div
      role="group"
      aria-label="Synthetic generation mode"
      className="inline-flex h-8 items-center rounded-full border border-slate-200 bg-white/80 p-0.5 shadow-rc-sm backdrop-blur"
    >
      {OPTIONS.map((option) => {
        const selected = option.value === value;
        const Icon = option.icon;
        return (
          <button
            key={option.value}
            type="button"
            disabled={disabled}
            aria-pressed={selected}
            title={option.hint}
            onClick={() => onChange(option.value)}
            className={cn(
              "inline-flex h-7 items-center gap-1.5 rounded-full px-2.5 text-[11px] font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-ring disabled:cursor-not-allowed disabled:opacity-60",
              selected
                ? "bg-accent-weak text-accent shadow-rc-sm"
                : "text-slate-500 hover:text-slate-800"
            )}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
            <span className="hidden sm:inline">{option.label}</span>
            <span className="sm:hidden">
              {option.value === "local" ? "Local" : "Forge"}
            </span>
          </button>
        );
      })}
    </div>
  );
}
