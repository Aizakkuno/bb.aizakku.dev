import os
import math
import string
import time

from flask import Flask, request, redirect
from dotenv import load_dotenv
from database import db

from tools import json_key, headers_key, get_http_error, generate_invite_token
from tools import generate_invite_code, validate_key

load_dotenv()

BOT_SECRET = os.getenv("BOT_SECRET")

app = Flask(__name__)

blocked_keywords = ["api"]
vanity_ratelimit = []

@app.route("/<string:code>")
def redirect_code(code):
    error = validate_key(code, "code")
    if error is not True:
        return redirect("/")

    db_invite = db.invites.find_one({"code": code})
    if not db_invite:
        return redirect("/")

    return redirect(db_invite["url"])


@app.route("/api/invite/create", methods=["POST"])
@json_key("discord_url")
@json_key("invite_code", 4, 20, required=False)
@json_key("bot_secret", 64, 64, required=False)
def api_invite_create(discord_url, invite_code, bot_secret):
    if not discord_url.startswith("https://"):
        discord_url = "https://" + discord_url

    if (not discord_url.startswith("https://discord.gg/")
        or discord_url.startswith("https://discord.com/invite/")):

        return get_http_error("invalid_discord_url")

    discord_code = discord_url.replace("https://discord.gg/", "")
    discord_code = discord_code.replace("https://discord.com/invite/", "")

    for char in discord_code:
        if char not in string.ascii_letters + string.digits:
            return get_http_error("not_printable", "discord_url")

    if invite_code:
        if bot_secret != BOT_SECRET:
            if db.invites.find_one({"url": discord_url,
                                    "ip": request.remote_addr}):
                
                return get_http_error("invite_limit")

            for ratelimited in vanity_ratelimit:
                if ratelimited["ip"] == request.remote_addr:
                    timestamp = int(time.time())
                    remaining_seconds = ratelimited["expiry"] - timestamp
                    remaining_mins = math.ceil(remaining_seconds / 60)

                    return get_http_error("creation_ratelimit",
                                          "vanity",
                                          remaining_mins)

        for char in invite_code:
            if char not in string.ascii_letters + string.digits:
                return get_http_error("not_printable", "invite_code")
            
        for keyword in blocked_keywords:
            if keyword in invite_code.lower():
                return get_http_error("blocked_keywords", "invite_code")
        
        if db.invites.find_one({"code": invite_code}):
            return get_http_error("exists", "invite_code")
        
        if bot_secret != bot_secret:
            vanity_ratelimit.append({"ip": request.remote_addr,
                                    "expiry": int(time.time()) + 3600})
    else:
        invite_code = generate_invite_code()

    invite_token = generate_invite_token()

    db.invites.insert_one({"code": invite_code,
                           "token": invite_token,
                           "url": discord_url,
                           "ip": request.remote_addr})
    
    return {"text": "Created new invite!",
            "token": invite_token,
            "code": invite_code}, 200


@app.route("/api/invite/update", methods=["POST"])
@json_key("invite_token", 64, 64)
@json_key("discord_url")
@json_key("invite_code", 4, 20, required=False)
@json_key("bot_secret", 64, 64, required=False)
def api_invite_update(invite_token, discord_url, invite_code, bot_secret):
    if not db.invites.find_one({"token": invite_token}):
        return get_http_error("invalid_auth", "invite_token")

    if not discord_url.startswith("https://"):
        discord_url = "https://" + discord_url

    if (not discord_url.startswith("https://discord.gg/")
        or discord_url.startswith("https://discord.com/invite/")):

        return get_http_error("invalid_discord_url")

    discord_code = discord_url.replace("https://discord.gg/", "")
    discord_code = discord_code.replace("https://discord.com/invite/", "")

    for char in discord_code:
        if char not in string.ascii_letters + string.digits:
            return get_http_error("not_printable", "discord_url")
        
    document = {"url": discord_url}

    if invite_code:
        if bot_secret != BOT_SECRET:
            for ratelimited in vanity_ratelimit:
                if ratelimited["ip"] == request.remote_addr:
                    timestamp = int(time.time())
                    remaining_seconds = ratelimited["expiry"] - timestamp
                    remaining_mins = math.ceil(remaining_seconds / 60)

                    return get_http_error("creation_ratelimit",
                                          "vanity",
                                          remaining_mins)

        for char in invite_code:
            if char not in string.ascii_letters + string.digits:
                return get_http_error("not_printable", "invite_code")
            
        for keyword in blocked_keywords:
            if keyword in invite_code.lower():
                return get_http_error("blocked_keywords", "invite_code")
        
        if db.invites.find_one({"code": invite_code}):
            return get_http_error("exists", "invite_code")
        
        document["code"] = invite_code
        
        if bot_secret != bot_secret:
            vanity_ratelimit.append({"ip": request.remote_addr,
                                    "expiry": int(time.time()) + 3600})

    db.invites.update_one({"token": invite_token}, {"$set": document})
    
    return {"text": "Updated invite!",
            "url": discord_url,
            "code": invite_code}, 200


if __name__ == "__main__":
    app.run()