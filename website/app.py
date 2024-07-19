import os
import sys
import requests

from flask import (
    Flask,
    redirect,
    render_template,
    url_for,
    request,
    session,
    make_response,
    send_from_directory,
)
from itsdangerous import URLSafeTimedSerializer
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True  # DEBUG Environment ONLY
app.secret_key = os.getenv("SECRET_KEY")
serializer = URLSafeTimedSerializer(app.secret_key, salt="cookie")

app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)
db = mongo.cx["ZorakCodingChallenge"]
obfs = db["html"]
prog = db["progress"]
sols = db["solutions"]
roles = db["roles"]
data = db["data"]

DISCORD_CLIENT_ID = os.getenv("CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
DISCORD_REDIRECT_URI = "http://127.0.0.1:5000/callback"

NUM = db["release"].find_one({"name": "release"})["num"]


def set_progress(num, n):
    if "user_data" in session:
        prog.update_one(
            {"id": session["user_data"]["id"]},
            {"$set": {f"c{num}.{n}": True}},
        )
    else:
        return serializer.dumps(f"{num}{'AB'[n]}")


def get_progress():
    if "user_data" in session:
        progress = prog.find_one({"id": session["user_data"]["id"]})
        return {
            "img": session["user_data"]["img"],
            "text": "Logout",
            "login": "logout.html",
            "progress": progress,
            "rockets": [progress[f"c{i}"] for i in range(1, 11)],
        }
    else:
        cookies = [*request.cookies.keys()]
        s = [serializer.loads(x) for x in cookies if len(x) > 40]
        rockets = [[f"{n}{p}" in s for p in "AB"] for n in range(1, 11)]
        progress = {f"c{i}": pair for i, pair in enumerate(rockets, 1)}
        return {
            "img": "images/index/blank.png",
            "text": "Log-in<br>with Discord",
            "login": "login.html",
            "progress": progress,
            "rockets": rockets,
        }


@app.template_global()
def obfuscate(value):
    return obfs.find_one({"num": value})["obs"]


@app.template_global()
def obscure_post(value):
    return roles.find_one({"name": "to"})[f"{value}"]


@app.route("/")
def index():
    user = get_progress()
    return render_template(
        "index.html",
        img=user["img"],
        text=user["text"],
        rockets=user["rockets"],
        num=NUM,
    )


@app.route("/pre-login")
def pre_login():
    user = get_progress()
    return render_template(user["login"], img=user["img"], text="")


@app.route("/login")
def login():
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds.members.read guilds.join",
    }
    return redirect(f"https://discord.com/api/oauth2/authorize?{urlencode(params)}")


@app.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        print(session, file=sys.stderr)
        return redirect(url_for("index"))

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
    avatar_url = "images/index/noimg.png"
    if avatar_hash:
        file_type = ["png", "gif"][avatar_hash.startswith("a_")]
        avatar_url = (
            f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{file_type}"
        )
    session["user_data"]["img"] = avatar_url

    if prog.find_one({"id": session["user_data"]["id"]}) is None:
        new_doc = {f"c{i}": [False, False] for i in range(1, 11)}
        new_doc["id"] = session["user_data"]["id"]
        new_doc["name"] = session["user_data"]["username"]
        prog.insert_one(new_doc)

    return redirect(url_for("index"))


@app.route("/challenge/<num>", methods=["GET", "POST"])
def get_challenge(num):
    num = f"{obfs.find_one({'obs': num})['num']}"
    error = None
    cookie = None

    if request.method == "POST":
        guesses = [request.form.get(f"answer{i}", None) for i in (1, 2)]
        solutions = sols.find_one({"num": num})
        for n, guess in enumerate(guesses):
            if guess:
                if guess.replace("_", " ").upper().strip() == solutions[f"part{n + 1}"]:
                    cookie = set_progress(num, n)
                    resp = make_response(
                        redirect(url_for("get_challenge", num=obfuscate(int(num))))
                    )
                    if cookie:
                        resp.set_cookie(cookie, f"{num}{'AB'[n]}")
                    return resp
                else:
                    error = "Incorrect. Please try again."

    user = get_progress()
    progress = user["progress"][f"c{num}"]
    data_raw = dict(data.find_one({"id": "html"}))
    try:
        a, b, _ = data_raw[num].values()
    except KeyError:
        return redirect(url_for("index"))

    params = {
        "img": user["img"],
        "text": user["text"],
        "num": num,
        "a": a,
        "b": b,
        "sol1": a["solution"] if progress[0] else a["form"],
        "sol2": b["solution"] if progress[1] else b["form"],
        "parttwo": progress[0],
        "done": progress[1] and "user_data" in session,
        "error": error,
    }
    return render_template("challenge.html", **params)


@app.route("/access", methods=["POST"])
def access():
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        return "Error: Bot token not found", 500

    num = roles.find_one({"name": "from"})[f"{request.form.get('num')}"]

    guild_id = 1251181792111755391
    user_id = session["user_data"]["id"]
    role_id = roles.find_one({"name": "roles"})[num]
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
        return f"Error: {e}", 400
    else:
        if response.status_code != 204:
            error_message = response.text
            return f"Error: Failed to assign role: {error_message}", 400

    user = get_progress()
    egg = data.find_one({"id": "html"})[num]["EE"]

    return render_template(
        "linkcomplete.html",
        img=user["img"],
        text="",
        num=num,
        egg=egg,
    )


@app.route("/help")
def help():
    user = get_progress()
    return render_template("howto.html", img=user["img"], text=user["text"])


@app.route("/logout")
def logout():
    session.pop("token", None)
    session.pop("user_data", None)
    return redirect(url_for("index"))


@app.route('/418')
def route_418():
    response = make_response(send_from_directory("static/images/index", "hmm.png"))
    response.headers["Easter-Egg"] = "Well done, you!"
    response.status_code = 418
    return response


if __name__ == "__main__":
    app.run(debug=True)
