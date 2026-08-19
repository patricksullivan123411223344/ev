from spotify import PlaySearchedSongArgs
from pydantic import BaseModel, Field
from typing import ClassVar, Literal

class RouteDecision(BaseModel):
    domain: Literal[
        "spotify",
        "system",
        "research",
        "conversation"
    ] = Field(
        description="Select the capability domain to handle the user's request."
    )
    DOMAIN_DESCRIPTIONS: ClassVar[dict[str, str]] = {
        "spotify": (
            "Spotify music playback and control, including songs, "
            "artists, playlists, queue, skipping, and playback."
        )
    }

SPOTIFY_TOOLS = {
    "play_song": {
        "description": "Play a specific Spotify song",
        "args_model": PlaySearchedSongArgs,
        "function": "play_searched_song"
    }
}