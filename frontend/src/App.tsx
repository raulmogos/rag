import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Container,
  Group,
  Loader,
  NavLink,
  Paper,
  ScrollArea,
  Stack,
  Text,
  Textarea,
  Title,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconMessageChatbot,
  IconPlus,
  IconRobot,
  IconSend,
  IconTrash,
  IconUser,
} from "@tabler/icons-react";
import {
  deleteSession,
  fetchHealth,
  fetchSessionHistory,
  fetchSessions,
  Message,
  resetSession,
  sendMessage,
  SessionSummary,
} from "./api";
import { MarkdownContent } from "./MarkdownContent";

function createId() {
  return crypto.randomUUID();
}

function formatWhen(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleString();
}

function toUiMessage(message: {
  id: string;
  role: string;
  content: string;
}): Message {
  const role =
    message.role === "user" || message.role === "assistant"
      ? message.role
      : "error";
  return { id: message.id, role, content: message.content };
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isError = message.role === "error";

  if (isError) {
    return (
      <Alert
        icon={<IconAlertCircle size={18} />}
        color="red"
        variant="light"
        title="Error"
      >
        {message.content}
      </Alert>
    );
  }

  return (
    <Paper
      withBorder
      shadow="xs"
      p="md"
      radius="lg"
      bg={isUser ? "indigo.0" : "gray.0"}
      style={{
        alignSelf: isUser ? "flex-end" : "flex-start",
        maxWidth: "85%",
      }}
    >
      <Group gap="xs" mb={6}>
        {isUser ? (
          <IconUser size={16} stroke={1.8} />
        ) : (
          <IconRobot size={16} stroke={1.8} />
        )}
        <Text size="xs" fw={700} tt="uppercase" c="dimmed">
          {isUser ? "You" : "Agent"}
        </Text>
      </Group>
      <MarkdownContent content={message.content} />
    </Paper>
  );
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);
  const [toolCount, setToolCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [backendOnline, setBackendOnline] = useState(false);
  const viewport = useRef<HTMLDivElement>(null);

  const refreshSessions = useCallback(async () => {
    try {
      setSessions(await fetchSessions());
    } catch {
      setSessions([]);
    } finally {
      setLoadingSessions(false);
    }
  }, []);

  const loadSession = useCallback(async (id: string) => {
    const history = await fetchSessionHistory(id);
    setSessionId(history.session_id);
    setMessages(history.messages.map(toUiMessage));
  }, []);

  useEffect(() => {
    fetchHealth()
      .then((health) => {
        setBackendOnline(health.status === "ok");
        setModel(health.model);
        setToolCount(health.tool_count);
      })
      .catch(() => setBackendOnline(false));

    refreshSessions();
  }, [refreshSessions]);

  useEffect(() => {
    viewport.current?.scrollTo({
      top: viewport.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading) {
      return;
    }

    setInput("");
    setMessages((current) => [
      ...current,
      { id: createId(), role: "user", content: text },
    ]);
    setLoading(true);

    try {
      const response = await sendMessage(text, sessionId);
      setSessionId(response.session_id);
      setMessages((current) => [
        ...current,
        { id: createId(), role: "assistant", content: response.reply },
      ]);
      await refreshSessions();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Something went wrong.";
      setMessages((current) => [
        ...current,
        { id: createId(), role: "error", content: message },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleNewChat() {
    try {
      const response = await resetSession(sessionId);
      setSessionId(response.session_id);
      setMessages([]);
      await refreshSessions();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not start a new chat.";
      setMessages((current) => [
        ...current,
        { id: createId(), role: "error", content: message },
      ]);
    }
  }

  async function handleSelectSession(id: string) {
    if (id === sessionId || loading) {
      return;
    }

    try {
      await loadSession(id);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not load chat.";
      setMessages([{ id: createId(), role: "error", content: message }]);
    }
  }

  async function handleDeleteSession(
    event: React.MouseEvent,
    id: string,
  ) {
    event.stopPropagation();
    if (loading) {
      return;
    }

    try {
      await deleteSession(id);
      if (sessionId === id) {
        setSessionId(null);
        setMessages([]);
      }
      await refreshSessions();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not delete chat.";
      setMessages((current) => [
        ...current,
        { id: createId(), role: "error", content: message },
      ]);
    }
  }

  return (
    <Box
      mih="100vh"
      style={{
        background:
          "radial-gradient(circle at top, rgba(99, 102, 241, 0.12), transparent 35%), var(--mantine-color-gray-0)",
      }}
    >
      <Container size="xl" py="xl">
        <Stack gap="md" mih="calc(100vh - 3rem)">
          <Paper withBorder shadow="sm" p="lg" radius="xl">
            <Group justify="space-between" align="flex-start" wrap="wrap">
              <Group gap="sm">
                <IconMessageChatbot size={28} stroke={1.6} />
                <div>
                  <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                    Local RAG Assistant
                  </Text>
                  <Title order={2}>Chat with your agent</Title>
                </div>
              </Group>

              <Group gap="sm">
                <Badge
                  color={backendOnline ? "green" : "red"}
                  variant="light"
                  size="lg"
                >
                  {backendOnline ? "Backend online" : "Backend offline"}
                </Badge>
                <Button
                  leftSection={<IconPlus size={16} />}
                  variant="light"
                  onClick={handleNewChat}
                >
                  New chat
                </Button>
              </Group>
            </Group>

            <Group gap="md" mt="md">
              <Badge variant="outline" color="gray">
                {model ? `Model: ${model}` : "Model: not connected"}
              </Badge>
              <Badge variant="outline" color="gray">
                {toolCount ? `${toolCount} tools loaded` : "Tools unavailable"}
              </Badge>
            </Group>
          </Paper>

          <Group align="stretch" gap="md" wrap="nowrap" style={{ flex: 1 }}>
            <Paper
              withBorder
              shadow="sm"
              radius="xl"
              p="md"
              w={280}
              style={{
                flexShrink: 0,
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
                minHeight: 420,
              }}
            >
              <Text size="sm" fw={700} mb="xs">
                Chat history
              </Text>
              <ScrollArea
                flex={1}
                type="scroll"
                scrollbars="y"
                offsetScrollbars
                scrollbarSize={6}
              >
                {loadingSessions ? (
                  <Group justify="center" py="xl">
                    <Loader size="sm" />
                  </Group>
                ) : sessions.length === 0 ? (
                  <Text size="sm" c="dimmed">
                    No past chats yet.
                  </Text>
                ) : (
                  <Stack gap={4}>
                    {sessions.map((session) => {
                      const isActive = session.session_id === sessionId;

                      return (
                        <NavLink
                          key={session.session_id}
                          label={session.title}
                          description={`${session.message_count} messages · ${formatWhen(session.updated_at)}`}
                          active={isActive}
                          variant="light"
                          color="indigo"
                          disabled={loading}
                          onClick={() =>
                            handleSelectSession(session.session_id)
                          }
                          rightSection={
                            <ActionIcon
                              variant="subtle"
                              color="red"
                              size="sm"
                              aria-label="Delete chat"
                              onClick={(event) =>
                                handleDeleteSession(event, session.session_id)
                              }
                            >
                              <IconTrash size={15} />
                            </ActionIcon>
                          }
                          styles={{
                            root: {
                              borderRadius: "var(--mantine-radius-md)",
                              paddingInline: 0,
                              paddingBlock: "var(--mantine-spacing-xs)",
                            },
                            body: {
                              flex: 1,
                              minWidth: 0,
                            },
                            label: {
                              fontSize: "var(--mantine-font-size-sm)",
                              fontWeight: 600,
                              lineClamp: 2,
                              whiteSpace: "normal",
                            },
                            description: {
                              fontSize: "var(--mantine-font-size-xs)",
                              lineClamp: 1,
                            },
                            section: {
                              marginInlineStart: "var(--mantine-spacing-xs)",
                              alignSelf: "center",
                            },
                          }}
                        />
                      );
                    })}
                  </Stack>
                )}
              </ScrollArea>
            </Paper>

            <Stack gap="md" style={{ flex: 1, minWidth: 0 }}>
              <Paper
                withBorder
                shadow="sm"
                radius="xl"
                p="md"
                style={{ flex: 1, minHeight: 420, display: "flex" }}
              >
                <ScrollArea style={{ flex: 1 }} viewportRef={viewport}>
                  {messages.length === 0 ? (
                    <Stack align="center" justify="center" mih={320} ta="center">
                      <IconRobot size={42} stroke={1.4} />
                      <Title order={3}>Ask anything</Title>
                      <Text maw={420} c="dimmed">
                        Pick a past chat from the sidebar or start a new one.
                      </Text>
                    </Stack>
                  ) : (
                    <Stack gap="sm" pr="xs">
                      {messages.map((message) => (
                        <MessageBubble key={message.id} message={message} />
                      ))}

                      {loading ? (
                        <Paper withBorder p="md" radius="lg" bg="gray.0" maw="85%">
                          <Group gap="sm">
                            <Loader size="sm" />
                            <Text size="sm" c="dimmed">
                              Agent is thinking...
                            </Text>
                          </Group>
                        </Paper>
                      ) : null}
                    </Stack>
                  )}
                </ScrollArea>
              </Paper>

              <Paper
                withBorder
                shadow="sm"
                p="md"
                radius="xl"
                component="form"
                onSubmit={handleSubmit}
              >
                <Group align="flex-end" wrap="nowrap">
                  <Textarea
                    value={input}
                    onChange={(event) => setInput(event.currentTarget.value)}
                    placeholder="Type your message..."
                    autosize
                    minRows={2}
                    maxRows={6}
                    disabled={loading || !backendOnline}
                    style={{ flex: 1 }}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        event.currentTarget.form?.requestSubmit();
                      }
                    }}
                  />
                  <ActionIcon
                    type="submit"
                    size="xl"
                    radius="xl"
                    variant="filled"
                    color="indigo"
                    disabled={loading || !backendOnline || !input.trim()}
                    aria-label="Send message"
                  >
                    <IconSend size={18} />
                  </ActionIcon>
                </Group>
              </Paper>
            </Stack>
          </Group>
        </Stack>
      </Container>
    </Box>
  );
}
