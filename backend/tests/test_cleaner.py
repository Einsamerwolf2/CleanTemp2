import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cleaner import inspect
from app import app, TOKEN


class CleanerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2])
        self.root = Path(self.temp.name)
        self.target = dict(id='user_temp', name='Test', path=str(self.root), enabled=True, reason='')

    def tearDown(self):
        self.temp.cleanup()

    def old_file(self, name, content=b'abc'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        old = time.time() - 48 * 3600
        os.utime(path, (old, old))
        return path

    def test_scan_then_clean_preserves_recent_and_directories(self):
        old = self.old_file('nested/old.tmp')
        recent = self.root / 'recent.tmp'
        recent.write_bytes(b'keep')
        self.assertEqual(inspect(self.target)['size_bytes'], 3)
        self.assertTrue(old.exists())
        self.assertEqual(inspect(self.target, clean=True)['size_bytes'], 3)
        self.assertFalse(old.exists())
        self.assertTrue(recent.exists())
        self.assertTrue(old.parent.exists())

    def test_explorer_only_deletes_thumbnails(self):
        thumbnail = self.old_file('thumbcache_32.db')
        other = self.old_file('important.db')
        self.target['id'] = 'explorer'
        inspect(self.target, clean=True)
        self.assertFalse(thumbnail.exists())
        self.assertTrue(other.exists())

    def test_protected_folder_is_untouched(self):
        path = self.old_file('installer.msi')
        self.target['enabled'] = False
        inspect(self.target, clean=True)
        self.assertTrue(path.exists())

    def test_failed_deletion_is_not_counted(self):
        self.old_file('locked.tmp')
        with patch('cleaner.delete_file', side_effect=PermissionError):
            result = inspect(self.target, clean=True)
        self.assertEqual(result['size_bytes'], 0)
        self.assertEqual(result['skipped'], 1)

    def test_reparse_root_is_rejected(self):
        self.old_file('keep.tmp')
        with patch('cleaner.linked', return_value=True):
            result = inspect(self.target, clean=True)
        self.assertEqual(result['file_count'], 0)
        self.assertEqual(result['skipped'], 1)

    def test_api_rejects_invalid_ids_and_foreign_requests(self):
        client = app.test_client()
        base = 'http://127.0.0.1:5000'
        self.assertEqual(client.post('/api/clean', base_url=base, json={'ids':['user_temp']}).status_code, 403)
        for payload in ({'ids':['installer']}, {'ids':[True]}, {'ids':'user_temp'}, {'ids':['C:\\Windows']}, []):
            response = client.post('/api/clean', base_url=base, json=payload, headers={'X-CleanTemp-Token':TOKEN})
            self.assertEqual(response.status_code, 400)
        self.assertEqual(client.get('/api/status', base_url=base, headers={'Origin':'https://example.com'}).status_code, 403)
        self.assertEqual(client.get('/api/status', base_url='http://example.com:5000').status_code, 403)
        response = client.get('/', base_url=base)
        try:
            self.assertEqual(response.status_code, 200)
        finally:
            response.close()


if __name__ == '__main__':
    unittest.main()


