"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowDown, MessageSquareText } from "lucide-react";
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
        "flex min-h-0 flex-1 flex-col rounded-2xl border border-slate-200 bg-white shadow-rc-sm",
        className
      )}
    >
      {children}
    </section>
  );
}

const NEAR_BOTTOM_PX = 120;

export function ConversationContent({
  children,
  watch,
  newTurnKey,
  className,
}: {
  children: React.ReactNode;
  /** Changes on every streaming update; drives "follow while pinned". */
  watch?: unknown;
  /** Increments when the user sends a new message; forces a re-pin + jump. */
  newTurnKey?: number;
  className?: string;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  // "pinned" = stuck to the bottom and following new content. The user
  // detaches by scrolling up; they re-attach by scrolling back to the bottom.
  const [pinned, setPinned] = useState(true);
  const pinnedRef = useRef(true);
  // Ignore scroll events fired by our own smooth programmatic scrolls so the
  // animation's intermediate positions don't get mistaken for a user scroll-up.
  const suppressUntil = useRef(0);

  const setPinnedBoth = useCallback((value: boolean) => {
    pinnedRef.current = value;
    setPinned(value);
  }, []);

  const scrollToBottom = useCallback((behavior: ScrollBehavior) => {
    if (behavior === "smooth") {
      suppressUntil.current = performance.now() + 700;
    }
    endRef.current?.scrollIntoView({ behavior, block: "end" });
  }, []);

  // Re-evaluate pinned state on user scroll. Programmatic scrolls always land
  // at the bottom (→ near bottom → stays pinned), so a "far from bottom" event
  // can only come from the user scrolling up.
  const handleScroll = useCallback(() => {
    if (performance.now() < suppressUntil.current) return;
    const el = scrollRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    setPinnedBoth(distance < NEAR_BOTTOM_PX);
  }, [setPinnedBoth]);

  // Follow new/streaming content only while pinned — instant, no animation.
  useEffect(() => {
    if (pinnedRef.current) {
      scrollToBottom("auto");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watch]);

  // A new user turn always re-pins and jumps to it.
  useEffect(() => {
    if (newTurnKey === undefined) return;
    setPinnedBoth(true);
    requestAnimationFrame(() => scrollToBottom("smooth"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [newTurnKey]);

  return (
    <div className="relative min-h-0 flex-1">
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className={cn("h-full overflow-y-auto px-4 py-5 sm:px-6 sm:py-6 xl:px-8", className)}
      >
        <div className="mx-auto flex max-w-3xl flex-col gap-4">
          {children}
          <div ref={endRef} />
        </div>
      </div>

      {!pinned ? (
        <button
          type="button"
          onClick={() => {
            setPinnedBoth(true);
            scrollToBottom("smooth");
          }}
          aria-label="Scroll to latest message"
          className="absolute bottom-4 left-1/2 inline-flex -translate-x-1/2 items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-rc-md transition hover:border-accent-ring hover:text-accent"
        >
          <ArrowDown className="h-3.5 w-3.5" />
          Latest
        </button>
      ) : null}
    </div>
  );
}

export function ConversationEmptyState() {
  return (
    <div className="mx-auto mt-10 flex max-w-md flex-col items-center text-center animate-[recordchat-rise_320ms_ease-out] sm:mt-16">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-weak text-accent">
        <MessageSquareText className="h-6 w-6" />
      </div>
      <h2 className="mt-4 text-xl font-semibold text-slate-900 sm:text-2xl">
        Ask RecordChat about IATA ONE Record
      </h2>
      <p className="mt-2 text-sm leading-6 text-slate-500">
        Grounded answers on ONE Record concepts, ontology relationships, JSON-LD,
        API behavior, and NE:ONE implementation — with sources you can inspect.
      </p>
    </div>
  );
}
