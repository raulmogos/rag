const MARKDOWN_PATTERNS = [
  /^#{1,6}\s/m,
  /^\s*[-*+]\s/m,
  /^\s*\d+\.\s/m,
  /^\s*>\s/m,
  /```[\s\S]*?```/,
  /`[^`\n]+`/,
  /\*\*[^*\n]+\*\*/,
  /__[^_\n]+__/,
  /\[[^\]]+\]\([^)]+\)/,
  /^\|.+\|$/m,
];

export function looksLikeMarkdown(text: string): boolean {
  const trimmed = text.trim();
  if (!trimmed) {
    return false;
  }

  return MARKDOWN_PATTERNS.some((pattern) => pattern.test(trimmed));
}
