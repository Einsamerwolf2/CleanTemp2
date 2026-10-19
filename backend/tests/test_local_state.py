import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_state import LocalState
from cleaner import inspect
import scheduler


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.store = LocalState(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_history_is_bounded_and_contains_no_paths(self):
        result = dict(file_count=3, size_bytes=1234, skipped=1,
                      path='C:/Users/private-name/file.txt', preserved={'in_use': 1})
        for _ in range(64):
            self.store.record('manual', [result])
        history = self.store.history()
        self.assertEqual(len(history), 60)
        self.assertEqual(history[0]['deleted'], 3)
        self.assertNotIn('private-name', (self.path / 'history.json').read_text('utf-8'))
        self.assertFalse((self.path / 'history.json.new').exists())

    def test_corrupt_preferences_and_history_do_not_break_startup(self):
        (self.path / 'preferences.json').write_text('null')
        (self.path / 'history.json').write_text('{bad')
        self.assertEqual(self.store.preferences(), {'automatic_updates': True})
        self.assertEqual(self.store.history(), [])
        self.store.save_preferences({'automatic_updates': False})
        self.assertFalse(self.store.preferences()['automatic_updates'])

    def test_untrusted_history_counters_are_sanitized(self):
        data = [None, {'mode': 'unknown', 'at': '2026-10-18'},
                {'mode': 'manual', 'at': '2026-10-18T10:00:00', 'deleted': 'bad',
                 'freed': -1, 'preserved': {'in_use': True}}]
        (self.path / 'history.json').write_text(json.dumps(data))
        record = self.store.history()[0]
        self.assertEqual(record['deleted'], 0)
        self.assertEqual(record['freed'], 0)
        self.assertEqual(record['preserved']['in_use'], 0)

    def test_malformed_schedule_is_disabled_instead_of_crashing(self):
        for value in [[], {'enabled': True, 'hour': None, 'ids': None},
                      {'enabled': True, 'hour': '12:00', 'ids': ['installer']}]:
            (self.path / 'schedule.json').write_text(json.dumps(value))
            with patch('scheduler.data_dir', return_value=self.path):
                self.assertFalse(scheduler.read_schedule().get('enabled', False))

    def test_failed_task_removal_disables_future_cleanup(self):
        (self.path / 'schedule.json').write_text(json.dumps({'enabled': True, 'hour': '18:00', 'ids': ['user_temp']}))
        with patch('scheduler.data_dir', return_value=self.path), patch('scheduler.identity', return_value='S-1-5-21-123'), patch('scheduler.command', side_effect=OSError('denied')):
            with self.assertRaises(OSError):
                scheduler.disable()
            self.assertFalse(scheduler.read_schedule()['enabled'])
            with patch('scheduler.inspect') as remove:
                self.assertEqual(scheduler.run_scheduled(), 1)
                remove.assert_not_called()

    def test_interrupted_analysis_never_deletes(self):
        (self.path / 'keep.tmp').write_bytes(b'keep')
        stop = threading.Event()
        stop.set()
        target = dict(id='user_temp', path=str(self.path), enabled=True)
        with patch('cleaner.delete_file') as remove:
            result = inspect(target, cancel=stop)
        self.assertEqual(result['file_count'], 0)
        remove.assert_not_called()
