import hashlib
import os
import secrets
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

SECRET = os.environ.get("POCKETDOC_SECRET", "pocketdoc-dev-secret-change-me")
ALGO = "HS256"
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    test = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return secrets.compare_digest(test, digest)


def make_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(days=14),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def user_from_token(db: Session, raw: str) -> User:
    try:
        payload = jwt.decode(raw, SECRET, algorithms=[ALGO])
        user_id = int(payload["sub"])
    except Exception as exc:
        raise HTTPException(401, "Please sign in again") from exc
    user = db.get(User, user_id)
    if not user or not user.active or user.removed:
        raise HTTPException(401, "This account is not active")
    return user


def get_current(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(401, "Please sign in")
    return user_from_token(db, creds.credentials)


def optional_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    if not creds:
        return None
    try:
        return user_from_token(db, creds.credentials)
    except HTTPException:
        return None


def require(*roles: str):
    def dependency(user: User = Depends(get_current)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "You do not have access to this")
        return user

    return dependency
