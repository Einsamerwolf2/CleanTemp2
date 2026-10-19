# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
root = Path(SPECPATH).parent
data = [(str(root / 'assets' / ('support-' + name + '.png')), 'assets')
        for name in ('discord', 'telegram', 'whatsapp')]
data += [(str(root / 'output/pdf/cleantemp-primeiros-passos.pdf'), 'output/pdf'),
         (str(root / 'TERMS.txt'), '.'),
         (str(root / 'assets/cleantemp.ico'), 'assets'),
         (str(root / 'assets/cleantemp.png'), 'assets'),
         (str(root / 'app_config.json'), '.'), (str(root / 'LICENSE'), '.')]

a = Analysis([str(root / 'backend/desktop.py')], pathex=[str(root / 'backend')],
             binaries=[], datas=data, hiddenimports=[], hookspath=[], hooksconfig={},
             runtime_hooks=[], excludes=['flask', 'waitress', 'reportlab', 'PIL', 'playwright', 'pypdf', 'pypdfium2'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='CleanTemp',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, icon=str(root / 'assets/cleantemp.ico'),
          version=str(root / 'packaging/version_info.txt'), uac_admin=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='CleanTemp')

