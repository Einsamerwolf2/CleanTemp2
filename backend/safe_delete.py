"""Delete only through a verified exclusive Windows handle.

A failed check preserves the file. No fallback deletion is permitted.
"""
import ctypes
from ctypes import wintypes
import os
import time


class PreservedError(OSError):
    """A known safety decision; never a reason to force deletion."""
    def __init__(self, category, message):
        super().__init__(message)
        self.category = category


def category_for(error):
    if isinstance(error, PreservedError):
        return error.category
    code = getattr(error, 'winerror', None)
    if code in (32, 33):
        return 'in_use'
    if code in (5, 1314) or isinstance(error, PermissionError):
        return 'needs_permission'
    if code in (2, 3) or isinstance(error, FileNotFoundError):
        return 'missing'
    return 'unverified'


class FileInfo(ctypes.Structure):
    _fields_ = [
        ('attributes', wintypes.DWORD),
        ('created', wintypes.FILETIME),
        ('accessed', wintypes.FILETIME),
        ('modified', wintypes.FILETIME),
        ('volume', wintypes.DWORD),
        ('size_high', wintypes.DWORD),
        ('size_low', wintypes.DWORD),
        ('links', wintypes.DWORD),
        ('index_high', wintypes.DWORD),
        ('index_low', wintypes.DWORD),
    ]


class Disposition(ctypes.Structure):
    _fields_ = [('delete', ctypes.c_ubyte)]


def windows_api():
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                               ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    api.CreateFileW.restype = wintypes.HANDLE
    api.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(FileInfo)]
    api.GetFileInformationByHandle.restype = wintypes.BOOL
    api.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    api.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    api.SetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    api.SetFileInformationByHandle.restype = wintypes.BOOL
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL
    return api


def delete_file(path):
    """Return the deleted file's logical size, or raise OSError without forcing it.

    Sharing mode zero rejects ordinary open read/write/delete handles, even if
    they allow FILE_SHARE_DELETE. The same handle is retained for deletion.
    """
    if os.name != 'nt':
        raise OSError('A exclusão segura está disponível apenas no Windows.')
    # Reject known protected attributes before an access-denied open can hide them.
    metadata = path.lstat()
    if (getattr(metadata, 'st_file_attributes', 0) & (0x10 | 0x400 | 0x1 | 0x4)
            or metadata.st_nlink != 1):
        raise PreservedError('safety', 'Arquivo protegido; preservado.')
    api = windows_api()
    # GENERIC_READ | DELETE; no sharing; OPEN_EXISTING; OPEN_REPARSE_POINT.
    handle = api.CreateFileW(str(path), 0x80010000, 0, None, 3, 0x00200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        info = FileInfo()
        if not api.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        # Preserve directories, reparse points, readonly/system files and hardlinks.
        if info.attributes & (0x10 | 0x400 | 0x1 | 0x4) or info.links != 1:
            raise PreservedError('safety', 'Arquivo protegido ou com referências adicionais; preservado.')
        modified = ((info.modified.dwHighDateTime << 32) | info.modified.dwLowDateTime) / 10000000 - 11644473600
        if modified >= time.time() - 24 * 3600:
            raise PreservedError('recent', 'Arquivo alterado recentemente; preservado.')
        name = ctypes.create_unicode_buffer(32768)
        length = api.GetFinalPathNameByHandleW(handle, name, len(name), 0)
        if not length or length >= len(name):
            raise OSError('Não foi possível confirmar o caminho do arquivo.')
        final = name.value
        if final.startswith('\\\\?\\UNC\\'):
            final = '\\\\' + final[8:]
        elif final.startswith('\\\\?\\'):
            final = final[4:]
        if os.path.normcase(final) != os.path.normcase(os.path.abspath(path)):
            raise PreservedError('safety', 'O caminho mudou durante a limpeza; arquivo preservado.')
        disposition = Disposition(1)
        # FileDispositionInfo = 4: mark this verified handle for deletion on close.
        if not api.SetFileInformationByHandle(handle, 4, ctypes.byref(disposition), ctypes.sizeof(disposition)):
            raise ctypes.WinError(ctypes.get_last_error())
        return (info.size_high << 32) | info.size_low
    finally:
        api.CloseHandle(handle)
