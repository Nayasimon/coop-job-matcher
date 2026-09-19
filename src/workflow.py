"""Shared batch workflow and deadline handling for UI and CLI."""
from datetime import date
from src import db, matcher


def deadline_days(value, today=None):
    try:
        return (date.fromisoformat(value) - (today or date.today())).days
    except (TypeError, ValueError):
        return None


def score_batch(postings, resume_text, mode, progress=None):
    successes, errors = 0, []
    for index, posting in enumerate(postings):
        try:
            result = matcher.score_posting(posting['description'], resume_text, mode, posting['title'])
            db.save_score(posting['id'], result['score'], ', '.join(result['matching_skills']), ', '.join(result['gaps']), result['reasoning'], result['score_source'])
            successes += 1
        except Exception as error:
            errors.append(f"{posting['title']} at {posting['company']}: {matcher.friendly_error(error)}")
        if progress:
            progress((index + 1) / len(postings))
    return successes, errors
