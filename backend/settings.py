"""Public application settings. No credentials or personal data are stored here."""
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

VERSION = '1.0.0'
CONFIG_PATH = Path(__file__).resolve().parent.parent / 'app_config.json'


def read_config():
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    repository = data.get('github_repository', '')
    if not isinstance(repository, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        repository = ''
    supplied = data.get('support', {})
    if not isinstance(supplied, dict):
        supplied = {}
    allowed = {'discord': {'discord.gg', 'discord.com'}, 'telegram': {'t.me'}, 'whatsapp': {'wa.me', 'api.whatsapp.com'}}
    support = {}
    for channel, hosts in allowed.items():
        value = supplied.get(channel, '')
        try:
            parsed = urlsplit(value) if isinstance(value, str) else None
            valid = parsed and parsed.scheme == 'https' and parsed.hostname in hosts and not parsed.username and not parsed.password and parsed.port in (None, 443)
        except ValueError:
            valid = False
        support[channel] = value if valid else ''
    return dict(version=VERSION, github_repository=repository, support=support)
