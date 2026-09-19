# Co-op Job Matcher

I built this app to organize my co-op job search. It lets users save job postings, compare them with their resume, and track applications in one place. The full app also supports Claude AI for more detailed feedback on job fit.

## Features

- Save and edit job postings
- Compare job requirements with resume skills
- Track applications, interviews, offers, and rejections
- Add notes and view upcoming deadlines
- Filter, sort, and export postings as a CSV

## Technical skills

- **Python:** scoring logic, application tracking, and connecting the app's components.
- **Streamlit:** forms, tabs, filters, progress bars, and the resume editor.
- **SQL and SQLite:** storing and updating postings, scores, and application notes.
- **Claude API integration:** sending resumes and job descriptions for analysis and processing the responses.
- **JSON:** storing resume profiles and validating AI response formats.
- **Text processing and regular expressions:** matching resume skills with terms in job descriptions.
- **Automated testing:** checking app behaviour with `unittest`, simulated API responses, and Streamlit's testing tools.
- **Git and GitHub:** version control and sharing the source code.
- **Streamlit Community Cloud:** hosting the public demo.

## Live demo

[Try the demo](https://nayasimon-coop-job-matcher.streamlit.app/)

The demo includes a fictional resume and three sample jobs. Users can score postings, add sample jobs, and update application statuses. Each visitor has a separate session, and the **Reset demo** button restores the sample data. Changes may be lost when the page reloads.

Demo scores use keyword matching and do not require an API key. They measure how many resume skills appear in a posting, not the likelihood of receiving an offer.

After installing the dependencies below, run the demo locally with:

```powershell
python -m streamlit run demo_app.py
```

## Local setup

Install Python 3.11 or newer, then open a terminal in the project folder. On Windows, run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On Mac or Linux, use `python3` to create the environment and `.venv/bin/python` for the next two commands.

For an existing Windows setup, you can also use:

```powershell
.\start.ps1
```

Open the link shown in the terminal. The full app saves jobs between sessions. Update your profile in the **Resume** tab, then add postings to begin comparing jobs.

## Claude setup

Offline matching works without an account. To enable Claude:

1. Copy `.env.example` to `.env` if the file does not already exist.
2. Add your API key after `ANTHROPIC_API_KEY=` in `.env`.
3. Restart the app and select **Claude AI** in the sidebar.

Claude sends the resume and posting to Anthropic, and API charges apply. Keep the key in `.env`, not `.env.example`, and do not upload it to GitHub.

Jobs are saved in `data/postings.db`, and the resume is saved in `data/resume_profile.json`. These files and `.env` are excluded from Git.

## Deployment

On [Streamlit Community Cloud](https://share.streamlit.io/), select this repository, the `main` branch, and **`demo_app.py`**. Choose Python 3.12 and leave the secrets section empty.

`demo_app.py` runs the public demo. `app.py` runs the personal version with saved jobs and optional Claude scoring.

## Tests

```powershell
python -m unittest discover -s tests -v
```

The tests cover job storage, application updates, scoring errors, and separate demo sessions. API responses are simulated, so tests do not use Claude credits.

## Future improvements

- Better matching before sending jobs to Claude
- Support for drafting cover letters
- User accounts for saving jobs online
