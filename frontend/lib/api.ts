import type { UIMessage } from "ai";

export type QueryType =
  | "concept_explanation"
  | "relationship_question"
  | "api_question"
  | "implementation_question"
  | "ontology_question"
  | "architecture_question"
  | "synthetic_data_generation"
  | "jsonld_generation"
  | "general_question";

export const SYNTHETIC_MODES = ["local", "recordforge"] as const;
export type SyntheticMode = (typeof SYNTHETIC_MODES)[number];

export interface Source {
  source_name: string;
  section_title: string | null;
  source_url: string | null;
  chunk_id: string;
}

export interface ChatResponse {
  answer: string;
  query_type: QueryType;
  sources: Source[];
  related_concepts: string[];
  structured_output: Record<string, unknown> | null;
}

export type WorkflowStatus = "planned" | "blocked" | "failed" | "completed";
export type WorkflowStepStatus =
  | "pending"
  | "ready"
  | "skipped"
  | "failed"
  | "completed";
export type ConnectorAvailability = "ready" | "unconfigured" | "unavailable";

export interface WorkflowStep {
  id: string;
  title: string;
  status: WorkflowStepStatus;
  detail?: string | null;
}

export interface WorkflowArtifact {
  kind: string;
  name: string;
  content?: Record<string, unknown> | unknown[] | string | null;
}

export interface WorkflowConnectorInfo {
  name: string;
  availability: ConnectorAvailability;
  base_url?: string | null;
  detail?: string | null;
}

export interface WorkflowResult {
  kind: "workflow_result";
  workflow: string;
  status: WorkflowStatus;
  connector: WorkflowConnectorInfo;
  steps: WorkflowStep[];
  artifacts: WorkflowArtifact[];
  detail?: string | null;
}

export function isWorkflowResult(
  data: Record<string, unknown> | null | undefined
): data is WorkflowResult & Record<string, unknown> {
  return (
    !!data &&
    data.kind === "workflow_result" &&
    typeof data.workflow === "string" &&
    typeof data.status === "string" &&
    typeof data.connector === "object" &&
    data.connector !== null
  );
}

export function structuredOutputTitle(data: Record<string, unknown>): string {
  if (isWorkflowResult(data)) {
    const label = data.workflow.replace(/_/g, " ");
    return `Workflow · ${label}`;
  }
  const graph = data["@graph"];
  if (Array.isArray(graph) && graph.length > 0) {
    const firstType =
      graph.find(
        (item): item is Record<string, unknown> =>
          !!item && typeof item === "object" && typeof item["@type"] === "string"
      )?.["@type"] ?? null;
    const typeLabel =
      typeof firstType === "string"
        ? firstType.split(/[#/]/).pop() || firstType
        : "JSON-LD";
    return `${typeLabel} · ${graph.length} objects`;
  }
  const type = data["@type"];
  if (typeof type === "string" && type.trim()) {
    return type.split(/[#/]/).pop() || type;
  }
  return "Structured output";
}

// Mirrors the backend allowlist (`backend/app/core/llm.py` → ChatModel).
// Keep exactly one entry per allowed model, in the same order as the backend.
export const CHAT_MODELS = ["deepseek-v4-flash", "deepseek-v4-pro"] as const;
export type ChatModel = (typeof CHAT_MODELS)[number];

export type RecordChatDataParts = {
  recordchat: ChatResponse;
};

export type RecordChatMessage = UIMessage<unknown, RecordChatDataParts>;

export function getMessageText(message: RecordChatMessage): string {
  return message.parts
    .filter((part): part is Extract<RecordChatMessage["parts"][number], { type: "text" }> => part.type === "text")
    .map((part) => part.text)
    .join("");
}

export function getMessageData(
  message: RecordChatMessage
): ChatResponse | undefined {
  const dataPart = message.parts.find(
    (part): part is Extract<RecordChatMessage["parts"][number], { type: "data-recordchat" }> =>
      part.type === "data-recordchat"
  );
  return dataPart?.data;
}
