"use client";

import {
  isValidElement,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Check, Copy, Lightbulb } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { copyText } from "@/lib/utils";
import { MermaidDiagram } from "./MermaidDiagram";

// Matches a section header line like "Answer:", "**Related concepts:**",
// "## Implementation note:", optionally with inline content after the colon.
const HEADER_RE =
  /^\s*(?:#{1,6}\s+)?(?:\*\*|__)?\s*(Answer|Related concepts?|Implementation notes?|Sources?)\s*(?:\*\*|__)?\s*:\s*(.*)$/i;

function canonicalSection(label: string): "answer" | "related" | "implementation" | "sources" {
  const l = label.toLowerCase();
  if (l.startsWith("related")) return "related";
  if (l.startsWith("implementation")) return "implementation";
  if (l.startsWith("source")) return "sources";
  return "answer";
}

// Split the model's structured answer into the parts we actually render.
// Related concepts / Sources are dropped here — <Message> renders them from the
// structured response data instead; the leading "Answer:" label is stripped.
function parseAnswerSections(text: string): { body: string; implementation?: string } {
  const lines = text.split("\n");
  const buckets: Record<string, string[]> = {
    answer: [],
    related: [],
    implementation: [],
    sources: [],
  };
  let current: keyof typeof buckets = "answer";
  let matchedAny = false;

  for (const line of lines) {
    const match = line.match(HEADER_RE);
    if (match) {
      matchedAny = true;
      current = canonicalSection(match[1]);
      const inline = match[2]?.trim();
      if (inline) buckets[current].push(inline);
      continue;
    }
    buckets[current].push(line);
  }

  if (!matchedAny) return { body: text.trim() };
  const body = buckets.answer.join("\n").trim();
  const implementation = buckets.implementation.join("\n").trim();
  return { body, implementation: implementation || undefined };
}

const LINK_CLASS =
  "font-medium text-accent underline decoration-accent-ring underline-offset-4 transition hover:text-accent-hover";

function ImplementationNote({ text }: { text: string }) {
  return (
    <div className="mt-3 flex gap-2.5 rounded-xl border border-accent-ring bg-accent-weak px-3.5 py-3">
      <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
      <div className="min-w-0 flex-1">
        <p className="mb-1 text-xs font-semibold text-accent">Implementation note</p>
        <div className="recordchat-markdown text-sm leading-6 text-slate-700">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ ...props }) => (
                <a {...props} className={LINK_CLASS} target="_blank" rel="noreferrer" />
              ),
            }}
          >
            {text}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

// Recursively collect raw text from rendered markdown children. rehype-highlight
// may wrap code in <span>s, so we rebuild the original source from text leaves.
function extractText(node: ReactNode): string {
  if (node == null || typeof node === "boolean") return "";
  if (typeof node === "string") return node;
  if (typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(extractText).join("");
  if (isValidElement(node)) {
    return extractText((node.props as { children?: ReactNode }).children);
  }
  return "";
}

function CodeBlock({ children }: { children: ReactNode }) {
  const preRef = useRef<HTMLPreElement>(null);
  const [copied, setCopied] = useState(false);

  async function copy() {
    const text = preRef.current?.textContent ?? "";
    if (await copyText(text)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    }
  }

  return (
    <div className="group relative">
      <button
        type="button"
        onClick={copy}
        aria-label="Copy code"
        className="absolute right-2 top-2 inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-800/80 px-2 py-1 text-[11px] font-medium text-slate-200 opacity-0 transition hover:bg-slate-700 focus-visible:opacity-100 group-hover:opacity-100"
      >
        {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
        {copied ? "Copied" : "Copy"}
      </button>
      <pre ref={preRef}>{children}</pre>
    </div>
  );
}

// During streaming we re-parse Markdown at most this often instead of on every
// token — full re-parse per token is O(n²) as the answer grows.
const STREAM_RENDER_MS = 90;

export function MarkdownAnswer({
  text,
  streaming = false,
}: {
  text: string;
  streaming?: boolean;
}) {
  // Throttle the text fed to ReactMarkdown while streaming.
  const latest = useRef(text);
  latest.current = text;
  const [shown, setShown] = useState(text);

  useEffect(() => {
    if (!streaming) {
      setShown(latest.current);
      return;
    }
    setShown(latest.current);
    const id = setInterval(() => setShown(latest.current), STREAM_RENDER_MS);
    return () => {
      clearInterval(id);
      setShown(latest.current);
    };
  }, [streaming]);

  // Drop redundant sections and pull out the implementation note. Cheap regex
  // pass over the (throttled) text, memoised — negligible cost.
  const { body, implementation } = useMemo(
    () => parseAnswerSections(shown),
    [shown]
  );

  // Syntax highlighting is the most expensive step, so skip it mid-stream and
  // apply it once the answer is complete.
  const rendered = useMemo(
    () => (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={streaming ? [] : [rehypeHighlight]}
        components={{
          a: ({ ...props }) => (
            <a
              {...props}
              className={LINK_CLASS}
              target="_blank"
              rel="noreferrer"
            />
          ),
          pre: ({ children }) => {
            const codeEl = Array.isArray(children) ? children[0] : children;
            const className = isValidElement(codeEl)
              ? ((codeEl.props as { className?: string }).className ?? "")
              : "";
            if (className.includes("language-mermaid")) {
              const raw = isValidElement(codeEl)
                ? extractText((codeEl.props as { children?: ReactNode }).children)
                : "";
              return <MermaidDiagram code={raw} streaming={streaming} />;
            }
            return <CodeBlock>{children}</CodeBlock>;
          },
          code: ({ className, children, ...props }) => {
            const isBlock = Boolean(className?.includes("language-"));
            if (!isBlock) {
              return (
                <code
                  {...props}
                  className="rounded-md bg-slate-100 px-1.5 py-0.5 font-mono text-[0.92em] text-slate-900"
                >
                  {children}
                </code>
              );
            }

            return (
              <code {...props} className={className}>
                {children}
              </code>
            );
          },
        }}
      >
        {body}
      </ReactMarkdown>
    ),
    [body, streaming]
  );

  return (
    <div className="recordchat-markdown text-sm leading-7 text-slate-800">
      {rendered}
      {implementation ? <ImplementationNote text={implementation} /> : null}
    </div>
  );
}
