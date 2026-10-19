import json
from pathlib import Path
import sys
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from native_window import Window

class NativeWindowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data = Path(self.temp.name)
        self.patcher = patch('native_window.data_dir', return_value=self.data)
        self.patcher.start()
        self.root = tk.Tk()
        self.root.withdraw()
        self.window = Window(self.root)
        self.root.update_idletasks()

    def tearDown(self):
        self.root.destroy()
        self.patcher.stop()
        self.temp.cleanup()

    def test_tour_is_local_and_remembers_skip(self):
        with patch('native_window.inspect') as inspect, patch('native_window.webbrowser.open') as browser:
            self.window.tour()
            self.root.update_idletasks()
            self.assertEqual(self.window.tour_index, 0)
            def buttons(parent):
                for child in parent.winfo_children():
                    if isinstance(child, tk.Button):
                        yield child
                    yield from buttons(child)
            controls = {button.cget('text'): button for button in buttons(self.window.tour_window)}
            self.assertEqual(controls['Anterior'].cget('state'), 'disabled')
            controls['Próximo'].invoke()
            self.assertEqual(self.window.tour_index, 1)
            controls['Anterior'].invoke()
            self.assertEqual(self.window.tour_index, 0)
            controls['Saltar'].invoke()
            self.assertTrue((self.data / 'tour-seen').exists())
            inspect.assert_not_called()
            browser.assert_not_called()

    def test_scan_selection_blocks_protected_items(self):
        rows = [dict(id='user_temp', enabled=True, file_count=2, size_bytes=1024, reason='', skipped=0, name='Temp'), dict(id='installer', enabled=False, file_count=0, size_bytes=0, reason='Protegido', skipped=0, name='Installer')]
        self.window.scanned(rows, None)
        self.window.tree.selection_set('installer')
        self.window.toggle()
        self.assertEqual(self.window.marked, set())
        self.window.tree.selection_set('user_temp')
        self.window.toggle()
        self.assertEqual(self.window.marked, {'user_temp'})
        self.assertEqual(self.window.clean_button.cget('state'), 'normal')
        self.window.toggle()
        self.assertEqual(self.window.clean_button.cget('state'), 'disabled')

    def test_support_is_colored_and_has_icons(self):
        for channel in ('discord', 'telegram', 'whatsapp'):
            self.assertEqual(getattr(self.window, 'icon_' + channel).width(), 28)
        self.assertEqual(set(self.window.choices), {'user_temp', 'direct3d', 'nvidia', 'wer_archive', 'wer_queue'})

    def test_native_authorization_cancel_preserves_previous_result(self):
        self.window.set_authorization([{'id': 'system_temp', 'preserved': {'needs_permission': 1}}])
        self.window.result.set('Resultado anterior')
        with patch('native_window.confirm_action', return_value=False), patch('native_window.request_authorization') as request:
            self.window.authorize()
            request.assert_not_called()
            self.assertEqual(self.window.result.get(), 'Resultado anterior')
            self.assertFalse(self.window.busy)

    def test_personal_access_denied_does_not_offer_elevation(self):
        self.window.set_authorization([{'id': 'user_temp', 'preserved': {'needs_permission': 5}}])
        self.assertFalse(self.window.authorization_pending)
        self.assertEqual(self.window.authorize_button.cget('state'), 'disabled')

    def test_uac_cancel_keeps_normal_controls_available(self):
        self.window.set_authorization([{'id': 'system_temp', 'preserved': {'needs_permission': 1}}])
        self.window.result.set('Resultado anterior')
        def immediate(function, done):
            done('cancelled', None)
        with patch('native_window.confirm_action', return_value=True), patch.object(self.window, 'work', side_effect=immediate):
            self.window.authorize()
        self.assertFalse(self.window.busy)
        self.assertIn('Resultado anterior', self.window.result.get())
        self.assertIn('cancelada', self.window.result.get())
        self.assertEqual(self.window.scan_button.cget('state'), 'normal')

    def test_update_available_never_opens_browser_without_click(self):
        payload = {'state': 'available', 'latest_version': '1.4.0', 'url': 'https://github.com/Einsamerwolf2/CleanTemp2/releases/tag/v1.4.0'}
        def immediate(function, done):
            done(payload, None)
        with patch.object(self.window, 'work', side_effect=immediate), patch('native_window.webbrowser.open') as browser, patch('native_window.messagebox.askyesno') as prompt:
            self.window.update()
            browser.assert_not_called()
            prompt.assert_not_called()
            self.window.open_update()
            browser.assert_called_once_with(payload['url'])

    def test_terms_are_displayed_in_the_app(self):
        with patch('native_window.os.startfile') as external, patch('native_window.webbrowser.open') as browser:
            self.window.show_terms()
            external.assert_not_called()
            browser.assert_not_called()

    def test_filter_and_select_all_keep_protected_rows_out(self):
        rows = [dict(id='user_temp', enabled=True, file_count=2, size_bytes=1024, reason='', skipped=0, name='Temp pessoal'), dict(id='direct3d', enabled=True, file_count=1, size_bytes=100, reason='', skipped=0, name='Direct3D'), dict(id='installer', enabled=False, file_count=0, size_bytes=0, reason='Protegido', skipped=0, name='Installer')]
        self.window.scanned(rows, None)
        self.window.search.set('Temp')
        self.window.select_available()
        self.assertEqual(self.window.marked, {'user_temp'})
        self.window.search.set('')
        self.window.select_available()
        self.assertEqual(self.window.marked, {'user_temp', 'direct3d'})
        self.window.clear_selection()
        self.assertFalse(self.window.marked)

    def test_cancelled_scan_does_not_offer_partial_cleanup(self):
        self.window.scanned({'rows': [], 'cancelled': True}, None)
        self.assertFalse(self.window.busy)
        self.assertFalse(self.window.rows)
        self.assertFalse(self.window.marked)
        self.assertEqual(self.window.clean_button.cget('state'), 'disabled')
        self.assertIn('interrompida', self.window.result.get())

    def test_manual_cancel_never_starts_worker(self):
        self.window.scanned([dict(id='user_temp', enabled=True, file_count=1, size_bytes=10, reason='', skipped=0, name='Temp')], None)
        self.window.marked = {'user_temp'}
        with patch('native_window.confirm_action', return_value=False), patch.object(self.window, 'work') as worker:
            self.window.clean()
            worker.assert_not_called()

    def test_schedule_blocks_invalid_time_before_confirmation(self):
        self.window.hour.set('25:99')
        with patch('native_window.messagebox.showinfo'), patch('native_window.confirm_action') as confirm, patch.object(self.window, 'work') as worker:
            self.window.save_schedule()
            confirm.assert_not_called()
            worker.assert_not_called()

    def test_disabled_auto_updates_do_not_call_network(self):
        self.window.auto_updates.set(False)
        with patch.object(self.window, 'update') as update:
            self.window.start_updates()
            update.assert_not_called()
