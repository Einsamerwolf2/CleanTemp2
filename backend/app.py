from pathlib import Path
import ctypes
import os
import secrets
import threading
import webbrowser
from flask import Flask, jsonify, request, send_from_directory
from cleaner import targets, inspect
from settings import read_config
from updates import checker

FRONTEND = Path(__file__).resolve().parent.parent / 'frontend'
app = Flask(__name__, static_folder=str(FRONTEND / 'src'), static_url_path='/assets')
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.Lock()


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


@app.before_request
def local_only():
    if request.host not in {'127.0.0.1:5000', 'localhost:5000'}:
        return jsonify(error='Host não permitido'), 403
    if request.headers.get('Origin') not in {None, 'http://127.0.0.1:5000', 'http://localhost:5000'}:
        return jsonify(error='Origem não permitida'), 403
    if request.method == 'POST' and not secrets.compare_digest(request.headers.get('X-CleanTemp-Token', ''), TOKEN):
        return jsonify(error='Sessão inválida. Recarregue a página.'), 403


@app.get('/')
def index():
    return send_from_directory(FRONTEND, 'index.html')


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
        return jsonify(folders=folders, total_size_bytes=sum(f['size_bytes'] for f in folders))
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
    catalog = {t['id']: t for t in targets()}
    ids = data.get('ids') if isinstance(data, dict) else None
    if not isinstance(ids, list) or not ids or any(not isinstance(i, str) or i not in catalog or not catalog[i]['enabled'] for i in ids):
        return jsonify(error='Selecione apenas identificadores de pastas permitidas.'), 400
    if os.name != 'nt':
        return jsonify(error='A limpeza está disponível apenas no Windows.'), 400
    if not LOCK.acquire(blocking=False):
        return jsonify(error='Uma operação já está em andamento.'), 409
    try:
        results = [inspect(catalog[i], clean=True) for i in dict.fromkeys(ids)]
        return jsonify(results=results, freed_bytes=sum(r['size_bytes'] for r in results), deleted_files=sum(r['file_count'] for r in results), skipped=sum(r['skipped'] for r in results))
    finally:
        LOCK.release()


if __name__ == '__main__':
    print('CleanTemp: http://127.0.0.1:5000 — Ctrl+C para encerrar')
    threading.Timer(1, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
