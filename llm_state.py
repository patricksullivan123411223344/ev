from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Any, Literal

class ActionRecord(BaseModel):
    user_input: str
    domain: str
    tool_name: str
    arguments: dict[str, Any]
    result: str | None = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

class ChatHistory(BaseModel):
    role: Literal["user", "assistant"]
    content: str