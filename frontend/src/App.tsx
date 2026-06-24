import { FormEvent, useEffect, useRef, useState } from "react";
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Container,
  Group,
  Loader,
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
  IconUser,
} from "@tabler/icons-react";
import {
  fetchHealth,
  Message,
  resetSession,
  sendMessage,
} from "./api";

function createId() {
  return crypto.randomUUID();
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
      <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
        {message.content}
      </Text>
    </Paper>
  );
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);
  const [toolCount, setToolCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const viewport = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchHealth()
      .then((health) => {
        setBackendOnline(health.status === "ok");
        setModel(health.model);
        setToolCount(health.tool_count);
      })
      .catch(() => setBackendOnline(false));
  }, []);

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
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not start a new chat.";
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
      <Container size="md" py="xl">
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
                    Try weather, local time, math, or MCP utilities like
                    reversing text.
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

          <Paper withBorder shadow="sm" p="md" radius="xl" component="form" onSubmit={handleSubmit}>
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
      </Container>
    </Box>
  );
}
