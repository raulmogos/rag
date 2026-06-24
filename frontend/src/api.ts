export type MessageRole = "user" | "assistant" | "error";

export type Message = {
  id: string;
  role: MessageRole;
  content: string;
};

export type HealthResponse = {
  status: string;
  model: string | null;
  tool_count: number;
  mcp_url: string;
};

export type ChatResponse = {
  reply: string;
  session_id: string;
};

export type ResetResponse = {
  session_id: string;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch("/api/health");
  if (!response.ok) {
    throw new Error("Backend is unavailable.");
  }
  return response.json();
}

export async function sendMessage(
  message: string,
  sessionId: string | null,
): Promise<ChatResponse> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail ?? "Failed to send message.");
  }

  return data;
}

export async function resetSession(
  sessionId: string | null,
): Promise<ResetResponse> {
  const response = await fetch("/api/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail ?? "Failed to reset chat.");
  }

  return data;
}
