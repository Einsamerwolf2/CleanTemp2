import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scheduler


class SchedulerTests(unittest.TestCase):
    def test_invalid_choices_never_create_task(self):
        with patch.object(sys, 'frozen', True, create=True), patch('scheduler.command') as run:
            for hour, ids in [('25:00', ['user_temp']), ('12:30', ['system_temp']), ('12:30', []), ('12:30', [{}])]:
                with self.assertRaises(ValueError):
                    scheduler.configure(hour, ids)
            run.assert_not_called()

    def test_source_does_not_register_python_as_task(self):
        with patch.object(sys, 'frozen', False, create=True), patch('scheduler.command') as run:
            with self.assertRaises(ValueError):
                scheduler.configure('12:30', ['user_temp'])
            run.assert_not_called()

    def test_xml_uses_user_session_and_no_elevation(self):
        with tempfile.TemporaryDirectory() as temp:
            xmls = []
            def register(args):
                xmls.append(Path(args[args.index('/XML') + 1]).read_text('utf-16'))
            with patch.object(sys, 'frozen', True, create=True), patch('scheduler.identity', return_value='S-1-5-21-123'), patch('scheduler.data_dir', return_value=Path(temp)), patch('scheduler.command', side_effect=register):
                scheduler.configure('18:30', ['user_temp'])
            ns = {'t': 'http://schemas.microsoft.com/windows/2004/02/mit/task'}
            root = ET.fromstring(xmls[0])
            self.assertEqual(root.find('.//t:RunLevel', ns).text, 'LeastPrivilege')
            self.assertEqual(root.find('.//t:LogonType', ns).text, 'InteractiveToken')
            self.assertEqual(root.find('.//t:Arguments', ns).text, '--scheduled-clean')
            self.assertEqual(root.find('.//t:StartWhenAvailable', ns).text, 'false')
            self.assertEqual(json.loads((Path(temp) / 'schedule.json').read_text())['ids'], ['user_temp'])

    def test_registration_failure_restores_previous_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'schedule.json'
            config.write_text('{"enabled": false}')
            with patch.object(sys, 'frozen', True, create=True), patch('scheduler.identity', return_value='S-1-5-21-123'), patch('scheduler.data_dir', return_value=Path(temp)), patch('scheduler.command', side_effect=OSError('denied')):
                with self.assertRaises(OSError):
                    scheduler.configure('18:30', ['user_temp'])
            self.assertEqual(json.loads(config.read_text()), {'enabled': False})

    def test_headless_rejects_protected_or_disabled_targets(self):
        with patch('scheduler.inspect') as clean:
            for value in [{'enabled': False, 'ids': ['user_temp']}, {'enabled': True, 'ids': ['installer']}, {'enabled': True, 'ids': [{}]}]:
                with patch('scheduler.read_schedule', return_value=value):
                    self.assertEqual(scheduler.run_scheduled(), 1)
            clean.assert_not_called()

    def test_disable_removes_task_and_config(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'schedule.json'
            config.write_text('{}')
            with patch('scheduler.identity', return_value='S-1-5-21-123'), patch('scheduler.data_dir', return_value=Path(temp)), patch('scheduler.command') as run:
                scheduler.disable()
                run.assert_called_once_with(['schtasks', '/Delete', '/TN', 'CleanTemp-User-S-1-5-21-123', '/F'])
            self.assertFalse(config.exists())
