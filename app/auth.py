import os
import time
import hmac
import hashlib
import secrets
from dotenv import load_dotenv
from .models import User

load_dotenv()

SECRET = os.getenv("SECRET_KEY", "dev-secret-change-me").encode()
COOKIE = "fb_session"
MAX_AGE = 7 * 24 * 3600


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$")
    except ValueError:
        return False
    calc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return hmac.compare_digest(calc, digest)


def _sign(value: str) -> str:
    return hmac.new(SECRET, value.encode(), hashlib.sha256).hexdigest()


def make_token(uid: int) -> str:
    value = f"{uid}:{int(time.time()) + MAX_AGE}"
    return f"{value}:{_sign(value)}"


def read_token(token: str):
    parts = token.split(":")
    if len(parts) != 3:
        return None
    uid, exp, sig = parts
    if not hmac.compare_digest(sig, _sign(f"{uid}:{exp}")):
        return None
    if not exp.isdigit() or int(exp) < time.time() or not uid.isdigit():
        return None
    return int(uid)


def get_current_user(request, db):
    token = request.cookies.get(COOKIE)
    uid = read_token(token) if token else None
    return db.query(User).filter(User.id == uid).first() if uid else None


def set_login_cookie(response, uid: int):
    response.set_cookie(COOKIE, make_token(uid), max_age=MAX_AGE, httponly=True, samesite="lax")
