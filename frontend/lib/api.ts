import type { UIMessage } from "ai";

export type QueryType =
  | "concept_explanation"
  | "relationship_question"
  | "api_question"
  | "implementation_question"
  | "ontology_question"
  | "synthetic_data_generation"
  | "jsonld_generation"
  | "general_question";

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

export const CHAT_MODELS = ["deepseek-v4-fast", "deepseek-v4-pro"] as const;
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
