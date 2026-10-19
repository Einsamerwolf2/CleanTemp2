import ctypes
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import elevation
from cleaner import inspect
from operation import cleaning_guard
from safe_delete import PreservedError, category_for


class OutcomeTests(unittest.TestCase):
    def test_windows_failures_are_classified_conservatively(self):
        for code, category in [(32, 'in_use'), (33, 'in_use'), (5, 'needs_permission'), (1314, 'needs_permission'), (2, 'missing'), (3, 'missing'), (999, 'unverified')]:
            error = OSError('test')
            error.winerror = code
            self.assertEqual(category_for(error), category)
        self.assertEqual(category_for(PreservedError('safety', 'keep')), 'safety')
        self.assertEqual(category_for(PermissionError()), 'needs_permission')

    def test_open_and_recent_files_have_distinct_counts(self):
        import os
        import time
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            locked = root / 'locked.tmp'
            locked.write_bytes(b'abc')
            os.utime(locked, (time.time() - 172800,) * 2)
            (root / 'recent.tmp').write_bytes(b'keep')
            target = dict(id='user_temp', path=str(root), enabled=True)
            error = OSError('sharing')
            error.winerror = 32
            with patch('cleaner.delete_file', side_effect=error):
                result = inspect(target, clean=True)
            self.assertEqual(result['preserved']['in_use'], 1)
            self.assertEqual(result['preserved']['recent'], 1)
            self.assertEqual(result['skipped'], 1)
            self.assertEqual(result['file_count'], 0)
            self.assertTrue(locked.exists())

    def test_inaccessible_folder_is_one_unknown_contents_event(self):
        with tempfile.TemporaryDirectory() as folder:
            target = dict(id='system_temp', path=folder, enabled=True)
            with patch('pathlib.Path.iterdir', side_effect=PermissionError):
                result = inspect(target, clean=True)
            self.assertEqual(result['preserved']['needs_permission'], 1)
            self.assertEqual(result['file_count'], 0)

    def test_guard_rejects_a_second_operation(self):
        with cleaning_guard():
            with self.assertRaises(OSError):
                with cleaning_guard():
                    self.fail('Second cleanup must not start')
        with cleaning_guard():
            pass


class ElevationTests(unittest.TestCase):
    def test_source_cannot_request_uac(self):
        with patch.object(sys, 'frozen', False, create=True):
            with self.assertRaises(OSError):
                elevation.trusted_executable()

    def test_helper_rejects_paths_personal_ids_and_extra_arguments(self):
        with patch('elevation.trusted_executable') as trusted, patch('elevation.inspect') as remove:
            for ids in [[], ['installer'], ['user_temp'], ['C:\\Windows'], ['system_temp', 'user_temp']]:
                self.assertEqual(elevation.run_authorized(ids), 1)
            trusted.assert_not_called()
            remove.assert_not_called()

    def request(self, exit_code=0, launch=True, last_error=0):
        shell = MagicMock()
        kernel = MagicMock()
        ole = MagicMock()
        ole.CoInitializeEx.return_value = 0
        def execute(pointer):
            pointer._obj.hProcess = 123
            return launch
        shell.ShellExecuteExW.side_effect = execute
        kernel.WaitForSingleObject.return_value = 0
        def get_exit(handle, pointer):
            pointer._obj.value = exit_code
            return True
        kernel.GetExitCodeProcess.side_effect = get_exit
        def library(name, **kwargs):
            return {'shell32': shell, 'kernel32': kernel, 'ole32': ole}[name]
        with patch('elevation.trusted_executable', return_value=Path('C:/Program Files/CleanTemp/CleanTemp.exe')), patch('elevation.ctypes.WinDLL', side_effect=library), patch('elevation.ctypes.get_last_error', return_value=last_error):
            result = elevation.request_authorization()
        return result, shell, kernel, ole

    def test_uac_cancelled_does_not_wait_or_delete(self):
        result, shell, kernel, ole = self.request(launch=False, last_error=1223)
        self.assertEqual(result, 'cancelled')
        kernel.WaitForSingleObject.assert_not_called()
        ole.CoUninitialize.assert_called_once()

    def test_helper_cancelled_is_not_reported_as_success(self):
        result, shell, kernel, ole = self.request(exit_code=2)
        self.assertEqual(result, 'cancelled')
        kernel.CloseHandle.assert_called_once_with(123)

    def test_completed_helper_closes_process_handle(self):
        result, shell, kernel, ole = self.request()
        self.assertEqual(result, 'completed')
        kernel.CloseHandle.assert_called_once_with(123)

    def test_failed_helper_is_reported_as_failure(self):
        with self.assertRaises(OSError):
            self.request(exit_code=1)

    def test_installed_helper_still_requires_administrator(self):
        with patch('elevation.trusted_executable'), patch('elevation.ctypes.windll.shell32.IsUserAnAdmin', return_value=False), patch('elevation.inspect') as remove:
            self.assertEqual(elevation.run_authorized(['system_temp']), 1)
            remove.assert_not_called()

    def test_windows_directory_does_not_use_environment_paths(self):
        kernel = MagicMock()
        def directory(buffer, length):
            buffer.value = 'C:\\Windows'
            return len(buffer.value)
        kernel.GetSystemWindowsDirectoryW.side_effect = directory
        with patch('elevation.ctypes.WinDLL', return_value=kernel), patch.dict('os.environ', {'SystemRoot': 'C:\\malicious'}):
            self.assertEqual(elevation.windows_temp(), Path('C:/Windows/Temp'))

    def test_untrusted_install_location_is_rejected_before_uac(self):
        shell = MagicMock()
        def program_files(hwnd, folder, token, flags, buffer):
            buffer.value = 'C:\\Program Files'
            return 0
        shell.SHGetFolderPathW.side_effect = program_files
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', 'C:\\Users\\User\\Downloads\\CleanTemp.exe'), patch('elevation.ctypes.WinDLL', return_value=shell):
            with self.assertRaises(OSError):
                elevation.trusted_executable()
            shell.ShellExecuteExW.assert_not_called()
