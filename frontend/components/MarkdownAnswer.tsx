"use client";

import { isValidElement, useRef, useState, type ReactNode } from "react";
import { Check, Copy } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { MermaidDiagram } from "./MermaidDiagram";

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
    if (!text) return;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
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

export function MarkdownAnswer({
  text,
  streaming = false,
}: {
  text: string;
  streaming?: boolean;
}) {
  return (
    <div className="recordchat-markdown text-sm leading-7 text-slate-800">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          a: ({ ...props }) => (
            <a
              {...props}
              className="font-medium text-accent underline decoration-accent-ring underline-offset-4 transition hover:text-accent-hover"
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
        {text}
      </ReactMarkdown>
    </div>
  );
}
