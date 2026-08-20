import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv
import psutil
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

    def skip_track(self):
        self.sp.next_track()

    def liked_track_play(self):
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

class PlaySearchedSongArgs(BaseModel):
    track: str = Field(
        description="Name of the song to play. May be explicitly requested by the user "
                    "or selected by the model when the user gives broader criteria."
    )
    artist: str = Field(
        description="Artist performing the song to play. Infer when necessary."
    )

if __name__ == "__main__":
    instance = SPTSessionManager()

