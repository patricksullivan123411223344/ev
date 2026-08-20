from spotify import PlaySearchedSongArgs, VolumeControllerArgs
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import ClassVar, Literal, Any

class RouteDecision(BaseModel):
    domain: Literal[
        "spotify",
        "conversation"
    ] = Field(
        description="Select the capability domain to handle the user's request."
    )

    needs_natural_response: bool = Field(
        description=(
            "True when the request contains conversation, humor, commentary, etc. "
            "or when a question is in addition to an executable command. "
            "False for a direct command requiring only confirmation."
        )
    )

    DOMAIN_DESCRIPTIONS: ClassVar[dict[str, str]] = {
        "spotify": (
            "Spotify music playback and control, including songs, "
            "artists, playlists, queue, skipping, and playback."
        )
    }

class ActionRecord(BaseModel):
    user_input: str

SPOTIFY_TOOLS = {
    "play_song": {
        "description": (
            "Choose and play a spotify song matching the user's request. "
            "If the user specifies and exact song, use it. "
            "If the request is broad, infer an appropriate track and artist relative to the request."
        ),
        "args_model": PlaySearchedSongArgs,
        "function": "play_searched_song",
        "uses_chat_history": True
    },
    "volume_controller": {
        "description": (
            "Turn the volume up or down based on an integer value based on user request "
            "The user may ask an ambiguous amount, so judge as necessary "
            "integer value represents the percent volume 0 through 100"
        ),
        "args_model": VolumeControllerArgs,
        "function": "volume_controller",
        "uses_chat_history": False
    }
}