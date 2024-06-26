import os
import sys
import json
import requests

from flask import Flask, redirect, render_template, url_for, request, session, current_app
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

app = Flask(__name__, template_folder=".")
app.secret_key = os.urandom(24)

DISCORD_CLIENT_ID = os.getenv("CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
DISCORD_REDIRECT_URI = "http://127.0.0.1:5000/callback"

NUM = 2


@app.route("/")
def index():
    img = "images/index/blank.png"
    text = "Log-in<br>with Discord"
    if "user_data" in session:
        img = session["user_data"]["img"]
        text = "Logout"
    return render_template("index.html", img=img, text=text, num=NUM)


@app.route("/pre-login")
def pre_login():
    if "user_data" in session:
        return render_template("logout.html", img=session["user_data"]["img"], text="")
    return render_template("login.html", img="images/index/blank.png", text="")


@app.route("/login")
def login():
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds guilds.members.read guilds.join role_connections.write",
    }
    return redirect(f"https://discord.com/api/oauth2/authorize?{urlencode(params)}")


@app.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        print(session, file=sys.stderr)
        return render_template(
            "index.html",
            img="images/index/blank.png",
            text="Log-in<br>with Discord",
            num=NUM,
        )

    code = request.args.get("code")
    if not code:
        return "Error: No code provided", 400

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(
        "https://discord.com/api/oauth2/token", data=token_data, headers=headers
    )

    token = response.json()["access_token"]
    if not token:
        return "Error: No token received", 400
    session["token"] = token

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://discord.com/api/users/@me", headers=headers)
    if response.status_code != 200:
        return "Error: No Response", 400

    user_data = response.json()
    if not user_data:
        return "Error: No user data received", 400
    session["user_data"] = user_data

    user_id = user_data["id"]
    avatar_hash = user_data["avatar"]
    avatar_url = "images/index/blank.png"
    if avatar_hash:
        file_type = ["png", "gif"][avatar_hash.startswith("a_")]
        avatar_url = (
            f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{file_type}"
        )
        session["user_data"]["img"] = avatar_url

    return render_template("index.html", img=avatar_url, text="Logout", num=NUM)


@app.route("/challenge/<num>", methods=["GET", "POST"])
def get_challenge(num):
    if request.method == "GET":
        img = session["user_data"]["img"] if "user_data" in session else "images/index/blank.png"
        text = "Logout" if "user_data" in session else "Log-in<br>with Discord"

        with open(os.path.join(current_app.static_folder, "data.json")) as f:
            data = json.load(f)
        try:
            a, b = data[num].values()
        except KeyError:
            return render_template("index.html", img=img, text=text, num=NUM)
        
        params = {
            "img": img,
            "text": text,
            "num":num,
            "a": a,
            "b": b,
            "sol1": a["solution"],
            "sol2": b["solution"],
            "parttwo": True,
            "done": True,
        }
        return render_template("challenge.html", **params)
        

    else:  # POST
        return "Method not allowed", 405


@app.route("/access")
def access():
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        return "Error: Bot token not found", 500

    guild_id = 1251181792111755391
    user_id = session["user_data"]["id"]
    role_id = 1252507286489010178
    headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}

    response = requests.get(
        f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}",
        headers=headers,
    )
    if response.status_code == 404:  # User is not a member of the guild
        payload = {"access_token": session["token"]}
        try:
            response = requests.put(
                f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}", file=sys.stderr)
            error_message = response.text
            return f"Error: Failed to assign role: {error_message}", 400

    try:
        response = requests.put(
            f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
            headers=headers,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
    else:
        if response.status_code != 204:
            error_message = response.text
            try:
                error_json = response.json()
                error_message = error_json.get("message", error_message)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                pass
            return f"Error: Failed to assign role: {error_message}", 400
    return "Role assigned successfully!"


@app.route("/logout")
def logout():
    session.pop("token", None)
    session.pop("user_data", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
