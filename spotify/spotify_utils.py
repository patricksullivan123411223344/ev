import spotipy
from action_models import ActionOutcome, tool_success, tool_error
from spotipy.oauth2 import SpotifyOAuth
from pydantic import BaseModel, ConfigDict, Field
from dotenv import load_dotenv, find_dotenv
import time
import os

load_dotenv(find_dotenv())

class SPTSessionManager():
    def __init__(self):
        self.auth_manager = SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            scope=os.getenv("SPOTIFY_SCOPE")
        )
        self.sp=spotipy.Spotify(auth_manager=self.auth_manager)
        self.refresh_devices()

    def refresh_devices(self):
        self._raw_devices = self.sp.devices().get("devices", [])

    @property
    def devices(self):
        return self._raw_devices

    @property 
    def desktop_id(self):
        for d in self.devices:
            if d["type"].lower() == "computer":
                return d["id"]
        return None

    def _current_track_id(self, playback: dict | None) -> str | None:
        if not playback:
            return None

        item = playback.get("item")
        if not item:
            return None

        return item.get("id")

    def _wait_for_track_change(
        self,
        previous_track_id: str | None,
        timeout: float = 4.0,
        poll_interval: float = 0.25,
    ) -> str | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            playback = self.sp.current_playback()
            current_track_id = self._current_track_id(playback)

            if current_track_id and current_track_id != previous_track_id:
                return current_track_id

            time.sleep(poll_interval)

        return None

    def skip_track(self) -> ActionOutcome:
        self.refresh_devices()
        device_id = self.desktop_id

        if device_id is None:
            return tool_error(
                domain="spotify",
                tool_name="skip_track",
                error="No spotify desktop device is available."
            )

        try:
            before = self.sp.current_playback()
            before_track_id = self._current_track_id(before)
            self.sp.next_track(device_id=device_id)

            after_track_id = self._wait_for_track_change(
                previous_track_id=before_track_id,
                timeout=4.0
            )

            if after_track_id is None:
                return tool_error(
                    domain="spotify",
                    tool_name="skip_track",
                    error="Spotify accepted the request, but playback did not advance."
                )

            return tool_success(
                domain="spotify",
                tool_name="skip_track",
                facts={"track_id": after_track_id},
                message_template="Skipped the current track."
            )
        except spotipy.exceptions.SpotifyException as e:
            return tool_error(
                domain="spotify",
                tool_name="skip_track",
                error=f"Spotify rejected the skip request: {e}"
            )
        except Exception as e:
            return tool_error(
                domain="spotify",
                tool_name="skip_track",
                error=f"Could not verify the track skip: {e}"
            )

    def que_songs(self, songs: list[str]):
        device_id = self.desktop_id
        if device_id is None:
            raise RuntimeError("No spotify device is available.")

        success_count = 0
        for track in songs:
            try:
                self.sp.add_to_que(track_id=track, device_id=device_id)
                success_count += 1
            except spotipy.exceptions.SpotifyException as e:
                print(f"Error adding {track} to queue: {e}")

    def volume_controller(self, volume: int):
        device_id = self.desktop_id
        if device_id is None:
            raise RuntimeError("No Spotify playback device is available.")
        self.sp.volume(volume_percent=volume, device_id=device_id)

    def play_liked_tracks(self):
        results = self.sp.current_user_saved_tracks(limit=20)
        track_uris = [item['track']['uri'] for item in results['items']]
        if track_uris:
            print(f"Attempting to play: {len(track_uris)} tracks")
            self.sp.start_playback(device_id=self.target_device_id, uris=track_uris)
        else:
            print("No tracks found")

    # for a quick lock in
    def play_whats_real(self):
        device_id = self.desktop_id
        query = "track:Say Whats Real artist:Drake"
        search = self.sp.search(q=query, limit=1, type='track')
        print(search)
        if search["tracks"]["items"][0]["uri"]:
            track_uri = search["tracks"]["items"][0]["uri"]
            self.sp.start_playback(device_id=device_id, uris=[track_uri])

    def shuffle_playlist(self, playlist_name: str) -> str:
        self.refresh_devices()
        device_id = self.desktop_id
        if device_id is None:
            raise RuntimeError("No Spotify desktop playback device is available.")

        playlists = self.sp.current_user_playlists(limit=50).get("items", [])
        playlist = next(
            (
                item for item in playlists
                if item.get("name", "").casefold() == playlist_name.casefold()
            ),
            None,
        )
        if playlist is None:
            raise LookupError(f"Spotify could not find a playlist named '{playlist_name}'.")

        playlist_uri = playlist.get("uri")
        if not playlist_uri:
            raise LookupError(f"Spotify returned no playable URI for '{playlist_name}'.")

        self.sp.shuffle(state=True, device_id=device_id)
        self.sp.start_playback(device_id=device_id, context_uri=playlist_uri)
        return f"Playing shuffled playlist '{playlist_name}'."

    def play_searched_song(self, track: str, artist: str) -> None:
        self.refresh_devices()
        device_id = self.desktop_id
        if device_id is None:
            raise RuntimeError("No Spotify desktop playback device is available.")

        query = f"track:{track} artist:{artist}"
        search = self.sp.search(q=query, limit=1, type='track')
        items = search.get("tracks", {}).get("items", [])
        if not items:
            raise LookupError(f"Spotify could not find '{track}' by {artist}.")

        track_uri = items[0].get("uri")
        if not track_uri:
            raise LookupError(f"Spotify returned no playable URI for '{track}'.")

        self.sp.start_playback(device_id=device_id, uris=[track_uri])
        return f"Playing '{track}' by {artist}."

    def fetch_playlist_id(self):
        results = self.sp.current_user_playlists(limit=20)

        for playlist in results ['items']:
            print(f"Name: {playlist["name"]} -> ID: {playlist["id"]}")

class ToolArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

class NoArgs(ToolArgs):
    pass

class PlaySearchedSongArgs(ToolArgs):
    track: str = Field(
        description="Name of the song to play. May be explicitly requested by the user "
                    "or selected by the model when the user gives broader criteria."
    )
    artist: str = Field(
        description="Artist performing the song to play. Infer when necessary."
    )

class VolumeControllerArgs(ToolArgs):
    volume: int = Field(
        ge=0,
        le=100,
        description="Integer relating to the volume percentage ranging from 0 to 100"
                    "Gets louder by increasing percentage amount, lower by lowering percentage amount"
    )

class PlayShuffledPlaylistArgs(ToolArgs):
    playlist_name: str = Field(
        min_length=1,
        description="Name of the Spotify playlist to shuffle and play. Follow the users commanded name"
    )

if __name__ == "__main__":
    instance = SPTSessionManager()
    instance.fetch_playlist_id()
