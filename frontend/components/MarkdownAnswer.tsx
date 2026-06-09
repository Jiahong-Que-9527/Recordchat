"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

export function MarkdownAnswer({ text }: { text: string }) {
  return (
    <div className="recordchat-markdown text-sm leading-7 text-slate-800">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          a: ({ ...props }) => (
            <a
              {...props}
              className="font-medium text-teal-700 underline decoration-teal-200 underline-offset-4 transition hover:text-teal-900"
              target="_blank"
              rel="noreferrer"
            />
          ),
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
