from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import anthropic
import re
import os

app = FastAPI()

# ── CORS (allow frontend to call backend) ──────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ─────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY    = os.getenv("ANTHROPIC_API_KEY", "YOUR_API_KEY_HERE")
SIMILARITY_THRESHOLD = 0.40   # 40% word overlap triggers a cache hit
DB_PATH              = "qa_cache.db"

# ── Request model ──────────────────────────────────────────────────────────────
class RequestData(BaseModel):
    text: str

# ── Database setup ─────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS qa_cache (
                id         INTEGER  PRIMARY KEY AUTOINCREMENT,
                question   TEXT     NOT NULL,
                answer     TEXT     NOT NULL,
                hit_count  INTEGER  DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

init_db()   # runs once when the server starts

# ── Similarity helpers ─────────────────────────────────────────────────────────
def tokenize(text: str) -> set:
    """Lowercase, strip punctuation, return word-token set."""
    return set(re.sub(r"[^a-z0-9\s]", "", text.lower()).split())

def jaccard_similarity(a: str, b: str) -> float:
    """Overlap between two questions as a 0-1 score."""
    set_a, set_b = tokenize(a), tokenize(b)
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    return len(set_a & set_b) / len(union) if union else 0.0

def find_best_match(question: str):
    """
    Scan the DB and return (row, score) if the best match
    exceeds SIMILARITY_THRESHOLD, otherwise (None, 0).
    """
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, question, answer FROM qa_cache"
        ).fetchall()

    best_row, best_score = None, 0.0
    for row in rows:
        score = jaccard_similarity(question, row["question"])
        if score > best_score:
            best_score, best_row = score, row

    if best_score >= SIMILARITY_THRESHOLD:
        return best_row, best_score
    return None, 0.0

def save_to_db(question: str, answer: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO qa_cache (question, answer) VALUES (?, ?)",
            (question, answer),
        )
        conn.commit()

def increment_hit(row_id: int):
    with get_db() as conn:
        conn.execute(
            "UPDATE qa_cache SET hit_count = hit_count + 1 WHERE id = ?",
            (row_id,),
        )
        conn.commit()

# ── Claude API call ────────────────────────────────────────────────────────────
def ask_claude(question: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=(
            "You are a helpful voice assistant. "
            "Answer questions clearly and concisely in 1-3 sentences."
        ),
        messages=[{"role": "user", "content": question}],
    )
    return message.content[0].text.strip()

# ── Root test route ────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "Voice AI Backend is running 🚀"}

# ── Voice processing route ─────────────────────────────────────────────────────
@app.post("/process")
def process(req: RequestData):
    question = req.text.strip()

    # 1️⃣  Check the database first
    match, score = find_best_match(question)
    if match:
        increment_hit(match["id"])
        return {
            "response":         match["answer"],
            "source":           "cache",
            "matched_question": match["question"],
            "similarity":       round(score * 100, 1),  # e.g. 87.5
        }

    # 2️⃣  Cache miss → ask Claude, then save for next time
    answer = ask_claude(question)
    save_to_db(question, answer)

    return {
        "response": answer,
        "source":   "claude",
    }

# ── Optional: view all saved Q&A pairs ────────────────────────────────────────
@app.get("/cache")
def get_cache():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, question, answer, hit_count, created_at "
            "FROM qa_cache ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]

# ── Optional: delete one cache entry ──────────────────────────────────────────
@app.delete("/cache/{entry_id}")
def delete_entry(entry_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM qa_cache WHERE id = ?", (entry_id,))
        conn.commit()
    return {"deleted": entry_id}