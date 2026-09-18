"""
Database layer for the co-op job matcher.
Uses SQLite for zero-setup local storage.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "postings.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist yet. Safe to call every startup."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS postings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            description TEXT NOT NULL,
            deadline TEXT,
            link TEXT,
            date_added TEXT NOT NULL,
            score INTEGER,
            matching_skills TEXT,
            gaps TEXT,
            reasoning TEXT,
            status TEXT DEFAULT 'Not Applied'
        )
    """)
    conn.commit()
    conn.close()


def add_posting(title, company, description, deadline=None, link=None):
    conn = get_connection()
    conn.execute(
        """INSERT INTO postings (title, company, description, deadline, link, date_added)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (title, company, description, deadline, link, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_all_postings():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM postings ORDER BY score DESC NULLS LAST").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_unscored_postings():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM postings WHERE score IS NULL").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_score(posting_id, score, matching_skills, gaps, reasoning):
    conn = get_connection()
    conn.execute(
        """UPDATE postings SET score = ?, matching_skills = ?, gaps = ?, reasoning = ?
           WHERE id = ?""",
        (score, matching_skills, gaps, reasoning, posting_id),
    )
    conn.commit()
    conn.close()


def update_status(posting_id, status):
    conn = get_connection()
    conn.execute("UPDATE postings SET status = ? WHERE id = ?", (status, posting_id))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Quick manual test — run `python src/db.py` to sanity check the schema
    init_db()
    add_posting(
        title="Test Mechatronics Co-op",
        company="Example Corp",
        description="Looking for a mechatronics student with Python and controls experience.",
        deadline="2026-10-01",
        link="https://example.com/job/123",
    )
    print(get_all_postings())
