"use client";

import Image from "next/image";
import { ChevronDown } from "lucide-react";
import type { ChatModel } from "@/lib/api";

const MODEL_LABELS: Record<ChatModel, string> = {
  "deepseek-v4-flash": "DeepSeek V4 Flash",
  "deepseek-v4-pro": "DeepSeek V4 Pro",
};

export function ModelPicker({
  value,
  onChange,
  disabled,
}: {
  value: ChatModel;
  onChange: (value: ChatModel) => void;
  disabled?: boolean;
}) {
  return (
    <label
      aria-disabled={disabled}
      className="relative inline-flex h-8 items-center gap-2 rounded-full border border-neutral-200 bg-neutral-100 pl-3 pr-8 text-xs font-semibold text-neutral-900 aria-disabled:opacity-60"
    >
      <Image
        src="/deepseek-mark.svg"
        alt=""
        width={16}
        height={12}
        className="h-3.5 w-4"
      />
      <select
        value={value}
        onChange={(event) => onChange(event.target.value as ChatModel)}
        disabled={disabled}
        aria-label="Select model"
        className="h-full appearance-none bg-transparent text-xs font-semibold text-neutral-900 outline-none disabled:cursor-not-allowed"
      >
        {Object.entries(MODEL_LABELS).map(([model, label]) => (
          <option key={model} value={model}>
            {label}
          </option>
        ))}
      </select>
      <ChevronDown
        aria-hidden="true"
        className="pointer-events-none absolute right-3 top-1/2 h-3 w-3 -translate-y-1/2 text-neutral-500"
      />
    </label>
  );
}
