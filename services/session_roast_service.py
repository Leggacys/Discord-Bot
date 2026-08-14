import asyncio
from dataclasses import dataclass, field

from services.roast_service import generate_group_session_roast


@dataclass
class FinishedSession:
    username: str
    game_name: str
    duration_seconds: int


@dataclass
class SessionRoastBatch:
    sessions: list[FinishedSession] = field(
        default_factory=list
    )
    task: asyncio.Task | None = None