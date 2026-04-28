from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

# ───────────────────────────────
# CORS
# ───────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────────────────
# CONFIG
# ───────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "qa_cache.db")

print("📦 DATABASE PATH:", DB_PATH)

# ───────────────────────────────
# REQUEST MODEL
# ───────────────────────────────
class RequestData(BaseModel):
    text: str

# ───────────────────────────────
# DATABASE
# ───────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS qa_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                hit_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

init_db()

# ───────────────────────────────
# SAVE CACHE
# ───────────────────────────────
def save_cache(question, answer):
    print("💾 SAVING TO DB:", question)

    with get_db() as conn:
        conn.execute(
            "INSERT INTO qa_cache (question, answer) VALUES (?, ?)",
            (question, answer),
        )
        conn.commit()

    print("✅ SAVED SUCCESSFULLY")

# ───────────────────────────────
# FIND CACHE
# ───────────────────────────────
def find_cache(question):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM qa_cache").fetchall()

    question = question.lower()

    for r in rows:
        if question in r["question"].lower():
            print("⚡ CACHE HIT:", r["question"])
            return r

    return None

# ───────────────────────────────
# UPDATE HIT COUNT
# ───────────────────────────────
def update_hit(id):
    with get_db() as conn:
        conn.execute(
            "UPDATE qa_cache SET hit_count = hit_count + 1 WHERE id = ?",
            (id,),
        )
        conn.commit()

# ───────────────────────────────
# CLAUDE CALL (OPTIONAL)
# ───────────────────────────────
def ask_claude(text: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    msg = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=300,
        messages=[{"role": "user", "content": text}],
    )

    return msg.content[0].text.strip()

# ───────────────────────────────
# SMART ENGINE (FIXED)
# ───────────────────────────────
def generate_response(text: str):

    # 1️⃣ CACHE FIRST
    cached = find_cache(text)
    if cached:
        update_hit(cached["id"])
        return cached["answer"], "cache"

    answer = None
    source = None

    # 2️⃣ CLAUDE (IF KEY EXISTS)
    if ANTHROPIC_API_KEY:
        try:
            answer = ask_claude(text)
            source = "claude"
        except Exception as e:
            print("❌ Claude error:", e)

    # 3️⃣ FALLBACK (ALWAYS WORKS)
    if answer is None:
        t = text.lower()

        if "hello" in t:
            answer = "Hello 👋 (fallback mode)"
        elif "how are you" in t:
            answer = "I'm good 🤖 (fallback mode)"
        else:
            answer = f"You said: {text} (fallback mode)"

        source = "fallback"

    # 🔥 IMPORTANT: ALWAYS SAVE
    save_cache(text, answer)

    return answer, source

# ───────────────────────────────
# API ENDPOINT
# ───────────────────────────────
@app.post("/process")
def process(req: RequestData):

    print("🎤 RECEIVED:", req.text)

    response, source = generate_response(req.text)

    print("🤖 RESPONSE:", response)
    print("📌 SOURCE:", source)

    return {
        "response": response,
        "source": source
    }

# ───────────────────────────────
# HEALTH CHECK
# ───────────────────────────────
@app.get("/")
def home():
    return {
        "status": "Voice AI Backend Running 🚀",
        "mode": "Claude ON" if ANTHROPIC_API_KEY else "Fallback Mode"
    }

# ───────────────────────────────
# VIEW CACHE
# ───────────────────────────────
@app.get("/cache")
def cache():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM qa_cache ORDER BY id DESC").fetchall()

    print("📊 CACHE SIZE:", len(rows))

    return [dict(r) for r in rows]

# ───────────────────────────────
# DELETE CACHE (OPTIONAL)
# ───────────────────────────────
@app.delete("/cache/{id}")
def delete_cache(id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM qa_cache WHERE id=?", (id,))
        conn.commit()

    return {"deleted": id}