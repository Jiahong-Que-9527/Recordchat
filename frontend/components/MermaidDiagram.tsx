"use client";

import { useEffect, useState } from "react";
import { Maximize2, Minus, Plus, RotateCcw, Workflow, X } from "lucide-react";

// Mermaid is heavy, so it is dynamically imported the first time a diagram
// actually appears and initialised once with the RecordChat palette.
let initialized = false;
// Monotonic counter so every render attempt gets a fresh DOM id — reusing a
// stable id across re-renders is the classic Mermaid footgun that leaves an
// orphan node behind and makes subsequent renders fail silently.
let renderSeq = 0;

async function getMermaid() {
  const mermaid = (await import("mermaid")).default;
  if (!initialized) {
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: "base",
      // Be generous so large model-generated diagrams don't trip the defaults
      // (maxTextSize 50k / maxEdges 500) and fail to render.
      maxTextSize: 200000,
      maxEdges: 2000,
      // Render at the diagram's natural pixel size instead of shrinking it to
      // the container. Inline we scale it down responsively, but the full-size
      // SVG is what the zoom dialog needs to stay crisp.
      flowchart: { useMaxWidth: false, htmlLabels: false },
      sequence: { useMaxWidth: false },
      er: { useMaxWidth: false },
      class: { useMaxWidth: false },
      gantt: { useMaxWidth: false },
      journey: { useMaxWidth: false },
      fontFamily:
        'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
      themeVariables: {
        // Match the app's accent (blue) + slate neutrals.
        primaryColor: "#eff6ff",
        primaryBorderColor: "#2563eb",
        primaryTextColor: "#0f172a",
        secondaryColor: "#f8fafc",
        secondaryBorderColor: "#cbd5e1",
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

// Drop the model's per-node colour directives so every diagram falls back to
// the single light-blue theme palette configured above (consistent with the
// app's accent). Only cosmetic statements are removed — never structure.
function unifyDiagramColors(source: string): string {
  const isFlow = /^\s*(?:graph|flowchart)\b/m.test(source);
  return source
    .split("\n")
    .filter((line) => {
      const trimmed = line.trim();
      if (/^(?:style|linkStyle|classDef)\s/i.test(trimmed)) return false;
      // `class A,B name` applies a CSS class in flowcharts; in a classDiagram
      // `class Foo` is structural, so only strip it for flow/graph diagrams.
      if (isFlow && /^class\s/i.test(trimmed)) return false;
      return true;
    })
    .join("\n")
    .replace(/:::[A-Za-z0-9_]+/g, "");
}

// LLMs frequently emit flowchart node labels with unquoted special characters
// (&, parentheses, colons) or bare <br>, which break Mermaid's parser. This is
// a best-effort repair applied ONLY after a raw render fails, so valid diagrams
// are never touched: wrap rectangle/rhombus labels in quotes and normalise <br>.
function normalizeMermaid(source: string): string {
  let out = source.replace(/<br\s*\/?\s*>/gi, "<br/>");

  // id[ label ] → id["label"]  (skips already-quoted labels and [[ ]] / [( )])
  out = out.replace(
    /([A-Za-z0-9_]+)\[([^[\]"\n|]+)\]/g,
    (_match, id: string, label: string) => `${id}["${label.trim()}"]`
  );
  // id{ label } → id{"label"}
  out = out.replace(
    /([A-Za-z0-9_]+)\{([^{}"\n|]+)\}/g,
    (_match, id: string, label: string) => `${id}{"${label.trim()}"}`
  );
  return out;
}

const MIN_ZOOM = 0.4;
const MAX_ZOOM = 4;
const ZOOM_STEP = 0.2;

function clampZoom(value: number): number {
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Math.round(value * 100) / 100));
}

// Full-screen viewer: shows the diagram at natural size with zoom controls and
// scroll/pan, so dense diagrams stay legible.
function MermaidZoomModal({ svg, onClose }: { svg: string; onClose: () => void }) {
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-[60] flex flex-col bg-slate-900/70 backdrop-blur-sm">
      <div className="flex items-center justify-between gap-2 border-b border-white/10 px-4 py-2.5">
        <span className="flex items-center gap-2 text-sm font-medium text-white/90">
          <Workflow className="h-4 w-4" />
          Diagram
        </span>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setZoom((z) => clampZoom(z - ZOOM_STEP))}
            aria-label="Zoom out"
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-white/80 transition hover:bg-white/10"
          >
            <Minus className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => setZoom(1)}
            aria-label="Reset zoom"
            title="Reset zoom"
            className="inline-flex h-8 min-w-[3.5rem] items-center justify-center gap-1 rounded-md px-2 text-xs font-medium text-white/80 transition hover:bg-white/10"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            {Math.round(zoom * 100)}%
          </button>
          <button
            type="button"
            onClick={() => setZoom((z) => clampZoom(z + ZOOM_STEP))}
            aria-label="Zoom in"
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-white/80 transition hover:bg-white/10"
          >
            <Plus className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="ml-1 inline-flex h-8 w-8 items-center justify-center rounded-md text-white/80 transition hover:bg-white/10"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <div
          className="flex min-h-full min-w-full items-center justify-center p-4 sm:p-8"
          onClick={(event) => {
            if (event.target === event.currentTarget) onClose();
          }}
        >
          <div
            // `zoom` (unlike transform: scale) grows the layout box, so the
            // diagram stays centred when it fits and scrolls cleanly when it
            // doesn't.
            style={{ zoom }}
            className="rounded-xl bg-white p-6 shadow-rc-md [&_svg]:h-auto"
            // eslint-disable-next-line react/no-danger
            dangerouslySetInnerHTML={{ __html: svg }}
          />
        </div>
      </div>
    </div>
  );
}

export function MermaidDiagram({
  code,
  streaming = false,
}: {
  code: string;
  streaming?: boolean;
}) {
  const [svg, setSvg] = useState("");
  const [failed, setFailed] = useState(false);
  const [zoomOpen, setZoomOpen] = useState(false);

  const source = code.trim();

  useEffect(() => {
    // Don't try to render half-streamed (invalid) or empty diagram source.
    if (streaming || !source) {
      return;
    }
    let cancelled = false;
    const renderId = `rc-mermaid-${(renderSeq += 1)}`;

    (async () => {
      try {
        const mermaid = await getMermaid();

        // Unify colours first, then try as-is; only if it fails fall back to
        // the best-effort repaired version. Every attempt uses a fresh DOM id.
        const themed = unifyDiagramColors(source);
        const variants = [themed];
        const repaired = normalizeMermaid(themed);
        if (repaired !== themed) {
          variants.push(repaired);
        }

        let rendered = "";
        let lastError: unknown = null;
        for (let i = 0; i < variants.length; i += 1) {
          const attemptId = `${renderId}-${i}`;
          try {
            // parse() throws on invalid syntax.
            await mermaid.parse(variants[i]);
            rendered = (await mermaid.render(attemptId, variants[i])).svg;
            lastError = null;
            break;
          } catch (error) {
            lastError = error;
            // Mermaid can leave an orphan measurement node in <body> on error;
            // clean it up so the next attempt starts fresh.
            document.getElementById(attemptId)?.remove();
            document.querySelector(`#d${attemptId}`)?.remove();
          }
        }

        if (lastError) {
          throw lastError;
        }
        if (!cancelled) {
          setSvg(rendered);
          setFailed(false);
        }
      } catch (error) {
        if (process.env.NODE_ENV !== "production") {
          console.warn("[RecordChat] Mermaid render failed:", error);
        }
        if (!cancelled) {
          setSvg("");
          setFailed(true);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [source, streaming]);

  if (!source) {
    return null;
  }

  if (streaming || (!svg && !failed)) {
    return (
      <div className="my-3 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-500">
        <Workflow className="h-3.5 w-3.5 text-accent" />
        Preparing diagram…
      </div>
    );
  }

  // If the diagram can't be parsed/rendered, keep the source visible (clearly
  // labelled) so the information is never lost.
  if (failed) {
    return (
      <div className="my-3 overflow-hidden rounded-xl border border-amber-200 bg-amber-50">
        <div className="flex items-center gap-2 border-b border-amber-200 px-3 py-2 text-xs font-medium text-amber-700">
          <Workflow className="h-3.5 w-3.5" />
          Diagram source (could not be rendered)
        </div>
        <pre className="overflow-x-auto p-3 text-xs leading-relaxed text-slate-700">
          <code>{source}</code>
        </pre>
      </div>
    );
  }

  return (
    <>
      <figure className="group relative my-3 overflow-x-auto rounded-xl border border-slate-200 bg-white p-4">
        <button
          type="button"
          onClick={() => setZoomOpen(true)}
          aria-label="Enlarge diagram"
          title="Enlarge diagram"
          className="absolute right-2 top-2 z-10 inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white/90 text-slate-500 opacity-100 shadow-rc-sm backdrop-blur transition hover:bg-white hover:text-accent xl:opacity-0 group-hover:opacity-100"
        >
          <Maximize2 className="h-3.5 w-3.5" />
        </button>
        <div
          className="text-center [&_svg]:mx-auto [&_svg]:h-auto [&_svg]:max-w-full"
          // eslint-disable-next-line react/no-danger
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      </figure>

      {zoomOpen ? (
        <MermaidZoomModal svg={svg} onClose={() => setZoomOpen(false)} />
      ) : null}
    </>
  );
}
