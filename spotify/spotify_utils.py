import spotipy
from spotipy.oauth2 import SpotifyOAuth
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
        device_id = self.desktop_id
        query = f"track:{track} artist:{artist}"
        search = self.sp.search(q=query, limit=1, type='track')
        if search["tracks"]["items"][0]["uri"]:
            track_uri = search["tracks"]["items"][0]["uri"]
            self.sp.start_playback(device_id=device_id, uris=[track_uri])

if __name__ == "__main__":
    instance = SPTSessionManager()
    instance.play_searched_song("Nothing like uuu", "Nettspend")

