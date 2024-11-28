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
        "scope": "playlist-read-private playlist-read-collaborative user-read-email user-read-private"    }
    spotify_auth_url = f"{AUTH_URL}?{requests.compat.urlencode(params)}"
    return redirect(spotify_auth_url)

'''@app.route("/callback")
def callback():
    return "Callback route is working!", 200'''

@app.route("/callback")
def callback():
    print("Callback route hit!")
    code = request.args.get("code")
    if not code:
        print("No authorization code received!")
        return "Authorization failed: No code received from Spotify.", 400

    print(f"Authorization Code: {code}")

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    # Make POST request to Spotify's token endpoint
    response = requests.post(TOKEN_URL, data=payload)

    if response.status_code != 200:
        return f"Failed to fetch token: {response.text}", 500

    token_info = response.json()
    access_token = token_info.get("access_token")
    if not access_token:
        print("No access token received!")
        return "Authorization failed: No access token received from Spotify.", 400
    # Save access token to session
    session["access_token"] = access_token
    return redirect(url_for("playlists"))


@app.route("/playlists")
def playlists():
    # Debugging: Log the access token
    access_token = session.get("access_token")
    
    if not access_token:
        return redirect(url_for("login"))

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(f"{API_BASE_URL}me/playlists", headers=headers)
        print(f"Spotify API Response: {response.status_code}, {response.text}")  # Log the response
        response.raise_for_status()  # Raise error if status is not 2xx
        playlists = response.json().get("items", [])
        valid_playlists = [
            playlist for playlist in playlists
            if playlist and "images" in playlist and playlist["images"]
        ]
        return render_template("playlists.html", playlists=valid_playlists)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return f"HTTP error occurred: {http_err}", 500

def refresh_access_token():
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        return None

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(TOKEN_URL, data=payload)
    if response.status_code == 200:
        token_info = response.json()
        # Update the session with the new access token
        session["access_token"] = token_info.get("access_token")
        return session["access_token"]
    else:
        print(f"Failed to refresh token: {response.json()}")
        return None

if __name__ == "__main__":
    app.run(debug=True)