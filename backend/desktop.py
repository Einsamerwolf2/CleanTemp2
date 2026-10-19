"""Windowed entry point, also used by the packaged application."""
import ctypes
from ctypes import wintypes
import json
import logging
from pathlib import Path
import os
import sys
import tkinter as tk
from tkinter import messagebox
from resources import RESOURCE_ROOT
from settings import VERSION


def configure_logging():
    from logging.handlers import RotatingFileHandler
    directory = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'CleanTemp/logs'
    directory.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(directory / 'cleantemp.log', maxBytes=512000, backupCount=2, encoding='utf-8')
    logging.basicConfig(level=logging.WARNING, handlers=[handler], format='%(asctime)s %(levelname)s %(message)s')


def self_test(report):
    """Offline smoke test of the frozen program; never scans or deletes files."""
    result = {'version': VERSION, 'frozen': bool(getattr(sys, 'frozen', False)), 'checks': [], 'ok': False}
    try:
        window = tk.Tk()
        window.withdraw()
        try:
            window.iconbitmap(str(RESOURCE_ROOT / 'assets/cleantemp.ico'))
            icon = tk.PhotoImage(file=str(RESOURCE_ROOT / 'assets/cleantemp.png'))
            assert icon.width() == 256 and icon.height() == 256
            from native_window import Window
            native = Window(window)
            assert len(native.choices) == 5
            window.update_idletasks()
            result['checks'].append('native-interface-and-schedule-controls')
            result['checks'].append('window-and-icon')
        finally:
            window.destroy()
        for relative in ('output/pdf/cleantemp-primeiros-passos.pdf',
                         'TERMS.txt', 'app_config.json',
                         'assets/support-discord.png', 'assets/support-telegram.png',
                         'assets/support-whatsapp.png'):
            assert (RESOURCE_ROOT / relative).is_file(), relative
            result['checks'].append(relative)
        result['ok'] = True
    except Exception as exc:
        result['error'] = str(exc)
    finally:
        Path(report).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if result['ok'] else 1


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--functional-check-report':
        from functional_check import verify
        return verify(sys.argv[2])
    if len(sys.argv) == 3 and sys.argv[1] == '--check-scheduled':
        from functional_check import scheduled_fixture
        return scheduled_fixture(sys.argv[2])
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test-report':
        return self_test(sys.argv[2])
    if len(sys.argv) >= 2 and sys.argv[1] == '--authorized-clean':
        from elevation import run_authorized
        return run_authorized(sys.argv[2:])
    configure_logging()
    if len(sys.argv) == 2 and sys.argv[1] == '--scheduled-clean':
        from scheduler import run_scheduled
        try:
            return run_scheduled()
        except OSError:
            logging.exception('Limpeza automática não iniciada ou não concluída')
            return 1
    root = tk.Tk()
    root.withdraw()
    root.title('CleanTemp')
    root.iconbitmap(str(RESOURCE_ROOT / 'assets/cleantemp.ico'))
    mutex = None
    api = None
    if os.name == 'nt':
        api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        api.CreateMutexW.restype = wintypes.HANDLE
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        api.CloseHandle.restype = wintypes.BOOL
        mutex = api.CreateMutexW(None, False, 'Local\\CleanTemp.EdilsonEnoque')
        if not mutex:
            messagebox.showerror('CleanTemp', 'Não foi possível abrir o CleanTemp. Tente novamente.', parent=root)
            root.destroy()
            return 1
        if ctypes.get_last_error() == 183:
            messagebox.showinfo('CleanTemp', 'O CleanTemp já está aberto. Procure sua janela na barra de tarefas.', parent=root)
            api.CloseHandle(mutex)
            root.destroy()
            return 0
    try:
        from native_window import Window
        Window(root)
        root.deiconify()
        root.mainloop()
        return 0
    finally:
        if mutex:
            api.CloseHandle(mutex)
        try:
            root.destroy()
        except tk.TclError:
            pass


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        logging.exception('Falha ao iniciar CleanTemp')
        if any(flag in sys.argv for flag in ('--scheduled-clean', '--check-scheduled', '--functional-check-report', '--self-test-report')):
            sys.exit(1)
        ctypes.windll.user32.MessageBoxW(None, 'Não foi possível abrir o CleanTemp. Tente novamente ou reinstale o aplicativo.', 'CleanTemp', 0x10)
        sys.exit(1)




