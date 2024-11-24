from flask import Flask, render_template, redirect, url_for, session, request
import requests

app = Flask(__name__)
app.secret_key = "your_secret_key"

CLIENT_ID = "a0d3125ad47c4a258f0ac6f1bd5ec2d3"
CLIENT_SECRET = "fed86126a79a46738e4014602a54df58"
REDIRECT_URI = "http://localhost:5000/callback"

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
    response = requests.get(f"{API_BASE_URL}me/playlists", headers=headers)
    playlists = response.json().get("items", [])
    return render_template("playlists.html", playlists=playlists)


if __name__ == "__main__":
    app.run(debug=True)