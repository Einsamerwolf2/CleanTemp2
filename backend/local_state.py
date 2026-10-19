"""Small local preferences and bounded cleanup history. Nothing is transmitted."""
from datetime import datetime
import json
import os
from pathlib import Path
import threading

from cleaner import PRESERVATION_LABELS

_WRITE_LOCK = threading.Lock()


def data_dir():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'CleanTemp'


def read_json(path, fallback):
    try:
        if path.stat().st_size > 512000:
            return fallback
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return fallback


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.new')
    with _WRITE_LOCK:
        try:
            temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def count(value):
    return value if type(value) is int and 0 <= value <= 2**63 else 0


class LocalState:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else data_dir()

    def preferences(self):
        value = read_json(self.directory / 'preferences.json', {})
        if not isinstance(value, dict):
            value = {}
        return {'automatic_updates': value.get('automatic_updates') is not False}

    def save_preferences(self, value):
        write_json(self.directory / 'preferences.json',
                   {'automatic_updates': value.get('automatic_updates') is True})

    def history(self):
        values = read_json(self.directory / 'history.json', [])
        if not isinstance(values, list):
            return []
        result = []
        for value in values[:60]:
            if not isinstance(value, dict) or value.get('mode') not in ('manual', 'scheduled'):
                continue
            try:
                when = datetime.fromisoformat(value['at'])
            except (KeyError, TypeError, ValueError):
                continue
            preserved = value.get('preserved', {})
            if not isinstance(preserved, dict):
                preserved = {}
            result.append(dict(at=when.isoformat(timespec='seconds'), mode=value['mode'],
                               deleted=count(value.get('deleted')), freed=count(value.get('freed')),
                               skipped=count(value.get('skipped')),
                               preserved={key: count(preserved.get(key)) for key in PRESERVATION_LABELS}))
        return result

    def record(self, mode, results):
        if mode not in ('manual', 'scheduled'):
            raise ValueError('Tipo de limpeza inválido.')
        entry = dict(at=datetime.now().astimezone().isoformat(timespec='seconds'), mode=mode,
                     deleted=sum(r['file_count'] for r in results),
                     freed=sum(r['size_bytes'] for r in results),
                     skipped=sum(r['skipped'] for r in results),
                     preserved={key: sum(r.get('preserved', {}).get(key, 0) for r in results)
                                for key in PRESERVATION_LABELS})
        write_json(self.directory / 'history.json', [entry, *self.history()][:60])
        return entry
