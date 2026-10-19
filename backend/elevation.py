"""One-shot UAC helper. No paths, config files or user profile from the caller."""
import ctypes
from ctypes import wintypes
from pathlib import Path
import os
import sys

from cleaner import inspect, linked, preservation_summary

SUPPORTED = frozenset({'system_temp'})


def windows_temp():
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.GetSystemWindowsDirectoryW.argtypes = [wintypes.LPWSTR, wintypes.UINT]
    api.GetSystemWindowsDirectoryW.restype = wintypes.UINT
    buffer = ctypes.create_unicode_buffer(32768)
    length = api.GetSystemWindowsDirectoryW(buffer, len(buffer))
    if not length or length >= len(buffer):
        raise OSError('Não foi possível confirmar a pasta do Windows.')
    return Path(buffer.value) / 'Temp'


def trusted_executable():
    """Only the frozen executable in the default protected installation folder."""
    if os.name != 'nt' or not getattr(sys, 'frozen', False):
        raise OSError('Esta função requer o aplicativo instalado em Arquivos de Programas.')
    shell = ctypes.WinDLL('shell32', use_last_error=True)
    shell.SHGetFolderPathW.argtypes = [wintypes.HWND, ctypes.c_int,
                                     wintypes.HANDLE, wintypes.DWORD,
                                     wintypes.LPWSTR]
    shell.SHGetFolderPathW.restype = ctypes.c_long
    buffer = ctypes.create_unicode_buffer(260)
    if shell.SHGetFolderPathW(None, 0x26, None, 0, buffer) != 0:
        raise OSError('Não foi possível confirmar a pasta de instalação.')
    expected = Path(buffer.value) / 'CleanTemp' / 'CleanTemp.exe'
    actual = Path(sys.executable).absolute()
    if os.path.normcase(str(actual)) != os.path.normcase(str(expected)):
        raise OSError('Reinstale o CleanTemp na pasta padrão antes de solicitar autorização.')
    for part in (actual, *actual.parents):
        if linked(part):
            raise OSError('Instalações com links ou junções não permitem autorização.')
    return actual


class ShellExecuteInfo(ctypes.Structure):
    _fields_ = [('cbSize', wintypes.DWORD), ('fMask', wintypes.ULONG),
                ('hwnd', wintypes.HWND), ('lpVerb', wintypes.LPCWSTR),
                ('lpFile', wintypes.LPCWSTR), ('lpParameters', wintypes.LPCWSTR),
                ('lpDirectory', wintypes.LPCWSTR), ('nShow', ctypes.c_int),
                ('hInstApp', wintypes.HINSTANCE), ('lpIDList', ctypes.c_void_p),
                ('lpClass', wintypes.LPCWSTR), ('hkeyClass', wintypes.HKEY),
                ('dwHotKey', wintypes.DWORD), ('hIcon', wintypes.HANDLE),
                ('hProcess', wintypes.HANDLE)]


def request_authorization():
    executable = trusted_executable()
    shell = ctypes.WinDLL('shell32', use_last_error=True)
    shell.ShellExecuteExW.argtypes = [ctypes.POINTER(ShellExecuteInfo)]
    shell.ShellExecuteExW.restype = wintypes.BOOL
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    ole = ctypes.WinDLL('ole32')
    ole.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    ole.CoInitializeEx.restype = ctypes.c_long
    initialized = ole.CoInitializeEx(None, 2) in (0, 1)
    info = ShellExecuteInfo()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = 0x40 | 0x100 | 0x400  # process handle, synchronous launch, own errors
    info.lpVerb = 'runas'
    info.lpFile = str(executable)
    info.lpParameters = '--authorized-clean system_temp'
    info.lpDirectory = str(executable.parent)
    info.nShow = 1
    try:
        if not shell.ShellExecuteExW(ctypes.byref(info)):
            code = ctypes.get_last_error()
            if code == 1223:
                return 'cancelled'
            raise ctypes.WinError(code)
        if not info.hProcess:
            raise OSError('O Windows não confirmou a execução autorizada.')
        try:
            if kernel.WaitForSingleObject(info.hProcess, 0xFFFFFFFF) != 0:
                raise OSError('Não foi possível acompanhar a limpeza autorizada.')
            code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(info.hProcess, ctypes.byref(code)):
                raise ctypes.WinError(ctypes.get_last_error())
            if code.value == 2:
                return 'cancelled'
            if code.value != 0:
                raise OSError('A limpeza autorizada não foi concluída. Os arquivos não verificados foram preservados.')
            return 'completed'
        finally:
            kernel.CloseHandle(info.hProcess)
    finally:
        if initialized:
            ole.CoUninitialize()


def run_authorized(ids):
    # No arbitrary path or caller-provided environment is used for deletion.
    if ids != ['system_temp']:
        return 1
    trusted_executable()
    if not ctypes.windll.shell32.IsUserAnAdmin():
        return 1
    target = dict(id='system_temp', name='Temporários do Windows',
                  path=str(windows_temp()), enabled=True, reason='')
    import tkinter as tk
    from tkinter import messagebox
    from ui_dialogs import confirm_action
    from resources import RESOURCE_ROOT
    from operation import cleaning_guard
    root = tk.Tk()
    root.withdraw()
    root.iconbitmap(str(RESOURCE_ROOT / 'assets/cleantemp.ico'))
    try:
        if not confirm_action(root, 'CleanTemp • Limpeza autorizada',
                'Limpar somente os arquivos temporários com mais de um dia em:\n'
                + target['path'] + '\n\nA exclusão é permanente. Arquivos abertos, protegidos e pastas serão preservados.'):
            return 2
        with cleaning_guard():
            result = inspect(target, clean=True)
        messagebox.showinfo('CleanTemp • Resultado da limpeza autorizada',
                            f"Removidos: {result['file_count']} arquivos\n\n"
                            + preservation_summary([result]), parent=root)
        return 0
    except OSError as exc:
        messagebox.showinfo('CleanTemp • Limpeza não concluída', str(exc), parent=root)
        return 1
    finally:
        root.destroy()
