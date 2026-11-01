
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash

router = APIRouter(prefix="/auth", tags=["Authentication"])

DB_PATH = Path(__file__).resolve().parent / "users.db"
password_hash = PasswordHash.recommended()

SECRET_KEY = os.environ.get("SIGNGUARD_JWT_SECRET")

if not SECRET_KEY:
    raise RuntimeError(
        "Set SIGNGUARD_JWT_SECRET before starting FastAPI."
    )

ALGORITHM = "HS256"


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)


init_db()


def create_token(user_id):
    expiry = datetime.now(timezone.utc) + timedelta(hours=2)

    return jwt.encode(
        {"sub": str(user_id), "exp": expiry},
        SECRET_KEY,
        algorithm=ALGORITHM
    )


@router.post("/register", status_code=201)
def register(data: RegisterRequest):
    email = str(data.email).lower().strip()

    with get_db() as db:
        existing = db.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Email already registered"
            )

        hashed = password_hash.hash(data.password)

        try:
            cursor = db.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (data.name.strip(), email, hashed)
            )
            db.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail="Email already registered"
            )

        user_id = cursor.lastrowid

    return {
        "message": "Account created successfully",
        "access_token": create_token(user_id),
        "token_type": "bearer",
        "name": data.name.strip()
    }


@router.post("/login")
def login(data: LoginRequest):
    email = str(data.email).lower().strip()

    with get_db() as db:
        user = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

    if not user or not password_hash.verify(
        data.password, user["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "message": "Login successful",
        "access_token": create_token(user["id"]),
        "token_type": "bearer",
        "name": user["name"]
    }

# Verify JWT tokens for protected API endpoints

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

        with get_db() as db:
            user = db.execute(
                "SELECT id, name, email FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User account not found"
            )

        return dict(user)

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
