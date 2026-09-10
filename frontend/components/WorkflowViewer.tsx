"use client";

import { useState } from "react";
import {
  Check,
  CheckCircle2,
  CircleDashed,
  Copy,
  Loader2,
  SkipForward,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type {
  ConnectorAvailability,
  WorkflowArtifact,
  WorkflowResult,
  WorkflowStatus,
  WorkflowStep,
  WorkflowStepStatus,
} from "@/lib/api";
import { cn, copyText } from "@/lib/utils";

const STATUS_STYLES: Record<
  WorkflowStatus,
  { label: string; className: string }
> = {
  completed: {
    label: "Completed",
    className: "border-emerald-200 bg-emerald-50 text-emerald-700",
  },
  blocked: {
    label: "Blocked",
    className: "border-amber-200 bg-amber-50 text-amber-700",
  },
  failed: {
    label: "Failed",
    className: "border-rose-200 bg-rose-50 text-rose-700",
  },
  planned: {
    label: "Planned",
    className: "border-sky-200 bg-sky-50 text-sky-700",
  },
};

const AVAILABILITY_STYLES: Record<
  ConnectorAvailability,
  { label: string; className: string }
> = {
  ready: {
    label: "Ready",
    className: "border-emerald-200 bg-emerald-50 text-emerald-700",
  },
  unconfigured: {
    label: "Unconfigured",
    className: "border-amber-200 bg-amber-50 text-amber-700",
  },
  unavailable: {
    label: "Unavailable",
    className: "border-rose-200 bg-rose-50 text-rose-700",
  },
};

function StepIcon({ status }: { status: WorkflowStepStatus }) {
  if (status === "completed") {
    return <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
  }
  if (status === "failed") {
    return <XCircle className="h-4 w-4 text-rose-600" />;
  }
  if (status === "skipped") {
    return <SkipForward className="h-4 w-4 text-slate-400" />;
  }
  if (status === "ready") {
    return <Loader2 className="h-4 w-4 text-sky-600" />;
  }
  return <CircleDashed className="h-4 w-4 text-slate-400" />;
}

function CopyBlock({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    if (await copyText(value)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    }
  }

  return (
    <button
      type="button"
      onClick={copy}
      aria-label={`Copy ${label}`}
      title={copied ? "Copied" : `Copy ${label}`}
      className="inline-flex h-7 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2 text-[11px] font-medium text-slate-500 transition hover:border-accent-ring hover:text-accent"
    >
      {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function ArtifactCard({ artifact }: { artifact: WorkflowArtifact }) {
  const [expanded, setExpanded] = useState(false);
  const raw =
    artifact.content === null || artifact.content === undefined
      ? ""
      : typeof artifact.content === "string"
        ? artifact.content
        : JSON.stringify(artifact.content, null, 2);
  const preview = raw.split("\n").slice(0, 6).join("\n");
  const hasMore = raw.split("\n").length > 6;

  return (
    <article className="rounded-xl border border-slate-200/80 bg-white/80 p-3.5 shadow-rc-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-slate-900">
            {artifact.name}
          </p>
          <p className="mt-0.5 text-[11px] uppercase tracking-wide text-slate-400">
            {artifact.kind}
          </p>
        </div>
        {raw ? <CopyBlock label={artifact.name} value={raw} /> : null}
      </div>
      {raw ? (
        <>
          <pre className="mt-3 max-h-48 overflow-auto whitespace-pre-wrap break-all rounded-lg bg-slate-50 px-3 py-2 font-mono text-[11px] leading-4 text-slate-600">
            {expanded ? raw : preview}
          </pre>
          {hasMore ? (
            <button
              type="button"
              onClick={() => setExpanded((value) => !value)}
              className="mt-2 text-[11px] font-medium text-accent transition hover:underline"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          ) : null}
        </>
      ) : (
        <p className="mt-3 text-xs text-slate-500">No content</p>
      )}
    </article>
  );
}

function StepRow({ step }: { step: WorkflowStep }) {
  return (
    <li className="flex gap-3 rounded-xl border border-slate-200/70 bg-white/70 px-3 py-3">
      <span className="mt-0.5 shrink-0">
        <StepIcon status={step.status} />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-medium text-slate-900">{step.title}</p>
          <Badge
            variant="outline"
            className="rounded-full border-slate-200 bg-slate-50 text-[10px] font-medium uppercase tracking-wide text-slate-500"
          >
            {step.status}
          </Badge>
        </div>
        {step.detail ? (
          <p className="mt-1 text-xs leading-5 text-slate-500">{step.detail}</p>
        ) : null}
      </div>
    </li>
  );
}

export function WorkflowViewer({ data }: { data: WorkflowResult }) {
  const statusStyle = STATUS_STYLES[data.status] ?? STATUS_STYLES.planned;
  const availabilityStyle =
    AVAILABILITY_STYLES[data.connector.availability] ??
    AVAILABILITY_STYLES.unconfigured;

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-slate-200/80 bg-white/80 p-4 shadow-rc-sm">
        <div className="flex flex-wrap items-center gap-2">
          <Badge
            variant="outline"
            className={cn("rounded-full text-[11px] font-semibold", statusStyle.className)}
          >
            {statusStyle.label}
          </Badge>
          <Badge
            variant="outline"
            className={cn(
              "rounded-full text-[11px] font-semibold",
              availabilityStyle.className
            )}
          >
            Connector · {availabilityStyle.label}
          </Badge>
        </div>
        <p className="mt-3 text-sm font-semibold text-slate-900">
          {data.workflow.replace(/_/g, " ")}
        </p>
        {data.detail ? (
          <p className="mt-2 text-xs leading-5 text-slate-600">{data.detail}</p>
        ) : null}
        <dl className="mt-3 grid gap-2 text-xs text-slate-500">
          <div className="flex gap-2">
            <dt className="shrink-0 font-medium text-slate-400">Connector</dt>
            <dd>{data.connector.name}</dd>
          </div>
          {data.connector.base_url ? (
            <div className="flex gap-2">
              <dt className="shrink-0 font-medium text-slate-400">URL</dt>
              <dd className="break-all">{data.connector.base_url}</dd>
            </div>
          ) : null}
          {data.connector.detail ? (
            <div className="flex gap-2">
              <dt className="shrink-0 font-medium text-slate-400">Detail</dt>
              <dd>{data.connector.detail}</dd>
            </div>
          ) : null}
        </dl>
      </section>

      <section>
        <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          Steps
        </h4>
        <ol className="space-y-2">
          {data.steps.map((step) => (
            <StepRow key={step.id} step={step} />
          ))}
        </ol>
      </section>

      {data.artifacts.length > 0 ? (
        <section>
          <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Artifacts
          </h4>
          <div className="space-y-3">
            {data.artifacts.map((artifact) => (
              <ArtifactCard
                key={`${artifact.kind}:${artifact.name}`}
                artifact={artifact}
              />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
