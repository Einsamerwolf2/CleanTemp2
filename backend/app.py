import ctypes
import os
import secrets
import threading

from flask import Flask, jsonify, request, send_from_directory

from cleaner import inspect, targets, PRESERVATION_LABELS
from operation import cleaning_guard
from resources import RESOURCE_ROOT
from settings import read_config
from updates import checker

FRONTEND = RESOURCE_ROOT / 'frontend'
app = Flask(
    __name__, static_folder=str(FRONTEND / 'src'), static_url_path='/assets'
)
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.Lock()
LOCAL_HOSTS = {'127.0.0.1:5000', 'localhost:5000'}
LOCAL_ORIGINS = {None, *(f'http://{host}' for host in LOCAL_HOSTS)}


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


@app.before_request
def local_only():
    if request.host not in LOCAL_HOSTS:
        return jsonify(error='Host não permitido'), 403
    if request.headers.get('Origin') not in LOCAL_ORIGINS:
        return jsonify(error='Origem não permitida'), 403
    if request.method == 'POST':
        supplied_token = request.headers.get('X-CleanTemp-Token', '')
        if not secrets.compare_digest(supplied_token, TOKEN):
            message = 'Sessão inválida. Recarregue a página.'
            return jsonify(error=message), 403


@app.get('/')
def index():
    return send_from_directory(FRONTEND, 'index.html')


@app.get('/favicon.ico')
def favicon():
    return send_from_directory(RESOURCE_ROOT / 'assets', 'cleantemp.ico')


@app.get('/brand/cleantemp.png')
def brand_icon():
    return send_from_directory(RESOURCE_ROOT / 'assets', 'cleantemp.png')


@app.get('/help/primeiros-passos.pdf')
def first_steps():
    return send_from_directory(
        RESOURCE_ROOT / 'output/pdf',
        'cleantemp-primeiros-passos.pdf',
        mimetype='application/pdf',
        as_attachment=request.args.get('download') == '1',
    )


@app.get('/help/terms')
def terms():
    return send_from_directory(
        RESOURCE_ROOT, 'TERMS.txt', mimetype='text/plain; charset=utf-8'
    )


@app.get('/api/status')
def status():
    response = jsonify(admin=is_admin(), windows=os.name == 'nt', token=TOKEN)
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.get('/api/scan')
def scan():
    if not LOCK.acquire(blocking=False):
        return jsonify(error='Uma operação já está em andamento.'), 409
    try:
        folders = [inspect(item) for item in targets()]
        total = sum(folder['size_bytes'] for folder in folders)
        return jsonify(folders=folders, total_size_bytes=total)
    finally:
        LOCK.release()


@app.get('/api/info')
def info():
    return jsonify(read_config())


@app.get('/api/updates')
def updates():
    response = jsonify(checker.check(read_config()['github_repository']))
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.post('/api/clean')
def clean():
    data = request.get_json(silent=True)
    catalog = {target['id']: target for target in targets()}
    ids = data.get('ids') if isinstance(data, dict) else None
    valid_ids = (
        isinstance(ids, list)
        and bool(ids)
        and all(
            isinstance(item_id, str)
            and item_id in catalog
            and catalog[item_id]['enabled']
            for item_id in ids
        )
    )
    if not valid_ids:
        return jsonify(error='Selecione apenas pastas permitidas.'), 400
    if os.name != 'nt':
        return jsonify(error='Limpeza disponível apenas no Windows.'), 400
    if not LOCK.acquire(blocking=False):
        return jsonify(error='Uma operação já está em andamento.'), 409
    try:
        with cleaning_guard():
            results = [
                inspect(catalog[item_id], clean=True)
                for item_id in dict.fromkeys(ids)
            ]
        return jsonify(
            results=results,
            freed_bytes=sum(result['size_bytes'] for result in results),
            deleted_files=sum(result['file_count'] for result in results),
            skipped=sum(result['skipped'] for result in results),
            preserved={
                key: sum(r['preserved'][key] for r in results)
                for key in PRESERVATION_LABELS
            },
        )
    except OSError as exc:
        return jsonify(error=str(exc)), 409
    finally:
        LOCK.release()


if __name__ == '__main__':
    from desktop import main
    raise SystemExit(main())
