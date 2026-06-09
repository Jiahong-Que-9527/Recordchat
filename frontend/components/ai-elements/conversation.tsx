"use client";

import { useEffect, useRef } from "react";
import { MessageSquareText } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function Conversation({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "flex min-h-0 flex-1 flex-col rounded-[34px] border border-white/80 bg-[linear-gradient(180deg,_rgba(255,255,255,0.70)_0%,_rgba(247,251,250,0.86)_100%)] shadow-[0_18px_52px_rgba(15,23,42,0.08)] ring-1 ring-white/60 backdrop-blur",
        className
      )}
    >
      {children}
    </section>
  );
}

export function ConversationContent({
  children,
  watch,
  className,
}: {
  children: React.ReactNode;
  watch?: unknown;
  className?: string;
}) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    requestAnimationFrame(() =>
      endRef.current?.scrollIntoView({ behavior: "smooth" })
    );
  }, [watch]);

  return (
    <div className={cn("flex-1 overflow-y-auto px-4 py-5 sm:px-6 sm:py-6", className)}>
      <div className="mx-auto flex max-w-4xl flex-col gap-4">
        {children}
        <div ref={endRef} />
      </div>
    </div>
  );
}

export function ConversationEmptyState() {
  return (
    <Card className="mt-8 bg-[linear-gradient(180deg,_rgba(255,255,255,0.92)_0%,_rgba(247,251,250,0.88)_100%)] animate-[recordchat-rise_320ms_ease-out] sm:mt-20">
      <CardHeader className="items-center text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-[linear-gradient(135deg,_rgba(20,184,166,0.14)_0%,_rgba(8,145,178,0.16)_100%)] text-teal-700 shadow-sm ring-1 ring-teal-100">
          <MessageSquareText className="h-7 w-7" />
        </div>
        <CardTitle className="text-2xl sm:text-3xl">
          Ask RecordChat about IATA ONE Record
        </CardTitle>
        <CardDescription className="max-w-2xl">
          Stream answers from the broadened official and NE:ONE source pack.
          Concepts, ontology relationships, JSON-LD, API behavior, and
          implementation support all land in the same chat surface.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 pt-0 sm:grid-cols-3">
        <div className="rounded-[24px] border border-slate-200/90 bg-slate-50/80 p-4 text-left shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
            Ontology
          </p>
          <p className="mt-2 text-sm text-slate-700">
            Inspect class relationships, properties, and official ontology links.
          </p>
        </div>
        <div className="rounded-[24px] border border-slate-200/90 bg-slate-50/80 p-4 text-left shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
            Implementation
          </p>
          <p className="mt-2 text-sm text-slate-700">
            Get grounded NE:ONE setup, Docker Compose, and API guidance.
          </p>
        </div>
        <div className="rounded-[24px] border border-slate-200/90 bg-slate-50/80 p-4 text-left shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
            Structured Output
          </p>
          <p className="mt-2 text-sm text-slate-700">
            Review JSON-LD and citations alongside the streamed answer.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
