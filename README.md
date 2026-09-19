# Co-op Job Matcher

A local Streamlit app for comparing co-op postings with your resume and tracking applications. Your existing SQLite database and resume stay in `data/`.

## Interactive public demo

Deploy **`demo_app.py`**, not `app.py`, on Streamlit Community Cloud. Each visitor gets a separate in-memory SQLite database, a fictional resume, and three sample jobs. Try scoring, editing, adding jobs, notes, status tracking, CSV export, and the Reset demo button. Reloading or ending the session can discard changes.

The demo forces offline scoring even if an API key exists on the server. It never accesses the personal database or writes a resume file. No secrets or paid services are needed. Use fictional text in the public demo.

Run locally with `python -m streamlit run demo_app.py`. The regular `app.py` entry point remains the personal, persistent application with optional Claude scoring.

### Cloud deployment

1. Sign in at https://share.streamlit.io/ with the GitHub account owning this repository.
2. Create an app from `Nayasimon/coop-job-matcher`, branch `main`, main file `demo_app.py`.
3. Select Python 3.12 in Advanced settings; leave Secrets empty, then deploy.
4. Test scoring and Reset demo, then copy the resulting `.streamlit.app` URL into the GitHub repository website field.

Your personal `data/resume_profile.json`, databases, and `.env` are excluded from new commits. A fictional `data/resume_profile.example.json` is included as the default for fresh local installations. Previously committed files can remain in Git history; ignoring a file does not remove historical commits.

## Run on this computer

From this project folder in PowerShell:

```powershell
.\start.ps1
```

Open http://localhost:8501. Use `-Port 8502` if that port is occupied. The launcher prefers the project virtual environment; on this recovered computer it can use the installed Codex Python runtime with the existing dependencies because the original Python installation is missing.

## Fresh setup (Python 3.11 or newer)

Create a new environment if the recovered `.venv` is broken:

```powershell
py -m venv .venv-new
.\.venv-new\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-new\Scripts\python.exe -m streamlit run app.py
```

On macOS/Linux, use `python3 -m venv .venv-new` and `.venv-new/bin/python` for the subsequent commands. A normal working `.venv` also works. Dependencies are constrained to compatible major versions, not fully locked.

Offline matching requires no account. To enable Claude, copy `.env.example` to `.env` **only if you do not already have a .env**, set `ANTHROPIC_API_KEY`, and restart. `ANTHROPIC_MODEL` defaults to `claude-sonnet-5`; it can be changed to a model available to your account. Model reference: https://platform.claude.com/docs/en/models/overview.

## Use

1. Review the **Resume** tab. Save a JSON object with a non-empty `skills` list; include education, projects, and experience for AI scoring.
2. In **Add posting**, enter title, company, description, and optional deadline/link. Dates use `YYYY-MM-DD`.
3. Choose **Offline skill overlap** or **Claude AI** in the sidebar. Claude sends the resume and selected posting to Anthropic and incurs API charges. Offline scores report the percentage of listed resume skills mentioned, not hiring probability. Different methods are labeled and should not be compared directly.
4. Score individual postings or a limited batch of unscored filtered results. Failed requests keep earlier scores intact and report a retryable error. Rescore individual postings after changing the resume or to replace a legacy/offline result with Claude.
5. Save application status and notes. Search, filter, sort, check deadline alerts, and export the visible results to CSV. Edit postings or explicitly confirm deletion. Editing job content clears its outdated score; updating a resume preserves historical scores until you rescore.

## Data and recovery

- `data/postings.db`: postings, tracking, and assessments. Existing databases receive additive schema migrations without replacing rows. Older scores have an unknown source because that metadata was not previously recorded.
- `data/resume_profile.json`: your editable profile. Paths resolve relative to the project, independent of the terminal's working directory.
- `.env`: local API settings; excluded from Git. Never commit keys or a shared database containing personal information.
- Back up the database and profile before moving computers. SQLite is intended for a single local user. This app has no login or user isolation and should not be publicly hosted with personal data.
- `COOP_DB_PATH` can select an alternate database for testing or a persistent disk.

## Verification and CLI

```powershell
.\start.ps1 -Test
# Or with a freshly configured Python environment:
python -m unittest discover -s tests -v
python run_scoring.py --mode offline --limit 10
python run_scoring.py --mode claude --limit 5
```

Tests use temporary databases and mock Claude: validation, legacy migration, persistence, score invalidation, response parsing, batch partial failures, and the Streamlit add/score/track/filter workflow. They do not spend API credits or modify your real postings. Live Claude billing and account access still require a successful real request from your account.

## Scope

Implemented: posting ingestion and editing, local persistence, resume editing, offline and Claude scoring, partial-failure handling, score provenance, tracking notes/status, deadline alerts, search/filter/sort, CSV export, CLI, and automated tests.

The recovered daily plan is historical context, not an executable checklist. Optional future work: semantic embeddings pre-filter, cover-letter drafts, and authenticated deployment with durable per-user storage. The public demo uses fictional sample jobs; the personal app retains its real local data.
