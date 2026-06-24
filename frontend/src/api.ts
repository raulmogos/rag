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

export type SessionSummary = {
  session_id: string;
  title: string;
  message_count: number;
  started_at: string;
  updated_at: string;
};

export type SessionHistory = {
  session_id: string;
  messages: Array<{
    id: string;
    role: string;
    content: string;
    created_at: string;
  }>;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch("/api/health");
  if (!response.ok) {
    throw new Error("Backend is unavailable.");
  }
  return response.json();
}

export async function fetchSessions(): Promise<SessionSummary[]> {
  const response = await fetch("/api/sessions");
  if (!response.ok) {
    throw new Error("Failed to load chat history.");
  }
  return response.json();
}

export async function fetchSessionHistory(
  sessionId: string,
): Promise<SessionHistory> {
  const response = await fetch(`/api/sessions/${sessionId}`);
  if (!response.ok) {
    throw new Error("Failed to load session.");
  }
  return response.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(`/api/sessions/${sessionId}`, {
    method: "DELETE",
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail ?? "Failed to delete chat.");
  }
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
