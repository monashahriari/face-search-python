"""Lightweight face enrollment and search system for roughly 20-30 people."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import face_recognition
import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "faces.db"
SYNC_MINUTES = int(os.getenv("SYNC_MINUTES", "5"))
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.50")) 

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

# Only embeddings are held in RAM for searching; images are stored on disk and in SQLite.
face_cache: dict[int, dict[str, Any]] = {}
cache_lock = threading.RLock()
scheduler = BackgroundScheduler(daemon=True)

#get admin user_name and password
with open("admin_information.json", "r", encoding="utf-8") as file:
    config = json.load(file)

username = config["username"]
password = config["password"]

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 300_000)
    return f"{salt.hex()}${digest.hex()}"


def password_ok(password: str, saved: str) -> bool:
    salt_hex, digest_hex = saved.split("$", 1)
    actual = password_hash(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
    return hmac.compare_digest(actual, digest_hex)


def init_db() -> None:
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_filename TEXT NOT NULL,
            embedding BLOB NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)
        
        
        if conn.execute(
            "SELECT 1 FROM admins WHERE username = ?",
            (username,)
        ).fetchone() is None:

            conn.execute(
                "INSERT INTO admins VALUES (?, ?)",
                (username, password_hash(password))
            )


def reload_cache() -> None:
    """Load all SQLite data into the RAM cache using an atomic cache replacement."""
    with db() as conn:
        rows = conn.execute("SELECT id, name, image_filename, embedding FROM people").fetchall()
    new_cache = {
        row["id"]: {
            "name": row["name"],
            "image_filename": row["image_filename"],
            "embedding": np.frombuffer(row["embedding"], dtype=np.float64),
        }
        for row in rows
    }
    with cache_lock:
        face_cache.clear()
        face_cache.update(new_cache)


def extract_single_encoding(content: bytes) -> np.ndarray:
    """Extract exactly one face from an image to prevent incorrect enrollment."""
    try:
        image = face_recognition.load_image_file(__import__("io").BytesIO(content))
        encodings = face_recognition.face_encodings(image)
    except Exception as exc:
        raise HTTPException(400, "فایل تصویر معتبر نیست یا قابل پردازش نیست.") from exc
    if len(encodings) == 0:
        raise HTTPException(400, "هیچ چهره‌ای در تصویر پیدا نشد.")
    if len(encodings) > 1:
        raise HTTPException(400, "لطفاً تصویری با دقیقاً یک چهره ارسال کنید.")
    return encodings[0]


async def read_image(upload: UploadFile) -> tuple[bytes, str]:
    if upload.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(400, "فقط فایل JPG یا PNG مجاز است.")
    content = await upload.read()
    if not content or len(content) > 8 * 1024 * 1024:
        raise HTTPException(400, "حجم تصویر باید بین ۱ بایت تا ۸ مگابایت باشد.")
    suffix = ".jpg" if upload.content_type == "image/jpeg" else ".png"
    return content, suffix


def logged_in(request: Request) -> bool:
    return request.cookies.get("face_admin") == "1"


def require_admin(request: Request) -> None:
    if not logged_in(request):
        raise HTTPException(401, "ابتدا وارد حساب ادمین شوید.")


def page(title: str, content: str, request: Request) -> HTMLResponse:
    admin_links = "<a href='/admin'>مدیریت</a> <a href='/logout'>خروج</a>" if logged_in(request) else "<a href='/login'>ورود ادمین</a>"
    return HTMLResponse(f"""<!doctype html><html lang='fa' dir='rtl'><head><meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'><title>{title}</title>
    <style>body{{font-family:tahoma,Arial;max-width:820px;margin:35px auto;padding:0 16px;background:#f6f8fb;color:#172033}}nav{{display:flex;gap:16px;margin-bottom:28px}}a{{color:#155eef}}.box{{background:white;border-radius:12px;padding:22px;margin:16px 0;box-shadow:0 1px 4px #0001}}input{{display:block;margin:8px 0 16px;padding:9px;width:min(100%,400px)}}button{{padding:10px 18px;background:#155eef;color:white;border:0;border-radius:7px;cursor:pointer}}img{{max-width:150px;border-radius:8px}}.error{{color:#b42318}}</style></head>
    <body><nav><a href='/'>جست‌وجوی چهره</a>{admin_links}</nav><h1>{title}</h1>{content}</body></html>""")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    reload_cache()
    scheduler.add_job(reload_cache, "interval", minutes=SYNC_MINUTES, id="db_to_memory", replace_existing=True)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Face Search", lifespan=lifespan)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return page("جست‌وجوی چهره", """<div class='box'><p>یک عکس دارای یک چهره بارگذاری کنید.</p>
    <form action='/search' method='post' enctype='multipart/form-data'><input type='file' name='photo' accept='image/jpeg,image/png' required><button>جست‌وجو</button></form></div>""", request)


@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, photo: UploadFile = File(...)):
    content, _ = await read_image(photo)
    query = extract_single_encoding(content)
    with cache_lock:
        candidates = list(face_cache.items())
    if not candidates:
        return page("نتیجه", "<div class='box'>هنوز هیچ چهره‌ای ثبت نشده است.</div>", request)
    person_id, person = min(candidates, key=lambda item: float(np.linalg.norm(item[1]["embedding"] - query)))
    distance = float(np.linalg.norm(person["embedding"] - query))
    if distance > MATCH_THRESHOLD:
        return page("نتیجه", f"<div class='box'>چهره‌ای با اطمینان کافی پیدا نشد. فاصله: {distance:.3f}</div>", request)
    score = max(0, round((1 - distance) * 100))
    body = f"<div class='box'><img src='/uploads/{person['image_filename']}'><h2>{person['name']}</h2><p>شناسه: {person_id} | امتیاز تقریبی: {score}% | فاصله: {distance:.3f}</p></div>"
    return page("چهره پیدا شد", body, request)


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return page("ورود ادمین", """<div class='box'><form action='/login' method='post'><label>نام کاربری</label><input name='username' required><label>رمز عبور</label><input type='password' name='password' required><button>ورود</button></form></div>""", request)


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    with db() as conn:
        row = conn.execute("SELECT password_hash FROM admins WHERE username=?", (username,)).fetchone()
    if not row or not password_ok(password, row["password_hash"]):
        return HTMLResponse("نام کاربری یا رمز عبور نادرست است.", status_code=401)
    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie("face_admin", "1", httponly=True, samesite="lax", secure=False)
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("face_admin")
    return response


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    require_admin(request)
    with cache_lock:
        people = list(face_cache.items())
    rows = "".join(f"<li>{p['name']} — <a href='/uploads/{p['image_filename']}' target='_blank'>عکس</a></li>" for _, p in people) or "<li>موردی ثبت نشده است.</li>"
    content = f"""<div class='box'><h2>افزودن چهره</h2><form action='/admin/enroll' method='post' enctype='multipart/form-data'><label>نام</label><input name='name' maxlength='100' required><label>تصویر (فقط یک چهره)</label><input type='file' name='photo' accept='image/jpeg,image/png' required><button>ثبت فوری</button></form></div><div class='box'><h2>افراد در حافظه: {len(people)}</h2><ul>{rows}</ul></div>"""
    return page("مدیریت چهره‌ها", content, request)


@app.post("/admin/enroll")
async def enroll(request: Request, name: str = Form(...), photo: UploadFile = File(...)):
    require_admin(request)
    name = name.strip()
    if not name:
        raise HTTPException(400, "نام الزامی است.")
    content, suffix = await read_image(photo)
    embedding = extract_single_encoding(content)
    filename = f"{secrets.token_urlsafe(16)}{suffix}"
    # Save to the database first, then the image file, then the cache.
    # This order prevents an incomplete image from being created on a database error.
    now = utcnow()
    with db() as conn:
        cur = conn.execute("INSERT INTO people(name,image_filename,embedding,created_at,updated_at) VALUES(?,?,?,?,?)", (name, filename, embedding.astype(np.float64).tobytes(), now, now))
        person_id = cur.lastrowid
    (UPLOAD_DIR / filename).write_bytes(content)
    with cache_lock:
        face_cache[person_id] = {"name": name, "image_filename": filename, "embedding": embedding}
    return RedirectResponse("/admin", status_code=303)


@app.get("/health")
def health():
    with cache_lock:
        return {"status": "ok", "cached_people": len(face_cache), "sync_minutes": SYNC_MINUTES}
