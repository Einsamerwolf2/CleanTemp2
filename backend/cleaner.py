from pathlib import Path
import os
import stat
import time


def targets():
    user = Path(os.environ.get('USERPROFILE', str(Path.home())))
    local = Path(os.environ.get('LOCALAPPDATA', str(user / 'AppData/Local')))
    windows = Path(os.environ.get('SystemRoot', r'C:\Windows'))
    program = Path(os.environ.get('ProgramData', r'C:\ProgramData'))
    definitions = [
        ('user_temp', 'Temporários do usuário', Path(os.environ.get('TEMP', str(local / 'Temp'))), True, ''),
        ('system_temp', 'Temporários do Windows', windows / 'Temp', True, ''),
        ('explorer', 'Miniaturas do Explorer', local / 'Microsoft/Windows/Explorer', True, ''),
        ('direct3d', 'Cache Direct3D', local / 'D3DSCache', True, ''),
        ('nvidia', 'Cache NVIDIA', local / 'NVIDIA/DXCache', True, ''),
        ('wer_archive', 'Relatórios de erros do usuário', local / 'Microsoft/Windows/WER/ReportArchive', True, ''),
        ('wer_queue', 'Fila de relatórios de erros', local / 'Microsoft/Windows/WER/ReportQueue', True, ''),
        ('wer_system', 'Relatórios de erros do sistema', program / 'Microsoft/Windows/WER/ReportArchive', True, ''),
        ('npm', 'Cache npm', user / '.npm/_cacache', True, ''),
        ('pip', 'Cache pip', local / 'pip/cache', True, ''),
        ('update', 'Downloads do Windows Update', windows / 'SoftwareDistribution/Download', False, 'Use a Limpeza de Disco do Windows para não interferir em atualizações.'),
        ('installer', 'Windows Installer', windows / 'Installer', False, 'Instaladores e patches são necessários para reparar e remover programas.'),
        ('cbs', 'Logs CBS', windows / 'Logs/CBS', False, 'Logs de manutenção do Windows: limpeza automática desativada.'),
        ('defender', 'Histórico do Defender', program / 'Microsoft/Windows Defender/Scans/History/Store', False, 'Histórico de segurança: limpeza automática desativada.'),
        ('prefetch', 'Prefetch', windows / 'Prefetch', False, 'Gerenciado pelo Windows.'),
    ]
    return [dict(id=i, name=n, path=str(p), enabled=e, reason=r) for i,n,p,e,r in definitions]


def linked(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def checked_root(item):
    root = Path(item['path'])
    if not root.is_absolute() or root == Path(root.anchor):
        raise OSError('Caminho inválido')
    for part in (root, *root.parents):
        if linked(part):
            raise OSError('Links e junções não são permitidos')
    if not root.is_dir():
        raise OSError('Pasta não encontrada')
    return root


def files(item, errors):
    root = checked_root(item)
    stack = [root]
    cutoff = time.time() - 24 * 3600
    while stack:
        directory = stack.pop()
        try:
            children = list(directory.iterdir())
        except OSError:
            errors.append(str(directory))
            continue
        for child in children:
            try:
                if linked(child):
                    continue
                if child.is_dir():
                    if item['id'] != 'explorer':
                        stack.append(child)
                elif child.is_file():
                    if item['id'] == 'explorer' and not child.match('thumbcache_*.db'):
                        continue
                    if child.stat().st_mtime < cutoff:
                        yield child
            except OSError:
                errors.append(str(child))


def inspect(item, clean=False):
    result = dict(item, exists=Path(item['path']).is_dir(), size_bytes=0, file_count=0, skipped=0)
    if not item['enabled']:
        return result
    errors = []
    try:
        for path in files(item, errors):
            try:
                # Validate containment and every ancestor again immediately before deletion.
                root = checked_root(item)
                path.relative_to(root)
                if any(linked(p) for p in (path, *path.parents)):
                    continue
                size = path.stat().st_size
                if clean:
                    path.unlink()
                result['size_bytes'] += size
                result['file_count'] += 1
            except OSError:
                errors.append(str(path))
    except OSError as exc:
        result['reason'] = str(exc)
        errors.append(str(exc))
    result['skipped'] = len(errors)
    return result
