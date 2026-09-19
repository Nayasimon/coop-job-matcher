"""SQLite storage with additive migrations for existing posting databases."""
import math
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from src.demo_context import CURRENT

DB_PATH = Path(os.getenv('COOP_DB_PATH', Path(__file__).resolve().parent.parent / 'data' / 'postings.db'))
STATUSES = ['Not Applied', 'Applied', 'Interview', 'Rejected', 'Offer']


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connection():
    session = CURRENT.get()
    if session is not None:
        with session['lock'], session['connection']:
            yield session['connection']
        return
    conn = get_connection()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db():
    with connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS postings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            company TEXT NOT NULL, description TEXT NOT NULL, deadline TEXT,
            link TEXT, date_added TEXT NOT NULL, score INTEGER, matching_skills TEXT,
            gaps TEXT, reasoning TEXT, status TEXT DEFAULT 'Not Applied')''')
        columns = {r['name'] for r in conn.execute('PRAGMA table_info(postings)')}
        for name, definition in {'notes': "TEXT DEFAULT ''", 'score_source': 'TEXT', 'scored_at': 'TEXT', 'updated_at': 'TEXT'}.items():
            if name not in columns:
                conn.execute(f'ALTER TABLE postings ADD COLUMN {name} {definition}')


def validate_posting(title, company, description, deadline=None, link=None):
    values = [title.strip(), company.strip(), description.strip()]
    if not all(values):
        raise ValueError('Title, company, and posting text are required.')
    deadline, link = (deadline or '').strip(), (link or '').strip()
    if deadline:
        try:
            if date.fromisoformat(deadline).isoformat() != deadline:
                raise ValueError()
        except ValueError:
            raise ValueError('Deadline must use YYYY-MM-DD.') from None
    if link and (urlparse(link).scheme not in ('http', 'https') or not urlparse(link).netloc):
        raise ValueError('Posting link must be a valid http:// or https:// URL.')
    return (*values, deadline, link)


def add_posting(title, company, description, deadline=None, link=None):
    values = validate_posting(title, company, description, deadline, link)
    with connection() as conn:
        cursor = conn.execute('INSERT INTO postings (title, company, description, deadline, link, date_added) VALUES (?, ?, ?, ?, ?, ?)', (*values, datetime.now().isoformat()))
        return cursor.lastrowid


def update_posting(posting_id, title, company, description, deadline=None, link=None):
    values = validate_posting(title, company, description, deadline, link)
    with connection() as conn:
        old = conn.execute('SELECT * FROM postings WHERE id = ?', (posting_id,)).fetchone()
        if old is None:
            raise ValueError('Posting no longer exists.')
        if any(old[key] != val for key, val in zip(('title', 'company', 'description'), values[:3])):
            conn.execute('UPDATE postings SET score=NULL, matching_skills=NULL, gaps=NULL, reasoning=NULL, score_source=NULL, scored_at=NULL WHERE id=?', (posting_id,))
        conn.execute('UPDATE postings SET title=?, company=?, description=?, deadline=?, link=?, updated_at=? WHERE id=?', (*values, datetime.now().isoformat(), posting_id))


def get_all_postings():
    with connection() as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM postings ORDER BY score DESC, id DESC')]


def get_unscored_postings():
    return [p for p in get_all_postings() if p['score'] is None]


def save_score(posting_id, score, matching_skills, gaps, reasoning, score_source='unknown'):
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 100:
        raise ValueError('Score must be between 0 and 100.')
    with connection() as conn:
        conn.execute('UPDATE postings SET score=?, matching_skills=?, gaps=?, reasoning=?, score_source=?, scored_at=? WHERE id=?', (round(score), matching_skills, gaps, reasoning, score_source, datetime.now().isoformat(), posting_id))


def update_status(posting_id, status, notes=None):
    if status not in STATUSES:
        raise ValueError('Unknown application status.')
    with connection() as conn:
        conn.execute('UPDATE postings SET status=?, notes=COALESCE(?, notes), updated_at=? WHERE id=?', (status, notes, datetime.now().isoformat(), posting_id))


def delete_posting(posting_id):
    with connection() as conn:
        conn.execute('DELETE FROM postings WHERE id=?', (posting_id,))
