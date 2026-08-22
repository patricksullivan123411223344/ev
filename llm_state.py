from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from action_models import ActionOutcome


class SpotifyState(BaseModel):
    volume_percent: int | None = None
    current_track_uri: str | None = None
    current_track: str | None = None
    current_artist: str | None = None
    is_playing: bool | None = None
    updated_at: datetime | None = None


class ActionStateManager(BaseModel):
    last_outcome: ActionOutcome | None = None

    def record_outcome(self, outcome: ActionOutcome) -> None:
        self.last_outcome = outcome

    def apply(self, outcome: ActionOutcome) -> None:
        # Domain state mutations will be added as each controller adopts ActionOutcome.
        pass


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
