import argparse
from src import db, matcher
from src.workflow import score_batch


def main():
    parser = argparse.ArgumentParser(description='Score unscored co-op postings.')
    parser.add_argument('--mode', choices=['offline', 'claude'], default='offline')
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    db.init_db()
    postings = db.get_unscored_postings()[:args.limit]
    if not postings:
        print('No unscored postings.')
        return 0
    try:
        resume = matcher.load_resume_text()
    except (OSError, ValueError):
        print('Repair data/resume_profile.json before scoring.')
        return 1
    successes, errors = score_batch(postings, resume, args.mode)
    print(f'Saved {successes} scores; {len(errors)} failed.')
    for error in errors:
        print(error)
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
