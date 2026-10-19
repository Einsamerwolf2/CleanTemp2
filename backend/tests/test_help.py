import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app


class HelpTests(unittest.TestCase):
    def test_guide_is_available_offline_and_can_be_downloaded(self):
        with app.test_client() as client:
            for suffix in ('', '?download=1'):
                response = client.get('/help/primeiros-passos.pdf' + suffix,
                                      base_url='http://127.0.0.1:5000')
                try:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.mimetype, 'application/pdf')
                    self.assertTrue(response.data.startswith(b'%PDF'))
                    disposition = response.headers['Content-Disposition']
                    self.assertEqual('attachment' in disposition, bool(suffix))
                finally:
                    response.close()

    def test_terms_and_tour_are_bundled_local_resources(self):
        with app.test_client() as client:
            for path, content in (
                ('/help/terms', 'Aceitação'),
                ('/assets/tour.js', 'tour-prev'),
                ('/', 'Saltar'),
            ):
                response = client.get(path, base_url='http://127.0.0.1:5000')
                try:
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(content, response.get_data(as_text=True))
                finally:
                    response.close()


if __name__ == '__main__':
    unittest.main()

