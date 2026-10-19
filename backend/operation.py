"""Shared non-blocking operation guard for manual, scheduled and UAC cleaning."""
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import threading
import os

_LOCAL = threading.Lock()


@contextmanager
def cleaning_guard():
    if not _LOCAL.acquire(blocking=False):
        raise OSError('Uma limpeza já está em andamento. Aguarde.')
    handle = None
    kernel = None
    try:
        if os.name == 'nt':
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
            kernel.CreateMutexW.restype = wintypes.HANDLE
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel.CreateMutexW(None, False, 'Local\\CleanTemp.Cleaning')
            if not handle:
                raise OSError('Não foi possível reservar a limpeza. Nenhum arquivo foi apagado.')
            if ctypes.get_last_error() == 183:
                raise OSError('Uma limpeza já está em andamento. Aguarde.')
        yield
    finally:
        if handle:
            kernel.CloseHandle(handle)
        _LOCAL.release()
