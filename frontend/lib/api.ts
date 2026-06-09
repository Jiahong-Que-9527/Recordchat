// API client + types. Field names mirror the backend contract (SPEC section 6).

export type QueryType =
  | "concept_explanation"
  | "relationship_question"
  | "api_question"
  | "implementation_question"
  | "ontology_question"
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

export interface StreamEvent {
  event: "token" | "metadata";
  data: Record<string, unknown>;
}

function getApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }

  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }

  return "http://localhost:8000";
}

export async function sendChat(message: string): Promise<ChatResponse> {
  const res = await fetch(`${getApiBase()}/chat`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    throw new Error(`Backend error ${res.status}`);
  }
  return res.json();
}

export async function streamChat(
  message: string,
  handlers: {
    onToken: (text: string) => void;
    onMetadata: (data: ChatResponse) => void;
  }
): Promise<void> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok || !res.body) {
    throw new Error(`Backend error ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const parsed = parseSseEvent(rawEvent);
      if (parsed?.event === "token") {
        const text = parsed.data.text;
        if (typeof text === "string" && text) {
          handlers.onToken(text);
        }
      }
      if (parsed?.event === "metadata") {
        handlers.onMetadata(parsed.data as unknown as ChatResponse);
      }
      boundary = buffer.indexOf("\n\n");
    }

    if (done) {
      break;
    }
  }
}

function parseSseEvent(raw: string): StreamEvent | null {
  const lines = raw
    .split("\n")
    .map((line) => line.trimEnd())
    .filter(Boolean);
  const event = lines.find((line) => line.startsWith("event: "))?.slice(7);
  const dataLine = lines.find((line) => line.startsWith("data: "))?.slice(6);
  if (!event || !dataLine) {
    return null;
  }
  return {
    event: event as StreamEvent["event"],
    data: JSON.parse(dataLine) as Record<string, unknown>,
  };
}
