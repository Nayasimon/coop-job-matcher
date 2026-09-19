# Co-op Job Matcher

A project I built to help organize my co-op job search. You can paste in job postings, compare them with your resume, and keep track of where you've applied.

It can also use the Claude API to explain how well your resume matches a job.

## What it does

- Saves job postings so they're all in one place
- Compares jobs with the skills on your resume
- Tracks applications, interviews, offers, and rejections
- Lets you save notes and see upcoming deadlines
- Filters and sorts jobs, and lets you download them as a CSV

## Technical skills

- **Python:** writing the scoring logic, application tracking, and code that connects everything together.
- **Streamlit:** building forms, tabs, filters, buttons, progress bars, and the resume editor.
- **SQL and SQLite:** storing, reading, updating, and deleting job postings, scores, and application notes.
- **Claude API integration:** sending resumes and job descriptions to Claude and reading its responses.
- **JSON:** saving resume profiles and checking the structure of AI responses.
- **Text processing and regular expressions:** matching skill names in job descriptions for the offline scorer.
- **Automated testing:** using Python's `unittest`, mocked API responses, and Streamlit's testing tools to check the app without spending API credits.
- **Git and GitHub:** tracking changes and sharing the code.
- **Streamlit Community Cloud:** deploying the public demo so people can try it in their browser.

## Trying the demo

[Try it here](https://nayasimon-coop-job-matcher.streamlit.app/)

The demo starts with a made-up resume and three sample jobs. You can score them, add your own sample posting, or change an application status to see how it works.

Everyone gets their own demo session. Changes can disappear when you reload, and the **Reset demo** button starts over.

The demo uses basic keyword matching, so it doesn't need an API key. A high score just means more of the resume's skills appear in the posting. It doesn't tell you how likely you are to get hired.

To run the demo locally:

```powershell
python -m streamlit run demo_app.py
```

## Running the full app

You'll need Python 3.11 or newer. Open a terminal in the project folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

These commands are for Windows. On Mac or Linux, use `python3` to create the environment and `.venv/bin/python` for the next two commands.

If you've already set things up on Windows, you can also run:

```powershell
.\start.ps1
```

Open the link printed in the terminal. The full app saves your jobs between visits. You can edit your resume in the **Resume** tab, then start adding postings.

## Using Claude

Keyword matching works without an account. If you want Claude to give a more detailed comparison:

1. Copy `.env.example` to `.env` if you don't already have one.
2. Put your API key beside `ANTHROPIC_API_KEY=` in `.env`.
3. Restart the app and choose **Claude AI** in the sidebar.

Claude sends your resume and the job posting to Anthropic, and API usage costs money. Keep your key in `.env`, not `.env.example`, and don't upload it to GitHub.

Your saved jobs are in `data/postings.db`. Your resume is in `data/resume_profile.json`. Both are ignored by Git, along with `.env`.

## Putting the demo online

On [Streamlit Community Cloud](https://share.streamlit.io/), select this repository, the `main` branch, and **`demo_app.py`**. Choose Python 3.12 and leave the secrets section empty.

Use `demo_app.py` for the public version. `app.py` is the version for keeping your own jobs and resume on your computer.

## Tests

```powershell
python -m unittest discover -s tests -v
```

The tests check things like saving jobs, updating applications, handling scoring errors, and keeping demo sessions separate. They use fake API responses, so running them doesn't spend any Claude credits.

## Things I'd like to add

- Better matching before sending jobs to Claude
- Help drafting cover letters
- Accounts so people can save their own jobs online
