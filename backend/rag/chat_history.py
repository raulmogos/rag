import psycopg

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_session_id
    ON chat_history (session_id);
"""


def _title_from_message(message: str, max_len: int = 60) -> str:
    text = " ".join(message.split())
    if len(text) <= max_len:
        return text or "Chat"
    return f"{text[: max_len - 1]}…"


class ChatHistoryStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._conn: psycopg.AsyncConnection | None = None

    async def connect(self) -> None:
        self._conn = await psycopg.AsyncConnection.connect(self.database_url)
        async with self._conn.cursor() as cursor:
            await cursor.execute(_SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def save(self, session_id: str, role: str, content: str) -> None:
        if self._conn is None:
            raise RuntimeError("ChatHistoryStore is not connected.")

        async with self._conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO chat_history (session_id, role, content)
                VALUES (%s, %s, %s)
                """,
                (session_id, role, content),
            )
        await self._conn.commit()

    async def get_messages(self, session_id: str) -> list[dict[str, str]]:
        if self._conn is None:
            raise RuntimeError("ChatHistoryStore is not connected.")

        async with self._conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT id, role, content, created_at
                FROM chat_history
                WHERE session_id = %s
                ORDER BY id ASC
                """,
                (session_id,),
            )
            rows = await cursor.fetchall()

        return [
            {
                "id": str(row[0]),
                "role": row[1],
                "content": row[2],
                "created_at": row[3].isoformat(),
            }
            for row in rows
        ]

    async def list_sessions(self, limit: int = 50) -> list[dict[str, str]]:
        if self._conn is None:
            raise RuntimeError("ChatHistoryStore is not connected.")

        async with self._conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT
                    session_id,
                    COUNT(*) AS message_count,
                    MIN(created_at) AS started_at,
                    MAX(created_at) AS updated_at,
                    (
                        SELECT content
                        FROM chat_history first_msg
                        WHERE first_msg.session_id = grouped.session_id
                          AND first_msg.role = 'user'
                        ORDER BY first_msg.id ASC
                        LIMIT 1
                    ) AS title
                FROM chat_history grouped
                GROUP BY session_id
                ORDER BY updated_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = await cursor.fetchall()

        return [
            {
                "session_id": str(row[0]),
                "message_count": str(row[1]),
                "started_at": row[2].isoformat(),
                "updated_at": row[3].isoformat(),
                "title": _title_from_message(row[4] or "Chat"),
            }
            for row in rows
        ]
