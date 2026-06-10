"use client";

import Image from "next/image";
import type { ChatModel } from "@/lib/api";

const MODEL_LABELS: Record<ChatModel, string> = {
  "deepseek-v4-fast": "DeepSeek V4 Fast",
  "deepseek-v4-pro": "DeepSeek V4 Pro",
};

export function ModelPicker({
  value,
  disabled,
}: {
  value: ChatModel;
  disabled?: boolean;
}) {
  return (
    <div
      aria-disabled={disabled}
      className="inline-flex h-8 items-center gap-2 rounded-full bg-neutral-100 px-3 text-xs font-semibold text-neutral-900 aria-disabled:text-neutral-400"
    >
      <Image
        src="/deepseek-mark.svg"
        alt=""
        width={16}
        height={12}
        className="h-3.5 w-4"
      />
      {MODEL_LABELS[value]}
    </div>
  );
}
