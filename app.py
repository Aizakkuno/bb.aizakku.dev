import os

from flask import Flask
from dotenv import load_dotenv

from tools import headers_key, get_http_error

load_dotenv()

INVITE_SECRET = os.getenv("INVITE_SECRET")

app = Flask(__name__)

@app.route("/api/invite/create", methods=["POST"])
@headers_key("invite_secret", 64, 64)
def api_invite_create(invite_secret):
    if invite_secret != INVITE_SECRET:
        return get_http_error("invalid_invite_secret")

if __name__ == "__main__":
    app.run()