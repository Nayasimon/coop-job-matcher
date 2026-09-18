import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()


def build_prompt(resume_text: str, job_title: str, job_description: str) -> str:
    return f"""You are a co-op recruiter evaluating a candidate for a job posting.

RESUME:
{resume_text}

JOB POSTING:
Title: {job_title}
Description: {job_description}

Evaluate this candidate's fit for the role. Respond with ONLY valid JSON in this exact format, no other text:
{{"score": <number 0-100>, "matching_skills": "<comma-separated skills from the resume that match this job>", "gaps": "<comma-separated skills/experience the job wants but the resume lacks>", "reasoning": "<2-3 sentence explanation of the score>"}}"""


def score_job_mock(resume_text: str, job_title: str, job_description: str) -> dict:
    """
    Temporary placeholder scorer that doesn't use the API.
    Does simple keyword overlap instead of real AI matching.
    Swap calls to this out for score_job() once billing is set up.
    """
    resume_words = set(resume_text.lower().split())
    job_words = set(job_description.lower().split())

    overlap = resume_words & job_words
    score = min(100, len(overlap) * 5)

    return {
        "score": score,
        "matching_skills": ", ".join(list(overlap)[:5]),
        "gaps": "Unable to determine - mock scorer only checks keyword overlap",
        "reasoning": f"Mock score based on {len(overlap)} overlapping words between resume and job description. Replace with real API call (score_job) once billing is set up."
    }


def score_job(resume_text: str, job_title: str, job_description: str) -> dict:
    """
    Sends a job + resume to Claude and returns a dict with
    score, matching_skills, gaps, and reasoning.
    """
    prompt = build_prompt(resume_text, job_title, job_description)

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_text = response.content[0].text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw_text)
        return result
    except json.JSONDecodeError:
        return {
            "score": None,
            "matching_skills": "",
            "gaps": "",
            "reasoning": f"Could not parse response: {raw_text}"
        }


def load_resume_text() -> str:
    """
    Loads the resume profile JSON and returns it as a text string,
    ready to feed into the matcher. Used by app.py.
    """
    with open("data/resume_profile.json") as f:
        resume = json.load(f)
    return json.dumps(resume, indent=2)


def score_posting(description: str, resume_text: str) -> dict:
    """
    Wrapper used by app.py. Matches the (description, resume_text) argument
    order the UI expects, and returns matching_skills/gaps as lists instead
    of comma-separated strings, since app.py joins them with ", ".join(...).
    Currently uses the mock scorer - swap the internal call to score_job()
    once billing is set up.
    """
    result = score_job(resume_text, "", description)

    matching_skills_list = [s.strip() for s in result["matching_skills"].split(",") if s.strip()]
    gaps_list = [result["gaps"]] if result["gaps"] else []

    return {
        "score": result["score"],
        "matching_skills": matching_skills_list,
        "gaps": gaps_list,
        "reasoning": result["reasoning"],
    }
