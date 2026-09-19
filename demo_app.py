"""Public entry point: temporary session-only data, fictional resume, no API calls."""
from datetime import date, timedelta
from pathlib import Path
import runpy
import streamlit as st
from src import db
from src.demo_context import activate, new_session

if '_demo_session' not in st.session_state:
    session = new_session()
    with activate(session):
        db.init_db()
        samples = [
            ('Software Engineering Co-op', 'Maple Labs (fictional)', 'Build internal tools using Python, SQLite, and Git. Collaborate on code reviews and automate data analysis.', 3),
            ('Mechanical Design Co-op', 'Northstar Robotics (fictional)', 'Design robotic assemblies in SolidWorks, prototype mechanisms, and work with C++ controls engineers.', 7),
            ('Marketing Analytics Intern', 'Harbour Studio (fictional)', 'Analyze campaign performance using Excel, SQL, and Tableau. Present findings and plan marketing experiments.', 14),
        ]
        for title, company, description, days in samples:
            db.add_posting(title, company, description, (date.today() + timedelta(days=days)).isoformat())
    st.session_state['_demo_session'] = session

with activate(st.session_state['_demo_session']):
    runpy.run_path(str(Path(__file__).with_name('app.py')), run_name='__coop_demo__')
