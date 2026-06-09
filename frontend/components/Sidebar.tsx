"use client";

import { DatabaseZap, Layers3, Plus } from "lucide-react";
import Image from "next/image";
import { EXAMPLE_QUESTIONS, ONE_RECORD_CONCEPTS } from "@/lib/constants";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function Sidebar({
  onPick,
  onNewChat,
}: {
  onPick: (q: string) => void;
  onNewChat: () => void;
}) {
  return (
    <aside className="flex w-full shrink-0 flex-col gap-5 border-b border-border bg-slate-50/90 p-4 backdrop-blur lg:h-full lg:w-80 lg:border-b-0 lg:border-r">
      <div className="flex items-center gap-3">
        <Image
          src="/recordchat-logo.png"
          alt="RecordChat"
          width={40}
          height={40}
          className="h-10 w-10 shrink-0 rounded-lg object-contain"
          priority
        />
        <div className="min-w-0">
          <h1 className="text-lg font-bold text-slate-900">RecordChat</h1>
          <p className="text-xs text-slate-500">IATA ONE Record assistant</p>
        </div>
      </div>

      <Card className="rounded-[24px] bg-white/90">
        <CardContent className="space-y-4 p-4">
          <div className="flex items-center justify-between gap-3">
            <Badge variant="secondary" className="gap-1.5">
              <DatabaseZap className="h-3 w-3" />
              Grounded RAG
            </Badge>
            <Badge variant="outline">v0.2.3</Badge>
          </div>
          <p className="text-sm leading-6 text-slate-600">
            Template-style chat shell on top of the ONE Record ontology, official
            specification pack, and NE:ONE implementation sources.
          </p>
          <Button onClick={onNewChat} variant="secondary" className="w-full gap-2">
            <Plus className="h-4 w-4" />
            New chat
          </Button>
        </CardContent>
      </Card>

      <div className="lg:block">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Example Questions
        </p>
        <div className="flex gap-1.5 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible">
          {EXAMPLE_QUESTIONS.map((q) => (
            <Button
              key={q}
              onClick={() => onPick(q)}
              variant="ghost"
              size="sm"
              className="h-auto min-w-[220px] justify-start rounded-2xl px-3 py-2 text-left text-xs leading-5 text-slate-600 lg:min-w-0"
            >
              {q}
            </Button>
          ))}
        </div>
      </div>

      <div>
        <div className="mb-2 flex items-center gap-2">
          <Layers3 className="h-3.5 w-3.5 text-slate-400" />
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            ONE Record Concepts
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {ONE_RECORD_CONCEPTS.map((c) => (
            <Button
              key={c}
              onClick={() => onPick(`What is ${c} in ONE Record?`)}
              variant="outline"
              size="sm"
              className="h-auto rounded-full px-3 py-1 text-xs"
            >
              {c}
            </Button>
          ))}
        </div>
      </div>

      <Button
        onClick={() => onPick("Generate a JSON-LD example for a Piece.")}
        variant="ghost"
        className="justify-start rounded-2xl px-3 py-2 text-left text-xs text-accent lg:mt-auto"
      >
        ⚙ JSON-LD Generator
      </Button>
    </aside>
  );
}
