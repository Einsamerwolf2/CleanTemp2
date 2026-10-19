"""Include the license texts of bundled runtime dependencies."""
from importlib.metadata import distribution
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parents[1]
out = root / 'dist/CleanTemp/ThirdPartyLicenses'
out.mkdir(parents=True, exist_ok=True)
python_license = Path(sys.base_prefix) / 'LICENSE.txt'
if not python_license.is_file():
    raise RuntimeError('Python license not found')
shutil.copyfile(python_license, out / 'Python-LICENSE.txt')
tcl_root = Path(sys.base_prefix) / 'tcl'
for source in tcl_root.rglob('license*'):
    if source.is_file():
        destination = out / 'TclTk' / source.relative_to(tcl_root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

