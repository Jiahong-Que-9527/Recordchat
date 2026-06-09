"use client";

import { Sparkles } from "lucide-react";
import { EXAMPLE_QUESTIONS } from "@/lib/constants";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export function SuggestionList({
  onPick,
}: {
  onPick: (question: string) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Badge variant="secondary" className="gap-1.5">
          <Sparkles className="h-3 w-3" />
          Suggested prompts
        </Badge>
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {EXAMPLE_QUESTIONS.map((question) => (
          <Button
            key={question}
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onPick(question)}
            className="h-auto min-w-[220px] justify-start whitespace-normal px-3 py-2 text-left text-xs leading-5"
          >
            {question}
          </Button>
        ))}
      </div>
    </div>
  );
}
