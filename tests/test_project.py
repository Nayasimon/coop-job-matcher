import json
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from src import db, matcher
from src.workflow import deadline_days, score_batch


class DatabaseFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.patch = patch.object(db, 'DB_PATH', Path(self.temp.name) / 'postings.db')
        self.patch.start()
        db.init_db()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def add(self):
        return db.add_posting('Developer', 'Example', 'Python and SQL', '2026-10-01', 'https://example.com/job')


class DatabaseTests(DatabaseFixture):
    def test_tracking_edit_and_delete(self):
        pid = self.add()
        db.save_score(pid, 82, 'Python', 'SQL', 'Relevant experience', 'claude')
        db.update_status(pid, 'Applied', 'Follow up next week')
        db.update_posting(pid, 'Developer', 'Example', 'Python and SQL', '2026-10-02')
        p = db.get_all_postings()[0]
        self.assertEqual((p['score'], p['notes'], p['status']), (82, 'Follow up next week', 'Applied'))
        db.update_posting(pid, 'Engineer', 'Example', 'C++')
        self.assertIsNone(db.get_all_postings()[0]['score'])
        db.delete_posting(pid)
        self.assertEqual(db.get_all_postings(), [])

    def test_invalid_inputs(self):
        for args in [(' ', 'X', 'Python'), ('Role', 'X', 'Python', 'tomorrow'), ('Role', 'X', 'Python', None, 'javascript:alert(1)')]:
            with self.assertRaises(ValueError):
                db.add_posting(*args)
        with self.assertRaises(ValueError):
            db.update_status(1, 'Invalid')
        for score in [None, True, -1, 101, float('nan')]:
            with self.assertRaises(ValueError):
                db.save_score(1, score, '', '', '')

    def test_batch_failure_preserves_previous_results_and_continues(self):
        first, second = self.add(), self.add()
        db.save_score(first, 50, '', '', 'Previous assessment', 'offline')
        result = {'score': 90, 'matching_skills': ['Python'], 'gaps': [], 'reasoning': 'Good fit', 'score_source': 'claude'}
        postings = sorted(db.get_all_postings(), key=lambda p: p['id'])
        with patch.object(matcher, 'score_posting', side_effect=[ValueError('bad response'), result]):
            successes, errors = score_batch(postings, '{}', 'claude')
        self.assertEqual((successes, len(errors)), (1, 1))
        saved = {p['id']: p for p in db.get_all_postings()}
        self.assertEqual(saved[first]['score'], 50)
        self.assertEqual(saved[second]['score'], 90)

    def test_legacy_migration_preserves_rows(self):
        legacy = Path(self.temp.name) / 'legacy.db'
        with sqlite3.connect(legacy) as conn:
            conn.execute("CREATE TABLE postings (id INTEGER PRIMARY KEY, title TEXT, company TEXT, description TEXT, deadline TEXT, link TEXT, date_added TEXT, score INTEGER, matching_skills TEXT, gaps TEXT, reasoning TEXT, status TEXT)")
            conn.execute("INSERT INTO postings VALUES (1, 'Old role', 'Example', 'Python', '', '', '', 75, 'Python', '', 'Old assessment', 'Applied')")
        conn.close()
        with patch.object(db, 'DB_PATH', legacy):
            db.init_db()
            db.init_db()
            row = db.get_all_postings()[0]
            self.assertEqual((row['title'], row['score'], row['status'], row['notes']), ('Old role', 75, 'Applied', ''))


class MatcherTests(unittest.TestCase):
    def test_offline_has_skill_boundaries_and_no_api(self):
        resume = json.dumps({'skills': ['C++', 'Python', 'Git']})
        with patch.object(matcher, 'score_job', side_effect=AssertionError('API used')):
            result = matcher.score_posting('C++ and PYTHON; digital tools', resume, 'offline')
        self.assertEqual(result['matching_skills'], ['C++', 'Python'])
        self.assertEqual(result['score'], 67)
        self.assertEqual(result['score_source'], 'offline')

    def test_auto_falls_back_without_key(self):
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': ''}):
            result = matcher.score_posting('Python', '{"skills":["Python"]}')
        self.assertEqual(result['score_source'], 'offline')

    def test_response_validation(self):
        valid = {'score': 75, 'matching_skills': 'Python, SQL', 'gaps': [], 'reasoning': 'Good fit'}
        self.assertEqual(matcher.normalize_result(valid)['matching_skills'], ['Python', 'SQL'])
        for change in [{'score': '75'}, {'score': True}, {'score': 101}, {'gaps': [5]}, {'reasoning': ''}]:
            with self.assertRaises(ValueError):
                matcher.normalize_result({**valid, **change})

    def test_claude_fenced_response_and_truncation(self):
        block = SimpleNamespace(type='text', text='```json\n{"score":80,"matching_skills":["Python"],"gaps":[],"reasoning":"Fits"}\n```')
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-only'}), patch('anthropic.Anthropic') as factory:
            client = factory.return_value.__enter__.return_value
            client.messages.create.return_value = SimpleNamespace(content=[block], stop_reason='end_turn')
            self.assertEqual(matcher.score_job('{}', 'Role', 'Python')['score'], 80)
            client.messages.create.return_value.stop_reason = 'max_tokens'
            with self.assertRaises(ValueError):
                matcher.score_job('{}', 'Role', 'Python')

    def test_profile_save_rejects_bad_data_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(matcher, 'RESUME_PATH', Path(temp) / 'resume.json'):
            matcher.save_resume_text('{"skills":["Python"]}')
            with self.assertRaises(ValueError):
                matcher.save_resume_text('{"skills":[]}')
            self.assertIn('Python', matcher.load_resume_text())

    def test_deadlines(self):
        today = date(2026, 9, 18)
        self.assertEqual(deadline_days('2026-09-18', today), 0)
        self.assertEqual(deadline_days('2026-09-17', today), -1)
        self.assertIsNone(deadline_days('invalid', today))


class AppTests(DatabaseFixture):
    def test_ui_add_score_track_filter(self):
        from streamlit.testing.v1 import AppTest
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': ''}):
            app = AppTest.from_file(str(Path(__file__).resolve().parent.parent / 'app.py')).run()
            self.assertFalse(app.exception)
            def by_label(elements, label):
                return next(e for e in elements if e.label == label)
            by_label(app.text_input, 'Job title').set_value('Python co-op')
            by_label(app.text_input, 'Company').set_value('Example')
            by_label(app.text_area, 'Full posting text').set_value('Python and SQLite development')
            by_label(app.button, 'Save posting').click().run()
            self.assertFalse(app.exception)
            by_label(app.button, 'Score unscored results (1)').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(db.get_all_postings()[0]['score_source'], 'offline')
            by_label(app.selectbox, 'Application status').set_value('Applied')
            by_label(app.text_area, 'Notes').set_value('Sent resume')
            by_label(app.button, 'Save tracking').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(db.get_all_postings()[0]['notes'], 'Sent resume')
            by_label(app.selectbox, 'Status filter').set_value('Offer').run()
            self.assertFalse(app.exception)
            self.assertTrue(any('No matching opportunities' in i.value for i in app.info))


class DemoTests(unittest.TestCase):
    def test_session_storage_and_api_isolation(self):
        from src.demo_context import activate, new_session
        first, second = new_session(), new_session()
        try:
            with patch.object(db, 'get_connection', side_effect=AssertionError('Disk database accessed')):
                with activate(first):
                    db.init_db()
                    db.add_posting('Private to session one', 'Example', 'Python')
                    matcher.save_resume_text('{"skills":["Session one skill"]}')
                    with self.assertRaises(ValueError):
                        matcher.score_job('{}', 'Role', 'Python')
                    with patch.object(matcher, 'score_job', side_effect=AssertionError('API called')):
                        self.assertEqual(matcher.score_posting('Python', matcher.load_resume_text(), 'claude')['score_source'], 'offline')
                with activate(second):
                    db.init_db()
                    self.assertEqual(db.get_all_postings(), [])
                    self.assertNotIn('Session one skill', matcher.load_resume_text())
                with activate(first):
                    self.assertEqual(len(db.get_all_postings()), 1)
        finally:
            first['connection'].close()
            second['connection'].close()

    def test_demo_score_reset_and_independent_visitors(self):
        from streamlit.testing.v1 import AppTest
        path = str(Path(__file__).resolve().parent.parent / 'demo_app.py')
        with patch.object(db, 'get_connection', side_effect=AssertionError('Disk database accessed')), patch.object(matcher, 'score_job', side_effect=AssertionError('API called')):
            first = AppTest.from_file(path).run()
            self.assertFalse(first.exception)
            self.assertEqual(next(s for s in first.selectbox if s.label == 'Scoring method').options, ['Offline skill overlap'])
            next(b for b in first.button if b.label == 'Score unscored results (3)').click().run()
            self.assertFalse(first.exception)
            self.assertTrue(any('offline' in e.label and '/100' in e.label for e in first.expander))
            second = AppTest.from_file(path).run()
            self.assertFalse(second.exception)
            self.assertTrue(any(b.label == 'Score unscored results (3)' for b in second.button))
            next(b for b in first.button if b.label == 'Reset demo').click().run()
            self.assertFalse(first.exception)
            self.assertTrue(any(b.label == 'Score unscored results (3)' for b in first.button))
            first.session_state['_demo_session']['connection'].close()
            second.session_state['_demo_session']['connection'].close()


if __name__ == '__main__':
    unittest.main()
