import os
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    url_for,
    request,
    session,
    abort,
    flash,
    make_response,
    send_from_directory,
)
from itsdangerous import URLSafeTimedSerializer

from cache import DataCache
from models import db

# Load environment variables from .env file
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
path = os.path.join(parent_dir, '.env')
load_dotenv(path)

# Initialize Flask application
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True  # DEBUG Environment ONLY
app.secret_key = os.getenv("SECRET_KEY")
serializer = URLSafeTimedSerializer(app.secret_key, salt="cookie")

# Configure SQLAlchemy database URI and settings
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_SERVER}:{POSTGRES_PORT}/{DATABASE_NAME}"
)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False

# Initialize SQLAlchemy and the Data Cache with the Flask app
db.init_app(app)
data_cache = DataCache(app)

# Load Discord OAuth credentials from environment variables
DISCORD_CLIENT_ID = os.getenv("CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")


def set_progress(challenge_num: int, progress: int) -> str | None:
    """Set the progress for a user in the database.

    Args:
        challenge_num (int): The challenge number.
        progress (int): The specific progress index (0 or 1).
    """
    if "user_data" in session:
        # Change database and update Data Cache
        data_cache.update_progress(challenge_num, progress)
    else:
        # Alter Browser Cookies
        return serializer.dumps(f"{challenge_num}{'AB'[progress]}")


def get_progress() -> dict[str, str | None | list | dict[str, bool]]:
    """Retrieve the progress of the user.

    Returns:
        dict: A dictionary containing user progress and session information.
    """
    if "user_data" in session:
        # Retrieve information from Flask session and Data Cache
        data_cache.load_progress(session["user_data"]["id"])
        return {
            "id": session["user_data"]["id"],
            "img": session["user_data"]["img"],
            "text": "Logout",
            "login": "logout.html",
            "progress": data_cache.progress,
            "rockets": [data_cache.progress[f"c{i}"] for i in range(1, 11)],
        }
    else:
        # Retrieve information from Browser Cookies
        cookies = [*request.cookies.keys()]
        s = [serializer.loads(x) for x in cookies if len(x) > 40]
        rockets = [[f"{n}{p}" in s for p in "AB"] for n in range(1, 11)]
        progress = {f"c{i}": pair for i, pair in enumerate(rockets, 1)}
        return {
            "id": None,
            "img": "images/index/blank.png",
            "text": "Log-in<br>with Discord",
            "login": "login.html",
            "progress": progress,
            "rockets": rockets,
        }


@app.template_global()
def obfuscate(value: str | int) -> str | int:
    """Obfuscate a value using the obfuscation database.

    Args:
        value (str): The value to obfuscate.
    Returns:
        str: The obfuscated value.
    """
    return data_cache.html_nums[value]


@app.template_global()
def obscure_post(value: str | int) -> str:
    """Obscures week number using Data Cache (from database)

    Args:
        value (str): The number to obfuscate.
    Returns:
        str: The obfuscated number to pass to the HTML.
    """
    if isinstance(value, str):
        value = int(value)
    return data_cache.obfuscations[value]


@app.route("/")
def index() -> str:
    """Render the index page with user progress and release number.

    Returns:
        str: Rendered index.html template.
    """
    user = get_progress()
    release = data_cache.release
    return render_template(
        "index.html",
        img=user["img"],
        text=user["text"],
        rockets=user["rockets"],
        num=release,
    )


@app.route("/pre-login")
def pre_login() -> str:
    """Render the pre-login page.

    Returns:
        str: Rendered login template with user image.
    """
    user = get_progress()
    return render_template(user["login"], img=user["img"], text="")


@app.route("/login")
def login() -> Response:
    """Redirect the user to Discord's OAuth2 authorization page.

    Returns:
        Response: Redirect to Discord authorization URL.
    """
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds.members.read guilds.join",
    }
    return redirect(f"https://discord.com/api/oauth2/authorize?{urlencode(params)}")


@app.route("/callback")
def callback() -> Response | tuple[str, int]:
    """Handle the callback from Discord after user authorization.

    Returns:
        Response: Redirect to the index page or error message.
        tuple[str, int]: Error message with HTTP status code 400.
    """
    if request.args.get("error"):
        print(session)
        return redirect(url_for("index"))

    if not (code := request.args.get("code")):
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

    if not (token := response.json()["access_token"]):
        return "Error: No token received", 400
    session["token"] = token

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://discord.com/api/users/@me", headers=headers)
    if response.status_code != 200:
        return "Error: No Response", 400

    if not (user_data := response.json()):
        return "Error: No user data received", 400
    session["user_data"] = user_data

    # Get Discord profile picture for user
    user_id = user_data["id"]
    avatar_hash = user_data["avatar"]
    avatar_url = "images/index/noimg.png"
    if avatar_hash:
        file_type = ["png", "gif"][avatar_hash.startswith("a_")]
        avatar_url = (
            f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{file_type}"
        )
    session["user_data"]["img"] = avatar_url

    # Add to database if not present
    data_cache.load_progress(session["user_data"]["id"])
    if not data_cache.progress:
        added = data_cache.add_user(session["user_data"]["id"], session["user_data"]["username"])
        if not added:
            return redirect(url_for("logout"))
    return redirect(url_for("index"))


@app.route("/challenge/<num>", methods=["GET", "POST"])
def get_challenge(num) -> str | Response:
    """Render the challenge page for a specific challenge week number.

    Args:
        num (str): The challenge number.
    Returns:
        str: Rendered challenge.html template or error message.
        Response: redirect to the challenge page on correct guess.
    """
    num = data_cache.html_nums[num]
    error = None

    if request.method == "POST":
        guesses = [request.form.get(f"answer{i}", None) for i in (1, 2)]
        solutions = data_cache.solutions[num]
        for n, guess in enumerate(guesses):
            if guess:
                if guess.replace("_", " ").upper().strip() == solutions[f"part{n + 1}"]:
                    cookie = set_progress(num, n)
                    resp = make_response(
                        redirect(url_for("get_challenge", num=obfuscate(num)))
                    )
                    if cookie:
                        resp.set_cookie(cookie, f"{num}{'AB'[n]}")
                    return resp
                else:
                    error = "Incorrect. Please try again."

    user = get_progress()
    progress = user["progress"][f"c{num}"]
    try:
        a, b, _ = data_cache.html[num].values()
    except KeyError:
        return redirect(url_for("index"))

    params = {
        "img": user["img"],
        "text": user["text"],
        "num": f"{num}",
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
def access() -> str | tuple[str, int]:
    """Grant access to a user and assign roles in Discord.

    Returns:
        str: Rendered linkcomplete.html template or error message.
        tuple[str, int]: Error message with HTTP status code.
    """
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        return "Error: Bot token not found", 500

    num = data_cache.obfuscations[f"{request.form.get('num')}"]

    guild_id = data_cache.discord_ids["guild"]
    user_id = session["user_data"]["id"]
    channel_id = data_cache.discord_ids[f"{num}"]
    verified_role = "1343857328700657695"

    headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}
    url = f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 404:  # User is not a member of the guild
        payload = {"access_token": session["token"]}
        url = f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}"
        try:
            response = requests.put(url, headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return f"Error: Failed to assign role: {response.text}", 400
        else:
            url = f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}/roles/{verified_role}"
            try:
                response = requests.put(url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                return f"Error: {e}", 400
            else:
                if response.status_code != 204:
                    return f"Error: Failed to assign role: {response.text}", 400

    content = f"<@{user_id}> solved week {num}! If you'd like, please share how you arrived at the correct answer!"
    url = f"https://discord.com/api/v9/channels/{channel_id}/thread-members/{user_id}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        try:
            response = requests.post(url, headers=headers, json={"content": content})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return f"Error: {e}", 400
        else:
            if response.status_code != 200:
                return f"Error: Failed to send message: {response.text}", 400

    user = get_progress()
    egg = data_cache.html[num]["ee"]

    return render_template(
        "linkcomplete.html",
        img=user["img"],
        text="",
        num=num,
        egg=egg,
    )


@app.route("/help")
def help() -> str:
    """Render the help page.

    Returns:
        str: Rendered howto.html template with user information.
    """
    user = get_progress()
    return render_template("howto.html", img=user["img"], text=user["text"])


@app.route("/logout")
def logout() -> Response:
    """Log out the user by clearing the session.

    Returns:
        Response: Redirect to the index page.
    """
    session.pop("token", None)
    session.pop("user_data", None)
    data_cache.progress = {}
    return redirect(url_for("index"))


@app.route("/update", methods=["GET", "POST"])
def update() -> str | Response | tuple[str, int]:
    """Render the update page or process update requests.

    Returns:
        str: Rendered update.html template or error response.
        Response: Refreshed endpoint if data missing
        tuple[str, int]: Error message with HTTP status code.
    """
    user = get_progress()
    if (user["id"] or "bad") not in data_cache.permissions:
        return f"Error: No authorization {user['id']}", 400

    if request.method == "GET":
        return render_template("update.html", img=user["img"], text=user["text"], selected=0)
    else:
        if not (week := int(request.form.get('selection'))):
            return redirect(url_for('update'))

        try:
            data = data_cache.html[week]
            a, b, ee = data[1], data[2], data["ee"]
        except KeyError:
            return redirect(url_for("update"))

        params = {
            "img": user["img"],
            "text": user["text"],
            "num": week,
            "selected": week,
            "a": a,
            "b": b,
            "ee": ee,
        }
        return render_template("update.html", **params)


@app.route("/update-db", methods=["POST"])
def update_db() -> Response | tuple[str, int]:
    """Update the database with new data from the form.

    Returns:
        Response: Redirect to the update page with flash messages.
        tuple[str, int]: Error message with HTTP status code.
    """
    user = get_progress()
    if (user["id"] or "bad") not in data_cache.permissions:
        return f"Error: No authorization {user['id']}", 400
    a = {}
    b = {}
    ee = ""
    for k, v in request.form.items():
        if k == "ee":
            ee = v
        elif k.endswith("a"):
            a[k[:-2]] = v
        else:
            b[k[:-2]] = v
    week_num = int(request.form.get("num"))

    data_cache.update_html(week_num, a, b, ee)
    return redirect(url_for("update"))


@app.route("/admin", methods=["GET"])
def admin() -> str | tuple[str, int]:
    """Render the admin page with settings and permissions.

    Returns:
        Response: Rendered admin.html template or error response.
        tuple[str, int]: Error message with HTTP status code.
    """
    user = get_progress()
    permitted = data_cache.permissions[:]
    if (user["id"] or "bad") not in permitted:
        return f"Error: No authorization {user['id']}", 400

    release = data_cache.release
    guild = data_cache.discord_ids["guild"]
    channels = [data_cache.discord_ids[f"{i}"] for i in range(1, 11)]
    permitted.remove("609283782897303554")

    params = {
        "img": user["img"],
        "text": user["text"],
        "guild": guild,
        "channels": channels,
        "release": release,
        "perms": permitted,
    }
    return render_template("admin.html", **params)


@app.route("/update-admin", methods=["POST"])
def update_admin() -> Response | tuple[str, int]:
    """Update admin settings based on form input.

    Returns:
        Response: Redirect to the admin page with flash messages.
        tuple[str, int]: Error message with HTTP status code.
    """
    user = get_progress()
    print("in update admin")
    print(data_cache.permissions)
    if (user["id"] or "bad") not in data_cache.permissions:
        return f"Error: No authorization {user['id']}", 400

    channels = {f"{i}": request.form.get(f"c{i}").strip() for i in range(1, 11)}
    channels["guild"] = request.form.get("guild").strip()
    permitted = [perm for perm in request.form.get("perms").splitlines() if perm]
    try:
        release = min(10, max(1, int(request.form.get("release").strip())))
    except ValueError:
        flash("Invalid release number (must be a number 1 through 10)", "error")
        return redirect(url_for("admin"))

    data_cache.update_constants(channels, permitted, release)

    return redirect(url_for("admin"))


@app.route('/418')
def trigger_418() -> None:
    """Trigger a 418 error for testing purposes.

    Returns:
        Response: Abort with a 404 error.
    """
    abort(404)


@app.errorhandler(404)
def teapot(e: Exception) -> Response:
    """Handle 404 errors and return a custom response.

    Args:
        e: The error that occurred.
    Returns:
        Response: Custom response with a 418 status code and an image.
    """
    response = make_response(send_from_directory("static/images/index", "hmm.png"))
    response.headers["Easter-Egg"] = "TO BE CONTINUED"
    response.status_code = 418
    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
