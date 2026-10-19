"""Opt-in daily, non-elevated Windows task; no resident background service."""
import ctypes
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape

from cleaner import inspect, targets, PRESERVATION_LABELS
from operation import cleaning_guard
from local_state import LocalState, read_json, write_json, data_dir

ALLOWED = {'user_temp', 'direct3d', 'nvidia', 'wer_archive', 'wer_queue'}


def command(args):
    result = subprocess.run(args, capture_output=True, text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                            timeout=30)
    if result.returncode:
        raise OSError(result.stderr.strip() or result.stdout.strip()
                      or 'O Windows não conseguiu alterar o agendamento.')
    return result.stdout


def identity():
    import csv
    row = next(csv.reader(command(['whoami', '/user', '/fo', 'csv', '/nh'])
                          .strip().splitlines()))
    if len(row) != 2:
        raise OSError('Não foi possível identificar seu usuário.')
    sid = row[1]
    if not re.fullmatch(r'S-1-[0-9-]+', sid):
        raise OSError('Não foi possível identificar seu usuário.')
    return sid


def read_schedule():
    value = read_json(data_dir() / 'schedule.json', {})
    if not isinstance(value, dict) or not value:
        return {}
    hour = value.get('hour')
    ids = value.get('ids')
    valid = (isinstance(hour, str) and re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', hour)
             and isinstance(ids, list) and bool(ids)
             and all(isinstance(key, str) and key in ALLOWED for key in ids))
    if not valid:
        return {'enabled': False, 'hour': '18:00', 'ids': []}
    return {'enabled': value.get('enabled') is True, 'hour': hour, 'ids': list(dict.fromkeys(ids))}


def task_xml(hour, sid, executable, arguments='--scheduled-clean'):
    """Shared Windows schema, also used by the real disposable-task check."""
    return f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
<RegistrationInfo><Description>Limpeza pessoal autorizada no CleanTemp</Description></RegistrationInfo>
<Triggers><CalendarTrigger><StartBoundary>2026-01-01T{hour}:00</StartBoundary><Enabled>true</Enabled><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger></Triggers>
<Principals><Principal id="User"><UserId>{sid}</UserId><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
<Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries><StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><StartWhenAvailable>false</StartWhenAvailable><ExecutionTimeLimit>PT1H</ExecutionTimeLimit><Enabled>true</Enabled></Settings>
<Actions Context="User"><Exec><Command>{escape(executable)}</Command><Arguments>{escape(arguments)}</Arguments></Exec></Actions></Task>'''



def configure(hour, ids):
    if not getattr(sys, 'frozen', False):
        raise ValueError('O agendamento está disponível no aplicativo instalado.')
    if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', hour):
        raise ValueError('Informe o horário no formato HH:MM, como 18:30.')
    if (not isinstance(ids, list) or not ids
            or any(not isinstance(i, str) or i not in ALLOWED for i in ids)):
        raise ValueError('Selecione pelo menos uma opção pessoal permitida.')
    sid = identity()
    name = 'CleanTemp-User-' + sid
    executable = str(Path(sys.executable).resolve())
    xml = task_xml(hour, sid, executable)
    directory = data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    config = directory / 'schedule.json'
    previous = config.read_bytes() if config.exists() else None
    temporary = directory / 'schedule.new'
    temporary.write_text(json.dumps(dict(enabled=True, hour=hour, ids=ids),
                                    ensure_ascii=False), encoding='utf-8')
    temporary.replace(config)
    try:
        with tempfile.TemporaryDirectory() as staging:
            path = Path(staging) / 'task.xml'
            path.write_text(xml, encoding='utf-16')
            command(['schtasks', '/Create', '/TN', name, '/XML', str(path), '/F'])
    except Exception:
        if previous is None:
            config.unlink(missing_ok=True)
        else:
            config.write_bytes(previous)
        raise


def disable():
    # Fail closed before asking Windows to remove the task. A leftover task cannot clean.
    config = read_schedule()
    config['enabled'] = False
    write_json(data_dir() / 'schedule.json', config)
    name = 'CleanTemp-User-' + identity()
    try:
        command(['schtasks', '/Delete', '/TN', name, '/F'])
    except OSError as exc:
        raise OSError('A limpeza automática foi desativada, mas o Windows não confirmou a remoção da tarefa. '
                      'O agendamento restante não poderá iniciar novas limpezas.') from exc
    (data_dir() / 'schedule.json').unlink(missing_ok=True)


def run_scheduled():
    """Only explicit personal IDs, using the same exclusive-handle deletion."""
    if os.name != 'nt':
        return 1
    config = read_schedule()
    ids = config.get('ids')
    if (config.get('enabled') is not True or not isinstance(ids, list)
            or not ids or any(not isinstance(i, str) or i not in ALLOWED
                              for i in ids)):
        return 1
    with cleaning_guard():
        catalog = {item['id']: item for item in targets()}
        results = [inspect(catalog[i], clean=True) for i in dict.fromkeys(ids)]
        report = dict(at=datetime.now().isoformat(timespec='seconds'),
                      deleted=sum(r['file_count'] for r in results),
                      freed=sum(r['size_bytes'] for r in results),
                      skipped=sum(r['skipped'] for r in results),
                      preserved={key: sum(r['preserved'][key] for r in results)
                                 for key in PRESERVATION_LABELS})
        write_json(data_dir() / 'last-clean.json', report)
        try:
            LocalState(data_dir()).record('scheduled', results)
        except OSError:
            import logging
            logging.warning('Limpeza concluída sem conseguir guardar o histórico.')
        return 0
