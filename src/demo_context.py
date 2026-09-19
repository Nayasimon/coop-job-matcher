"""Per-session demo storage, never shared through mutable module globals."""
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
import sqlite3
from threading import RLock

CURRENT = ContextVar('coop_demo_session', default=None)
SAMPLE_PROFILE = {
    'name': 'Alex (fictional demo candidate)',
    'skills': ['Python', 'C++', 'SolidWorks', 'SQLite', 'Git', 'Data analysis'],
    'education': 'Engineering student at Example University',
    'experience': [{'role': 'Student lab assistant', 'company': 'Example University', 'description': 'Collected test data and automated reports with Python.'}],
    'projects': [{'name': 'Robotics project', 'description': 'Designed a chassis in SolidWorks and programmed a C++ controller.'}],
}


def new_session():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return {'connection': conn, 'lock': RLock(), 'profile': deepcopy(SAMPLE_PROFILE)}


@contextmanager
def activate(session):
    token = CURRENT.set(session)
    try:
        yield
    finally:
        CURRENT.reset(token)


def is_demo():
    return CURRENT.get() is not None
