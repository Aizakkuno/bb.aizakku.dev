import os
import math
import string
import time

from flask import Flask, request
from dotenv import load_dotenv
from database import db

from tools import json_key, headers_key, get_http_error, generate_invite_token
from tools import generate_invite_code

load_dotenv()

app = Flask(__name__)

blocked_keywords = ["api"]
vanity_ratelimit = []

@app.route("/api/invite/create", methods=["POST"])
@json_key("discord_url")
@json_key("invite_code", 4, 20, required=False)
def api_invite_create(discord_url, invite_code):
    if (not discord_url.startswith("https://discord.gg/")
        or discord_url.startswith("https://discord.com/invite/")):

        return get_http_error("invalid_discord_url")

    discord_code = discord_url.replace("https://discord.gg/", "")
    discord_code = discord_code.replace("https://discord.com/invite/", "")

    for char in discord_code:
        if char not in string.ascii_letters + string.digits:
            return get_http_error("not_printable", "discord_url")

    if invite_code:
        for ratelimited in vanity_ratelimit:
            if ratelimited["ip"] == request.remote_addr:
                remaining_seconds = ratelimited["expiry"] - int(time.time())
                remaining_mins = math.ceil(remaining_seconds / 60)

                return get_http_error("creation_ratelimit",
                                      remaining_mins,
                                      "vanity")

        for char in invite_code:
            if char not in string.ascii_letters + string.digits:
                return get_http_error("not_printable", "invite_code")
            
        if blocked_keywords in invite_code:
            return get_http_error("blocked_keywords", "invite_code")
        
        if db.invites.find_one({"code": invite_code}):
            return get_http_error("exists", "invite_code")
        
        vanity_ratelimit.append({"ip": request.remote_addr,
                                 "expiry": int(time.time())})
    else:
        invite_code = generate_invite_code()

    invite_token = generate_invite_token()



if __name__ == "__main__":
    app.run()