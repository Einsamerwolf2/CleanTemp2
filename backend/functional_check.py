"""Real Windows integration check; touches only a uniquely created fixture tree."""
import ctypes
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager

from cleaner import inspect
from safe_delete import windows_api
from scheduler import command, data_dir, identity, run_scheduled, task_xml
from settings import VERSION


@contextmanager
def fixture_environment(base):
    values = {'LOCALAPPDATA': str(base / 'profile'), 'TEMP': str(base / 'files')}
    original = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def scheduled_fixture(token):
    if not re.fullmatch(r'[0-9a-f]{32}', token):
        return 1
    base = data_dir() / 'validation' / token
    # This mode can only use fixtures created by verify(), never real Temp.
    manifest = json.loads((base / 'fixture.json').read_text('utf-8'))
    if manifest != {'token': token, 'version': VERSION}:
        return 1
    with fixture_environment(base):
        return run_scheduled()


def verify(report):
    result = {'version': VERSION, 'frozen': bool(getattr(sys, 'frozen', False)),
              'ok': False, 'checks': [], 'uac': 'Requires interactive installed validation'}
    if os.name != 'nt':
        result['error'] = 'Windows required'
        Path(report).write_text(json.dumps(result, indent=2), encoding='utf-8')
        return 1
    token = uuid.uuid4().hex
    base = data_dir() / 'validation' / token
    base.mkdir(parents=True, exist_ok=False)
    (base / 'fixture.json').write_text(json.dumps({'token': token, 'version': VERSION}), encoding='utf-8')
    files = base / 'files'
    files.mkdir()
    task_name = 'CleanTemp-Validation-' + token
    task_created = False
    handle = None
    api = windows_api()
    def old_file(name):
        path = files / name
        path.write_bytes(b'CleanTemp disposable verification file')
        old = time.time() - 172800
        os.utime(path, (old, old))
        return path
    try:
        removed = old_file('old.tmp')
        recent = files / 'recent.tmp'
        recent.write_bytes(b'keep recent')
        readonly = old_file('readonly.tmp')
        os.chmod(readonly, 0o444)
        opened = old_file('open.tmp')
        linked = old_file('linked.tmp')
        os.link(linked, files / 'linked-copy.tmp')
        handle = api.CreateFileW(str(opened), 0x80000000, 7, None, 3, 0, None)
        if handle == ctypes.c_void_p(-1).value:
            handle = None
            raise ctypes.WinError(ctypes.get_last_error())
        (files / 'kept-directory').mkdir()
        with fixture_environment(base):
            from cleaner import targets
            target = next(item for item in targets() if item['id'] == 'user_temp')
            scanned = inspect(target)
            assert scanned['file_count'] >= 1 and removed.exists()
            cleaned = inspect(target, clean=True)
            assert not removed.exists() and cleaned['file_count'] == 1
            assert all(p.exists() for p in (recent, readonly, opened, linked, files / 'linked-copy.tmp', files / 'kept-directory'))
            assert cleaned['preserved']['in_use'] == 1
            assert cleaned['preserved']['safety'] == 3
            result['checks'].extend(['real-scan', 'real-delete', 'open-preserved',
                                     'readonly-preserved', 'hardlinks-preserved',
                                     'recent-preserved', 'directories-preserved'])
            data_dir().mkdir(parents=True, exist_ok=True)
            (data_dir() / 'schedule.json').write_text(json.dumps({'enabled': True, 'hour': '23:59', 'ids': ['user_temp']}), encoding='utf-8')
        scheduled = old_file('scheduled.tmp')
        if getattr(sys, 'frozen', False):
            arguments = '--check-scheduled ' + token
        else:
            arguments = subprocess.list2cmdline([str(Path(__file__).with_name('desktop.py')), '--check-scheduled', token])
        # Real task, real Windows scheduler, same XML generator as daily cleaning.
        xml = task_xml('23:59', identity(), sys.executable, arguments)
        path = base / 'task.xml'
        path.write_text(xml, encoding='utf-16')
        command(['schtasks', '/Create', '/TN', task_name, '/XML', str(path)])
        task_created = True
        command(['schtasks', '/Run', '/TN', task_name])
        outcome = base / 'profile' / 'CleanTemp' / 'last-clean.json'
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline and not outcome.is_file():
            time.sleep(0.25)
        assert outcome.is_file(), 'Windows did not complete the isolated scheduled run'
        data = json.loads(outcome.read_text('utf-8'))
        assert not scheduled.exists() and data['deleted'] == 1
        result['checks'].extend(['real-task-created', 'real-task-executed',
                                 'real-scheduled-delete'])
        result['ok'] = True
    except Exception as exc:
        result['error'] = str(exc)
    finally:
        if handle:
            api.CloseHandle(handle)
        if task_created:
            try:
                command(['schtasks', '/Delete', '/TN', task_name, '/F'])
                result['checks'].append('real-task-removed')
            except OSError as exc:
                result['ok'] = False
                result['cleanup_error'] = str(exc)
        # Keep the small fixture and report as evidence; remove no user directories.
        readonly = files / 'readonly.tmp'
        if readonly.exists():
            os.chmod(readonly, 0o666)
        result['fixture'] = str(base)
        Path(report).parent.mkdir(parents=True, exist_ok=True)
        Path(report).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if result['ok'] else 1
