"use client";

import { useEffect, useRef, useState } from "react";
import { Workflow } from "lucide-react";

// Mermaid is heavy, so it is dynamically imported the first time a diagram
// actually appears and initialised once with the RecordChat palette.
let initialized = false;
async function getMermaid() {
  const mermaid = (await import("mermaid")).default;
  if (!initialized) {
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: "base",
      fontFamily:
        'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
      themeVariables: {
        // Match the app's accent (blue) + slate neutrals.
        primaryColor: "#eff6ff",
        primaryBorderColor: "#2563eb",
        primaryTextColor: "#0f172a",
        secondaryColor: "#f8fafc",
        secondaryBorderColor: "#cbd5e1",
        secondaryTextColor: "#334155",
        tertiaryColor: "#ffffff",
        tertiaryBorderColor: "#e2e8f0",
        lineColor: "#94a3b8",
        textColor: "#334155",
        mainBkg: "#eff6ff",
        nodeBorder: "#2563eb",
        clusterBkg: "#f8fafc",
        clusterBorder: "#e2e8f0",
        titleColor: "#0f172a",
        edgeLabelBackground: "#ffffff",
        fontSize: "14px",
      },
    });
    initialized = true;
  }
  return mermaid;
}

export function MermaidDiagram({
  code,
  streaming = false,
}: {
  code: string;
  streaming?: boolean;
}) {
  const idRef = useRef(`rc-mermaid-${Math.random().toString(36).slice(2)}`);
  const [svg, setSvg] = useState("");
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    // Don't try to render half-streamed (invalid) diagram source.
    if (streaming) return;
    let cancelled = false;
    (async () => {
      try {
        const mermaid = await getMermaid();
        const valid = await mermaid.parse(code, { suppressErrors: true });
        if (!valid) throw new Error("invalid mermaid");
        const { svg: rendered } = await mermaid.render(idRef.current, code);
        if (!cancelled) {
          setSvg(rendered);
          setFailed(false);
        }
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [code, streaming]);

  if (streaming || (!svg && !failed)) {
    return (
      <div className="my-3 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-500">
        <Workflow className="h-3.5 w-3.5 text-accent" />
        Preparing diagram…
      </div>
    );
  }

  // If the diagram can't be parsed, fall back to the raw source so the
  // information is never lost.
  if (failed) {
    return (
      <pre className="my-3">
        <code>{code}</code>
      </pre>
    );
  }

  return (
    <figure
      className="my-3 overflow-x-auto rounded-xl border border-slate-200 bg-white p-4 text-center [&_svg]:mx-auto [&_svg]:h-auto [&_svg]:max-w-full"
      // eslint-disable-next-line react/no-danger
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
