import random
import string

from flask import request
from functools import wraps
from database import db

errors = {
    "bad_request": {"text": "Bad request!",
                    "error": "bad_request",
                    "status": 400},

    "unspecified": {"text": "Please specify a value for '{}'!",
                    "error": "{}_unspecified",
                    "status": 400},
        
    "bad_type": {"text": "Value for '{}' must be type {}",
                 "error": "{}_bad_type",
                 "status": 400},

    "out_of_range": {"text": ("Value for '{}' must be between {} and {} "
                              "characters!"),
                    "error": "{}_out_of_range",
                    "status": 400},

    "not_printable": {"text": "Value for '{}' uses invalid characters!",
                      "error": "{}_not_printable",
                      "status": 400},

    "blocked_keywords": {"text": "Value for '{}' uses blocked keywords!",
                         "error": "{}_blocked_keywords",
                         "status": 400},

    "exists": {"text": "Value for '{}' already exists/is taken!",
               "error": "{}_exists",
               "status": 409},

    # change to invalid template in future which uses args
    "invalid": {"text": "Value for '{}' does not exist!",
                "error": "{}_invalid",
                "status": 404},

    "invalid_auth": {"text": ("Value for '{}' does not exist or could not be "
                              "used to authenticate you!"),
                    "error": "{}_invalid_auth",
                    "status": 401},

    "creation_ratelimit": {"text": ("You must wait {} minutes before "
                                    "creating a new {}!"),
                           "error": "{}_creation_ratelimit",
                           "status": 429},

    "invalid_discord_url": {"text": ("Discord URL must start with "
                                     "'https://discord.gg/' or "
                                     "'https://discord.com/invite/!'"),
                            "error": "invalid_discord_url",
                            "status": 400}
}


def format_json_template(response, *args):
    for field in response.keys():
        field = field.format(*args)

    return response


def get_http_error(code, *args):
    response = format_json_template(errors[code], *args)
    status = response["status"]

    response.pop("status")

    return response, status


def generate_token():
    return "".join(random.choices(string.ascii_letters + string.digits, k=64))


def generate_invite_token():
    token = generate_token()
    while db.invites.find_one({"token": token}):
        token = generate_token()

    return token


def generate_code():
    return "".join(random.choices(string.ascii_letters + string.digits, k=6))


def generate_invite_code():
    code = generate_code()
    while db.invites.find_one({"code": code}):
        code = generate_code()

    return code


def json_key(key,
             min: int = 1,
             max: int = 4096,
             var_type: type = str,
             required: bool = True,
             printable: bool = True):

    def wrapper(f):
        @wraps(f)
        def wrapper_function(*args, **kwargs):
            if request.json:
                value = request.json.get(key)
                if not value and required:
                    return get_http_error("unspecified", key)
                elif not required:
                    value = value or None
            else:
                if required:
                    return get_http_error("bad_request")
                else:
                    value = None

            if value:
                if not isinstance(value, var_type):
                    try:
                        value = var_type(value)
                    except ValueError:
                        return get_http_error("bad_type", key, var_type)

                if len(str(value)) < min or len(str(value)) > max:
                    return get_http_error("out_of_range", key, min, max)

                if printable and isinstance(value, str):
                    for chr in value:
                        if chr not in string.printable:
                            return get_http_error("not_printable", key)

            return f(**{key: value}, **kwargs)
        return wrapper_function
    return wrapper


def headers_key(key,
                min: int = 1,
                max: int = 4096,
                var_type: type = str,
                required: bool = True,
                printable: bool = True):

    def wrapper(f):
        @wraps(f)
        def wrapper_function(*args, **kwargs):
            if request.json:
                value = request.headers.get(key)
                if not value and required:
                    return get_http_error("unspecified", key)
                elif not required:
                    value = value or None
            else:
                if required:
                    return get_http_error("bad_request")
                else:
                    value = None

            if value:
                if not isinstance(value, var_type):
                    try:
                        value = var_type(value)
                    except ValueError:
                        return get_http_error("bad_type", key, var_type)

                if len(str(value)) < min or len(str(value)) > max:
                    return get_http_error("out_of_range", key, min, max)

                if printable and isinstance(value, str):
                    for chr in value:
                        if chr not in string.printable:
                            return get_http_error("not_printable", key)

            return f(**{key: value}, **kwargs)
        return wrapper_function
    return wrapper
