"""In-memory session storage for multi-turn advising conversations."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class SlotValues:
    """Collected advising details gathered across turns."""

    program: str | None = None
    track: str | None = None
    start_term: str | None = None
    term: str | None = None
    certificate: str | None = None


@dataclass
class ConversationSession:
    """Pending topic and slot values for one chat session."""

    topic: str | None = None
    slots: SlotValues = field(default_factory=SlotValues)
    pending_slots: list[str] = field(default_factory=list)


_sessions: dict[UUID, ConversationSession] = {}


def get_or_create_session(
    session_id: UUID | None,
) -> tuple[UUID, ConversationSession]:
    """Return an existing session or create a new one."""

    if session_id is not None and session_id in _sessions:
        return session_id, _sessions[session_id]

    new_session_id = session_id or uuid4()
    session = ConversationSession()

    _sessions[new_session_id] = session

    return new_session_id, session


def save_conversation_session(
    session_id: UUID,
    session: ConversationSession,
) -> None:
    """Persist updated session state."""

    _sessions[session_id] = session


def clear_conversation_session(session_id: UUID) -> None:
    """Reset slot-filling state after a completed answer."""

    if session_id in _sessions:
        del _sessions[session_id]


def reset_session_store() -> None:
    """Clear all sessions. Intended for tests."""

    _sessions.clear()
