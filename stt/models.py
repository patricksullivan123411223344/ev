from pydantic import BaseModel, Field
from typing import Literal

class TranscriptEvent(BaseModel):
    type = Literal("final_transcript")
    text: str = Field(min_length=1)
    confidence: float | None = None
    duration_ms = int | None = None
    