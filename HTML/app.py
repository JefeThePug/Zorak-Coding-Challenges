import os
import sys
import requests

from flask import Flask, redirect, url_for, request, session
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

DISCORD_CLIENT_ID = os.getenv('CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('CLIENT_SECRET')
DISCORD_REDIRECT_URI = "http://127.0.0.1:5000/callback"

@app.route("/")
def home():
    return '<h2><a href="/login">Login with Discord</a></h2>'

@app.route("/login")
def login():
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds guilds.members.read guilds.join role_connections.write"
    }
    return redirect(f"https://discord.com/api/oauth2/authorize?{urlencode(params)}")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return 'Error: No code provided', 400
    
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post("https://discord.com/api/oauth2/token", data=token_data, headers=headers)
    
    token = response.json()["access_token"]
    if not token:
        return 'Error: No token received', 400
    session["token"] = token
    
    return redirect(url_for("profile"))

@app.route("/profile")
def profile():
    token = session.get("token")
    if not token:
        return redirect(url_for("login"))
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://discord.com/api/users/@me", headers=headers)
    if response.status_code != 200:
        return 'Error: No Response', 400
    user_data = response.json()
    if not user_data:
        return 'Error: No user data received', 400
    session["user_data"] = user_data

    user_id = user_data["id"]
    avatar_hash = user_data["avatar"]
    avatar_url = "blank.png"
    if avatar_hash:
        file_type = ['png','gif'][avatar_hash.startswith("a_")]
        avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{file_type}"
    
    return f"""
    Logged in as {user_data['username']}#{user_data['discriminator']}<br>
    <img src="{avatar_url}" alt="User Avatar"><br>
    <a href='/access'>Grant Access</a>
    <a href='/logout'>Logout</a>
    """

@app.route("/access")
def access():
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        return "Error: Bot token not found", 500

    guild_id = 1251181792111755391
    user_id = session["user_data"]["id"]
    role_id = 1252507286489010178
    headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}

    response = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}", headers=headers)
    if response.status_code == 404:  # User is not a member of the guild
        payload = {"access_token": session["token"]}
        try:
            response = requests.put(f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}", headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}", file=sys.stderr)
            error_message = response.text
            return f'Error: Failed to assign role: {error_message}', 400

    try:
        response = requests.put(f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}/roles/{role_id}", headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
    else:
        if response.status_code!= 204:
            error_message = response.text
            try:
                error_json = response.json()
                error_message = error_json.get('message', error_message)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                pass
            return f'Error: Failed to assign role: {error_message}', 400
    return 'Role assigned successfully!'


@app.route('/logout')
def logout():
    session.pop('token', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)