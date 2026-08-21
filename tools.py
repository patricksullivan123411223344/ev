from spotify import PlaySearchedSongArgs, VolumeControllerArgs, PlayShuffledPlaylistArgs, NoArgs
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Callable, ClassVar, Literal

class ToolDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    args_model: type[BaseModel]
    handler: Callable[..., Any]
    uses_chat_history: bool = False

class RouteDecision(BaseModel):
    domain: Literal[
        "spotify",
        "conversation"
    ] = Field(
        description="Select the capability domain to handle the user's request."
    )

    has_separate_conversation: bool = Field(
        description=(
            "True only when the user's message contains a separate question, comment, "
            "or conversational request in addition to an executable command. "
            "False for direct commands, including casual commands such as 'shuffle my playlist'."
        )
    )

    DOMAIN_DESCRIPTIONS: ClassVar[dict[str, str]] = {
        "spotify": (
            "Spotify music playback and control, including songs, "
            "artists, playlists, queue, skipping, and playback."
        )
    }

def build_spotify_tools(controller: Any) -> dict[str, ToolDefinition]:
    return {
        "play_song": ToolDefinition(
            name="play_song",
            description=(
                "Choose and play a spotify song matching the user's request. "
                "If the user specifies and exact song, use it. "
                "If the request is broad, infer an appropriate track and artist relative to the request."
            ),
            args_model=PlaySearchedSongArgs,
            handler=controller.play_searched_song,
            uses_chat_history=True,
        ),
        "volume_controller": ToolDefinition(
            name="volume_controller",
            description=(
                "Turn the volume up or down based on an integer value based on user request "
                "The user may ask an ambiguous amount, so judge as necessary "
                "integer value represents the percent volume 0 through 100"
            ),
            args_model=VolumeControllerArgs,
            handler=controller.volume_controller,
            uses_chat_history=True,
        ),
        "shuffle_playlist": ToolDefinition(
            name="shuffle_playlist",
            description=(
                "Shuffle and play the user's Spotify playlist. Provide the playlist name exactly "
                "or approximately as requested by the user."
            ),
            args_model=PlayShuffledPlaylistArgs,
            handler=controller.shuffle_playlist,
            uses_chat_history=True,
        ),
        "skip_track": ToolDefinition(
            name="skip_track",
            description=(
                "Skip the currently playing Spotify track."
            ),
            args_model=NoArgs,
            handler=controller.skip_track,
            uses_chat_history=False,
        )
    }