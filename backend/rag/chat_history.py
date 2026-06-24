import uuid

from sqlalchemy import delete, func, select

from rag.db import Database
from rag.models import ChatMessage


def _title_from_message(message: str, max_len: int = 60) -> str:
    text = " ".join(message.split())
    if len(text) <= max_len:
        return text or "Chat"
    return f"{text[: max_len - 1]}…"


def _parse_session_id(session_id: str) -> uuid.UUID:
    return uuid.UUID(session_id)


class ChatHistoryStore:
    def __init__(self, database_url: str) -> None:
        self._db = Database(database_url)

    async def connect(self) -> None:
        await self._db.connect()

    async def close(self) -> None:
        await self._db.close()

    async def save(self, session_id: str, role: str, content: str) -> None:
        message = ChatMessage(
            session_id=_parse_session_id(session_id),
            role=role,
            content=content,
        )
        async with self._db.session_factory() as session:
            session.add(message)
            await session.commit()

    async def get_messages(self, session_id: str) -> list[dict[str, str]]:
        parsed_session_id = _parse_session_id(session_id)
        async with self._db.session_factory() as session:
            result = await session.scalars(
                select(ChatMessage)
                .where(ChatMessage.session_id == parsed_session_id)
                .order_by(ChatMessage.id.asc())
            )
            messages = result.all()

        return [
            {
                "id": str(message.id),
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            }
            for message in messages
        ]

    async def list_sessions(self, limit: int = 50) -> list[dict[str, str]]:
        async with self._db.session_factory() as session:
            grouped = await session.execute(
                select(
                    ChatMessage.session_id,
                    func.count(ChatMessage.id).label("message_count"),
                    func.min(ChatMessage.created_at).label("started_at"),
                    func.max(ChatMessage.created_at).label("updated_at"),
                )
                .group_by(ChatMessage.session_id)
                .order_by(func.max(ChatMessage.created_at).desc())
                .limit(limit)
            )
            rows = grouped.all()

            summaries: list[dict[str, str]] = []
            for row in rows:
                title = await session.scalar(
                    select(ChatMessage.content)
                    .where(
                        ChatMessage.session_id == row.session_id,
                        ChatMessage.role == "user",
                    )
                    .order_by(ChatMessage.id.asc())
                    .limit(1)
                )
                summaries.append(
                    {
                        "session_id": str(row.session_id),
                        "message_count": str(row.message_count),
                        "started_at": row.started_at.isoformat(),
                        "updated_at": row.updated_at.isoformat(),
                        "title": _title_from_message(title or "Chat"),
                    }
                )

        return summaries

    async def delete_session(self, session_id: str) -> bool:
        parsed_session_id = _parse_session_id(session_id)
        async with self._db.session_factory() as session:
            result = await session.execute(
                delete(ChatMessage).where(ChatMessage.session_id == parsed_session_id)
            )
            await session.commit()
            return result.rowcount > 0
