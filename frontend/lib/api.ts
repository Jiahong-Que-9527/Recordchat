// API client + types. Field names mirror the backend contract (SPEC section 6).

export type QueryType =
  | "concept_explanation"
  | "relationship_question"
  | "api_question"
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

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function sendChat(message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    throw new Error(`Backend error ${res.status}`);
  }
  return res.json();
}
