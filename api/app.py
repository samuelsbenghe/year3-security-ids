import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, constr

DATABASE = os.getenv("DATABASE_PATH", "/app/data/ids.db")
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 2


def get_db():
    database_dir = os.path.dirname(os.path.abspath(DATABASE))
    os.makedirs(database_dir, exist_ok=True)

    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row

    return db


def init_db():
    db = get_db()

    try:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        db.commit()

    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="IDS API",
    description="Backend API for the IDS social network",
    version="1.0.0",
    lifespan=lifespan,
)

hasher = PasswordHasher()
security = HTTPBearer()


class RegisterRequest(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class NoteRequest(BaseModel):
    content: constr(strip_whitespace=True, min_length=1, max_length=2000)


def create_token(user):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_EXPIRY_HOURS),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )

        return payload

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/users/register", status_code=201)
def register(data: RegisterRequest):
    db = get_db()

    try:
        password_hash = hasher.hash(data.password)

        db.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
            """,
            (data.username.strip(), password_hash),
        )

        db.commit()

        return {"message": "Account created"}

    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already exists")

    finally:
        db.close()


@app.post("/users/login")
def login(data: LoginRequest):
    db = get_db()

    try:
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (data.username.strip(),)
        ).fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        try:
            hasher.verify(user["password_hash"], data.password)
        except (VerificationError, InvalidHashError):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_token(user)

        return {
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "username": user["username"],
        }  # type: ignore

    finally:
        db.close()


@app.get("/notes")
def get_notes(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=10),
):
    db = get_db()

    try:
        total = db.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        offset = (page - 1) * per_page
        notes = db.execute(
            """
            SELECT id, username, content, created_at
            FROM notes
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """,
            (per_page, offset),
        ).fetchall()

        return {
            "notes": [dict(note) for note in notes],
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
            "has_previous": page > 1,
            "has_next": offset + len(notes) < total,
        }  # type: ignore

    finally:
        db.close()


@app.post("/notes", status_code=201)
def create_note(data: NoteRequest, user=Depends(require_auth)):
    db = get_db()

    try:
        db.execute(
            """
            INSERT INTO notes (username, content)
            VALUES (?, ?)
            """,
            (user["username"], data.content.strip()),
        )

        db.commit()

        return {"message": "Note created"}

    finally:
        db.close()
