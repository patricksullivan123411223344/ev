import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id = os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI"),
    scope = os.getenv("SPOTIFY_SCOPE")
))