"""Optional GitHub release lookup; never downloads or executes an update."""
import json
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from settings import VERSION


def version_tuple(value):
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', value)
    return tuple(map(int, match.groups())) if match else None


class UpdateChecker:
    def __init__(self):
        self.lock = threading.Lock()
        self.cached = None
        self.repository = None
        self.expires = 0

    def check(self, repository):
        if not repository:
            return dict(state='unconfigured', current_version=VERSION)
        with self.lock:
            if repository == self.repository and self.cached and time.monotonic() < self.expires:
                return dict(self.cached)
            result = self._fetch(repository)
            self.repository = repository
            self.cached = result
            self.expires = time.monotonic() + (900 if result['state'] in {'available', 'current', 'no_release'} else 60)
            return dict(result)

    def _fetch(self, repository):
        base = dict(current_version=VERSION)
        request = Request(f'https://api.github.com/repos/{repository}/releases/latest', headers={
            'Accept': 'application/vnd.github+json', 'User-Agent': f'CleanTemp/{VERSION}',
            'X-GitHub-Api-Version': '2026-03-10',
        })
        try:
            with urlopen(request, timeout=4) as response:
                raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError('Oversized response')
            release = json.loads(raw)
            tag = release.get('tag_name')
            latest = version_tuple(tag)
            if not latest or release.get('draft') or release.get('prerelease'):
                return dict(base, state='unavailable')
            newer = latest > version_tuple(VERSION)
            return dict(base, state='available' if newer else 'current', latest_version=tag,
                        url=f'https://github.com/{repository}/releases/tag/{quote(tag, safe="")}')
        except HTTPError as exc:
            return dict(base, state='no_release' if exc.code == 404 else 'unavailable')
        except (URLError, TimeoutError, OSError):
            return dict(base, state='offline')
        except (ValueError, TypeError, AttributeError):
            return dict(base, state='unavailable')


checker = UpdateChecker()
