import os
import sys
import json
import subprocess
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from database import Database
from scanner import RomScanner
from cover_fetcher import CoverFetcher

app = Flask(__name__, static_folder='../frontend')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, '../config.json'))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, '../data'))
DB_PATH = os.path.join(DATA_DIR, 'retrovault.db')
COVERS_DIR = os.path.abspath(os.path.join(DATA_DIR, 'covers'))

# Ensure data dir exists
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)

db = Database(DB_PATH)
scanner = RomScanner(CONFIG_PATH)
cover_fetcher = CoverFetcher(COVERS_DIR)

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

# Startup logic
def init():
    config = load_config()
    print(f"RetroVault Backend starting...")
    stats = db.get_stats()
    if stats.get('total_games', 0) == 0:
        print("Empty database. Running initial scan...")
        games = scanner.scan_all()
        for g in games:
            db.add_game(g)
        print(f"Scan complete. Added {len(games)} games.")
    else:
        print(f"Database loaded with {stats.get('total_games')} games.")
    
    # Sync any local covers dropped into data/covers
    synced = cover_fetcher.sync_local_covers(db)
    if synced:
        print(f"Synced {synced} local covers into database.")

# API Endpoints
@app.route('/api/games', methods=['GET'])
def get_games():
    filters = {
        'console': request.args.get('console'),
        'search': request.args.get('search'),
        'favorite': request.args.get('favorite'),
        'sort': request.args.get('sort'),
        'order': request.args.get('order'),
        'page': request.args.get('page', 1, type=int),
        'per_page': request.args.get('per_page', 50, type=int)
    }
    return jsonify(db.get_games(filters))

@app.route('/api/games/<int:game_id>', methods=['GET'])
def get_game(game_id):
    game = db.get_game(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    return jsonify(game)

@app.route('/api/games/<int:game_id>/favorite', methods=['POST'])
def toggle_favorite(game_id):
    return jsonify(db.toggle_favorite(game_id))

@app.route('/api/games/<int:game_id>/rating', methods=['POST'])
def set_rating(game_id):
    data = request.json
    rating = data.get('rating', 0)
    return jsonify(db.set_rating(game_id, rating))

@app.route('/api/games/<int:game_id>/cover', methods=['POST'])
def upload_cover(game_id):
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    game = db.get_game(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
        
    filename = secure_filename(f"{game_id}_{file.filename}")
    console_dir = os.path.join(COVERS_DIR, game['console_name'])
    os.makedirs(console_dir, exist_ok=True)
    
    save_path = os.path.join(console_dir, filename)
    file.save(save_path)
    
    updated_game = db.update_game(game_id, {'cover_path': save_path.replace('\\', '/')})
    return jsonify(updated_game)

@app.route('/api/consoles', methods=['GET'])
def get_consoles():
    consoles = db.get_consoles()
    config = load_config()
    icons = config.get('console_icons', {})
    for c in consoles:
        c['icon'] = icons.get(c['name'], '🎮')
    return jsonify(consoles)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify(db.get_stats())

@app.route('/api/scan', methods=['POST'])
def scan_all():
    games = scanner.scan_all()
    count_per_console = {}
    for g in games:
        db.add_game(g)
        count_per_console[g['console']] = count_per_console.get(g['console'], 0) + 1
    cover_fetcher.sync_local_covers(db)
    return jsonify({'added': len(games), 'by_console': count_per_console})

@app.route('/api/scan/<console>', methods=['POST'])
def scan_console(console):
    games = scanner.scan_console(console)
    for g in games:
        db.add_game(g)
    cover_fetcher.sync_local_covers(db)
    return jsonify({'added': len(games), 'console': console})

@app.route('/api/covers/sync', methods=['POST'])
def sync_covers():
    synced = cover_fetcher.sync_local_covers(db)
    return jsonify({'success': True, 'synced': synced})

@app.route('/api/covers/fetch', methods=['POST'])
def fetch_covers():
    # Find games without cover_path
    games = db.get_games({'per_page': 10000})['games']
    needs_cover = [g for g in games if not g.get('cover_path')]
    
    def fetch_thread():
        def update_db(game_id, path):
            db.update_game(game_id, {'cover_path': path})
        cover_fetcher.fetch_covers_batch(needs_cover, callback=update_db)
        
    threading.Thread(target=fetch_thread).start()
    return jsonify({'message': f'Started fetching covers for {len(needs_cover)} games in background.'})

@app.route('/api/launch/<int:game_id>', methods=['POST'])
def launch_game(game_id):
    game = db.get_game(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    config = load_config()
    emu_config = config.get('emulators', {}).get(game['console_name'])

    if not emu_config or not emu_config.get('path'):
        return jsonify({'error': f'Emulator not configured for {game["console_name"]}'}), 400

    exe_path = emu_config['path']
    args_template = emu_config.get('args', '{rom}')

    try:
        # Update play count and last played
        current_plays = game.get('play_count', 0)
        from datetime import datetime
        db.update_game(game_id, {
            'play_count': current_plays + 1,
            'date_last_played': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        # Build absolute ROM path with Windows backslashes
        rom_path = os.path.abspath(game['file_path']).replace('/', '\\')
        args = args_template.replace('{rom}', rom_path)

        import shlex
        # Strip outer quotes so subprocess list2cmdline properly quotes arguments with spaces
        args_list = [arg.strip('"').strip("'") for arg in shlex.split(args, posix=False)]

        exe_path = os.path.normpath(exe_path)
        cmd = [exe_path] + args_list
        emu_dir = os.path.dirname(exe_path)

        # Log launch attempts
        log_path = os.path.abspath(os.path.join(BASE_DIR, '..', 'launch.log'))
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"\n--- Launch {datetime.now()} ---\n")
            log_file.write(f"Command: {subprocess.list2cmdline(cmd)}\n")
            try:
                subprocess.Popen(
                    cmd,
                    cwd=emu_dir
                )
                return jsonify({'success': True, 'message': 'Game launched'})
            except Exception as e:
                log_file.write(f"Launch error: {e}\n")
                return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config_api():
    config = load_config()
    return jsonify(config)

@app.route('/api/config/emulator/<console>', methods=['PUT'])
def update_emulator(console):
    data = request.json
    config = load_config()
    if 'emulators' not in config:
        config['emulators'] = {}
        
    config['emulators'][console] = {
        'name': data.get('name', ''),
        'path': data.get('path', ''),
        'args': data.get('args', '"{rom}"')
    }
    
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        
    return jsonify({'success': True})

# Static file serving
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/covers/<path:filename>')
def serve_cover(filename):
    return send_from_directory(COVERS_DIR, filename)

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    init()
    config = load_config()
    port = config.get('server', {}).get('port', 8080)
    host = config.get('server', {}).get('host', '127.0.0.1')
    print(f"Server starting on http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
