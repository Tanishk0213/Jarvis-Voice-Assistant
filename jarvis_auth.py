"""
jarvis_auth.py — JARVIS Authentication Manager
Handles user registration, login, session persistence using local JSON files.
"""

import json
import os
import hashlib
from datetime import datetime

USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_users.json")
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_session.json")


def _hash_password(password: str) -> str:
    """SHA-256 hash the password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_users() -> dict:
    """Load all registered users from JSON file."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_users(users: dict) -> None:
    """Persist users dict to JSON file."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def register_user(name: str, email: str, password: str) -> tuple:
    """
    Register a new user.
    Returns (success: bool, message: str)
    """
    name = name.strip()
    email = email.strip().lower()
    if not name or not email or not password:
        return False, "All fields are required."
    if "@" not in email or "." not in email:
        return False, "Enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    users = load_users()
    if email in users:
        return False, "Email already registered. Please login."

    users[email] = {
        "name": name,
        "email": email,
        "password": _hash_password(password),
        "created_at": datetime.now().isoformat(),
    }
    _save_users(users)
    return True, "Registration successful!"


def login_user(email: str, password: str) -> tuple:
    """
    Authenticate a user.
    Returns (success: bool, message: str, name: str)
    """
    email = email.strip().lower()
    users = load_users()

    if email not in users:
        return False, "Email not found. Please register.", ""
    if users[email]["password"] != _hash_password(password):
        return False, "Incorrect password. Try again.", ""

    name = users[email]["name"]
    _save_session(email, name)
    return True, "Login successful!", name


def _save_session(email: str, name: str) -> None:
    """Persist login session to JSON file."""
    session = {
        "email": email,
        "name": name,
        "logged_in": True,
        "login_time": datetime.now().isoformat(),
    }
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)


def load_session() -> dict:
    """Load current session. Returns empty dict if no session exists."""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def is_logged_in() -> tuple:
    """
    Check if a user is already logged in.
    Returns (logged_in: bool, name: str)
    """
    session = load_session()
    if session.get("logged_in") and session.get("name"):
        return True, session["name"]
    return False, ""


def logout() -> None:
    """Clear the current session."""
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
        except OSError:
            pass
