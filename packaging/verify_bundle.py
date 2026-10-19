"""Check the Windows bundle's resources, icon and non-elevated manifest."""
from pathlib import Path
import json
import hashlib
import sys
import pefile

root = Path(__file__).resolve().parents[1]
bundle = root / 'dist/CleanTemp'
program = bundle / 'CleanTemp.exe'
sys.path.insert(0, str(root / 'backend'))
from settings import VERSION
pe = pefile.PE(str(program))
version_strings = {}
for group in pe.FileInfo:
    for item in group:
        for table in getattr(item, 'StringTable', []):
            version_strings.update(table.entries)
assert version_strings[b'ProductVersion'].decode() == VERSION, 'Stale executable version'
assert pe.FILE_HEADER.Machine == 0x8664, 'Expected Windows x64'

assert pe.OPTIONAL_HEADER.Subsystem == 2, 'Executable must use the Windows GUI subsystem'
resources = {entry.id: entry for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries}
assert 14 in resources and 3 in resources, 'Windows icon resources are missing'
manifest_resource = resources[24].directory.entries[0].directory.entries[0].data.struct
manifest = pe.get_data(manifest_resource.OffsetToData, manifest_resource.Size).decode('utf-8')
assert 'asInvoker' in manifest and 'requireAdministrator' not in manifest
for relative in ('assets/support-discord.png', 'assets/support-telegram.png', 'assets/support-whatsapp.png',
                 'output/pdf/cleantemp-primeiros-passos.pdf', 'TERMS.txt',
                 'assets/cleantemp.ico', 'assets/cleantemp.png', 'app_config.json', 'LICENSE',
                 'VCRUNTIME140.dll', 'VCRUNTIME140_1.dll', '_tkinter.pyd', f'python{sys.version_info.major}{sys.version_info.minor}.dll'):
    assert (bundle / '_internal' / relative).is_file(), relative
tk_pe = pefile.PE(str(bundle / '_internal/_tkinter.pyd'))
tk_imports = [entry.dll.decode() for entry in tk_pe.DIRECTORY_ENTRY_IMPORT
              if entry.dll.lower().startswith((b'tcl', b'tk'))]
assert len(tk_imports) == 2, 'Expected Tcl and Tk runtime libraries'
for name in tk_imports:
    assert (bundle / '_internal' / name).is_file(), name
tcl_name = next(name for name in tk_imports if 'tk' not in name.lower())
tk_name = next(name for name in tk_imports if 'tk' in name.lower())
assert (bundle / 'ThirdPartyLicenses/Python-LICENSE.txt').is_file()
assert not list(bundle.rglob('test_cleaner.py'))
assert not list(bundle.rglob('pip.exe'))
from PyInstaller.archive.readers import CArchiveReader
archive = CArchiveReader(str(program))
pyz = archive.open_embedded_archive('PYZ.pyz')
for module in ('native_window', 'native_layout', 'local_state', 'ui_dialogs', 'elevation', 'scheduler', 'operation', 'safe_delete', 'functional_check'):
    assert module in pyz.toc, module
assert 'flask' not in pyz.toc and 'waitress' not in pyz.toc
report = dict(native=True, gui=True, icon=True, permission='asInvoker',
              files=sum(1 for path in bundle.rglob('*') if path.is_file()),
              bytes=sum(path.stat().st_size for path in bundle.rglob('*') if path.is_file()))
(root / 'dist/bundle-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
pe.close()



# Verify hashes of every shipped file, independently of the developer's Python.
manifest = {str(path.relative_to(bundle)).replace('\\', '/'):
            hashlib.sha256(path.read_bytes()).hexdigest()
            for path in bundle.rglob('*') if path.is_file()}
(root / 'dist/bundle-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
(root / '.tools').mkdir(exist_ok=True)
(root / '.tools/runtime-required.iss').write_text(
    '#define PythonDllName "python' + str(sys.version_info.major) + str(sys.version_info.minor) + '.dll"\n' + '#define TclDllName "' + tcl_name + '"\n'
    + '#define TkDllName "' + tk_name + '"\n', encoding='utf-8')
