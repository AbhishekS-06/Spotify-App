from flask import Flask, render_template, redirect, url_for, session, request
import requests, os, logging
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    # Redirect to Spotify login
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "user-read-private user-read-email playlist-read-private",
    }
    spotify_auth_url = f"{AUTH_URL}?{requests.compat.urlencode(params)}"
    return redirect(spotify_auth_url)


@app.route("/callback")
def callback():
    # Handle Spotify callback and fetch access token
    code = request.args.get("code")
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(TOKEN_URL, data=payload)
    token_info = response.json()
    access_token = token_info.get("access_token")

    # Store access token in session for later use
    session["access_token"] = access_token
    return redirect(url_for("playlists"))


@app.route("/playlists")
def playlists():
    # Fetch user playlists
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("login"))

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        # Fetch playlists from Spotify API
        response = requests.get(f"{API_BASE_URL}me/playlists", headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (e.g., 401, 500)
        playlists = response.json().get("items", [])

        # Filter only valid playlists
        valid_playlists = [
            playlist for playlist in playlists
            if playlist and "images" in playlist and playlist["images"]
        ]

        return render_template("playlists.html", playlists=valid_playlists)

    except requests.exceptions.HTTPError as http_err:
        # Handle specific HTTP errors (e.g., expired token, unauthorized)
        if response.status_code == 401:
            session.pop("access_token", None)  # Clear session and redirect to login
            return redirect(url_for("login"))
        return f"HTTP error occurred: {http_err}", 500

    except requests.exceptions.RequestException as req_err:
        # Handle other request issues (e.g., connection errors)
        return f"Request error occurred: {req_err}", 500

    except KeyError as key_err:
        # Handle unexpected API response structure
        return f"Unexpected data format: {key_err}", 500

    except Exception as e:
        # Catch-all for other exceptions
        return f"An error occurred: {e}", 500


if __name__ == "__main__":
    app.run(debug=True)