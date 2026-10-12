import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from updates import UpdateChecker, version_tuple
from settings import read_config


class UpdateTests(unittest.TestCase):
    def response(self, tag):
        return io.BytesIO(json.dumps({'tag_name': tag, 'draft': False, 'prerelease': False}).encode())

    def test_numeric_versions(self):
        self.assertGreater(version_tuple('v1.10.0'), version_tuple('1.9.0'))
        self.assertIsNone(version_tuple('v2.0.0-beta'))

    def test_new_release_and_cache(self):
        checker = UpdateChecker()
        with patch('updates.urlopen', return_value=self.response('v1.1.0')) as fetch:
            result = checker.check('owner/CleanTemp')
            self.assertEqual(result['state'], 'available')
            self.assertEqual(result['url'], 'https://github.com/owner/CleanTemp/releases/tag/v1.1.0')
            self.assertEqual(checker.check('owner/CleanTemp'), result)
            self.assertEqual(fetch.call_count, 1)

    def test_current_or_older_release(self):
        for tag in ('v1.0.0', 'v0.9.0'):
            with patch('updates.urlopen', return_value=self.response(tag)):
                self.assertEqual(UpdateChecker().check('owner/repo')['state'], 'current')

    def test_offline_then_reconnected(self):
        checker = UpdateChecker()
        with patch('updates.urlopen', side_effect=URLError('offline')):
            self.assertEqual(checker.check('owner/repo')['state'], 'offline')
        checker.expires = 0
        with patch('updates.urlopen', return_value=self.response('v1.2.0')):
            self.assertEqual(checker.check('owner/repo')['state'], 'available')

    def test_no_repository_makes_no_request(self):
        with patch('updates.urlopen') as fetch:
            self.assertEqual(UpdateChecker().check('')['state'], 'unconfigured')
            fetch.assert_not_called()

    def test_missing_release_and_malformed_response(self):
        with patch('updates.urlopen', side_effect=HTTPError('url', 404, 'Not found', {}, None)):
            self.assertEqual(UpdateChecker().check('owner/repo')['state'], 'no_release')
        with patch('updates.urlopen', return_value=io.BytesIO(b'not json')):
            self.assertEqual(UpdateChecker().check('owner/repo')['state'], 'unavailable')

    def test_settings_reject_external_or_unsafe_links(self):
        data = {'github_repository': '../bad/path', 'support': {'discord': 'https://evil.example', 'telegram': 'javascript:alert(1)', 'whatsapp': 'https://wa.me/258000000000'}}
        with patch('settings.CONFIG_PATH') as path:
            path.read_text.return_value = json.dumps(data)
            config = read_config()
        self.assertEqual(config['github_repository'], '')
        self.assertEqual(config['support']['discord'], '')
        self.assertEqual(config['support']['telegram'], '')
        self.assertEqual(config['support']['whatsapp'], data['support']['whatsapp'])


if __name__ == '__main__':
    unittest.main()
