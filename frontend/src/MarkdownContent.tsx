import { Box, Text } from "@mantine/core";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { looksLikeMarkdown } from "./markdown";

type MarkdownContentProps = {
  content: string;
};

export function MarkdownContent({ content }: MarkdownContentProps) {
  if (!looksLikeMarkdown(content)) {
    return (
      <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
        {content}
      </Text>
    );
  }

  return (
    <Box className="markdown-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </Box>
  );
}
