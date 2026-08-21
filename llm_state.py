from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Any, Literal

class SpotifyState(BaseModel):
    volume_percent: int | None = None
    current_track_uri: str | None = None
    current_track: str | None = None
    current_artist: str | None = None
    is_playing: bool | None = None
    updated_at: datetime | None = None

class ActionRecord(BaseModel):
    user_input: str
    domain: str
    tool_name: str
    arguments: dict[str, Any]
    result: str | None = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

class ConversationMemory(BaseModel):
    role: Literal["user", "assistant"]
    content: str