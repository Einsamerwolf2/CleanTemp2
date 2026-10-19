import ctypes
from pathlib import Path
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from safe_delete import delete_file, windows_api


@unittest.skipUnless(os.name == 'nt', 'Native Windows checks')
class SafeDeleteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2])
        self.root = Path(self.temp.name)
        self.path = self.root / 'test.tmp'
        self.path.write_bytes(b'temporary')
        old = time.time() - 48 * 3600
        os.utime(self.path, (old, old))

    def tearDown(self):
        self.temp.cleanup()

    def test_old_unopened_file_can_be_deleted(self):
        self.assertEqual(delete_file(self.path), 9)
        self.assertFalse(self.path.exists())
        self.assertTrue(self.root.exists())

    def test_open_file_is_preserved_even_when_it_shares_delete_access(self):
        api = windows_api()
        # Read access; share read, write and delete. Ordinary unlink could succeed.
        handle = api.CreateFileW(str(self.path), 0x80000000, 7, None, 3, 0, None)
        self.assertNotEqual(handle, ctypes.c_void_p(-1).value)
        try:
            with self.assertRaises(OSError):
                delete_file(self.path)
            self.assertTrue(self.path.exists())
        finally:
            api.CloseHandle(handle)
        self.assertEqual(delete_file(self.path), 9)

    def test_recently_modified_file_is_preserved(self):
        os.utime(self.path, None)
        with self.assertRaises(OSError):
            delete_file(self.path)
        self.assertTrue(self.path.exists())

    def test_hard_link_is_preserved(self):
        other = self.root / 'other.tmp'
        os.link(self.path, other)
        with self.assertRaises(OSError):
            delete_file(self.path)
        self.assertTrue(self.path.exists())
        self.assertTrue(other.exists())

    def test_readonly_file_is_preserved(self):
        os.chmod(self.path, 0o444)
        try:
            with self.assertRaises(OSError):
                delete_file(self.path)
            self.assertTrue(self.path.exists())
        finally:
            os.chmod(self.path, 0o666)

    def test_directory_is_preserved(self):
        with self.assertRaises(OSError):
            delete_file(self.root)
        self.assertTrue(self.root.is_dir())


if __name__ == '__main__':
    unittest.main()
