import os
import json
import sqlite3
import urllib.request
import urllib.parse
import ssl
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class CoverFetcher:
    REPO_MAPPING = {
        "SNES": "Nintendo_-_Super_Nintendo_Entertainment_System",
        "NES": "Nintendo_-_Nintendo_Entertainment_System",
        "Mega Drive": "Sega_-_Mega_Drive_-_Genesis",
        "Master System": "Sega_-_Master_System_-_Mark_III",
        "Game Boy": "Nintendo_-_Game_Boy",
        "Game Boy Color": "Nintendo_-_Game_Boy_Color",
        "Game Boy Advance": "Nintendo_-_Game_Boy_Advance",
        "PS1": "Sony_-_PlayStation",
        "Atari 2600": "Atari_-_2600",
        "PC Engine": "NEC_-_PC_Engine_-_TurboGrafx_16",
        "Neo Geo": "SNK_-_Neo_Geo",
        "MAME": "MAME",
        "Sega 32X": "Sega_-_32X",
        "Mega CD": "Sega_-_Mega-CD_-_Sega_CD",
        "Nintendo DS": "Nintendo_-_Nintendo_DS",
        "WonderSwan": "Bandai_-_WonderSwan",
        "Pokemon Mini": "Nintendo_-_Pokemon_Mini",
        "Atari Lynx": "Atari_-_Lynx"
    }

    def __init__(self, covers_dir):
        self.covers_dir = covers_dir
        self.cache_dir = os.path.join(self.covers_dir, '.cache')
        os.makedirs(self.covers_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

    def _sanitize(self, name):
        return (name.replace('&', '_').replace('*', '_').replace('/', '_')
                    .replace(':', '_').replace('`', '_').replace('<', '_')
                    .replace('>', '_').replace('?', '_').replace('\\', '_')
                    .replace('|', '_').strip())

    def get_repo_boxarts(self, repo_name):
        cache_path = os.path.join(self.cache_dir, f"{repo_name}_tree.json")
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"https://api.github.com/repos/libretro-thumbnails/{repo_name}/git/trees/master?recursive=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'RetroVault/1.0'})
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                tree = data.get('tree', [])
                boxarts = [
                    item['path'].replace('Named_Boxarts/', '')
                    for item in tree
                    if item['path'].startswith('Named_Boxarts/') and item['path'].endswith('.png')
                ]
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(boxarts, f, ensure_ascii=False)
                return boxarts
        except Exception as e:
            print(f"Error loading boxart tree for {repo_name}: {e}")
            return []

    def find_best_boxart(self, clean_name, raw_name, boxarts_list):
        clean_lower = clean_name.lower().strip()
        raw_stem = os.path.splitext(raw_name)[0].lower().strip()
        
        candidates = []
        for filename in boxarts_list:
            fn_stem = os.path.splitext(filename)[0]
            fn_lower = fn_stem.lower()
            fn_clean = re.sub(r'\(.*?\)|\[.*?\]', '', fn_stem).strip().lower()
            
            score = None
            if fn_lower == raw_stem:
                score = 0
            elif fn_clean == clean_lower:
                score = 1
            elif fn_lower.startswith(clean_lower + " (") or fn_lower.startswith(clean_lower + " -") or fn_lower.startswith(clean_lower + ","):
                score = 5
            elif clean_lower in fn_clean:
                score = 20

            if score is not None:
                if any(r in fn_lower for r in ['(brazil', '(portuguese', '(pt']):
                    score -= 3
                elif any(r in fn_lower for r in ['(usa', '(world', '(en']):
                    score -= 2
                elif '(europe' in fn_lower:
                    score -= 1
                elif '(japan' in fn_lower:
                    score += 5
                candidates.append((score, filename))
                
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        return None

    def download_file(self, url, target_path):
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            if resp.status == 200:
                data = resp.read()
                if len(data) > 500:
                    with open(target_path, 'wb') as f:
                        f.write(data)
                    return True
        return False

    def fetch_covers_batch(self, games_list, callback=None):
        by_console = {}
        for g in games_list:
            c = g.get('console_name')
            if c:
                by_console.setdefault(c, []).append(g)

        for console_name, games in by_console.items():
            repo = self.REPO_MAPPING.get(console_name)
            if not repo:
                continue
            boxarts = self.get_repo_boxarts(repo)
            if not boxarts:
                continue

            console_covers_dir = os.path.join(self.covers_dir, console_name)
            os.makedirs(console_covers_dir, exist_ok=True)

            def worker(game):
                best = self.find_best_boxart(game['clean_name'], game.get('name', ''), boxarts)
                if not best:
                    return None
                encoded = urllib.parse.quote(best)
                url = f"https://raw.githubusercontent.com/libretro-thumbnails/{repo}/master/Named_Boxarts/{encoded}"
                save_name = f"{self._sanitize(game['clean_name'])}.png"
                target = os.path.join(console_covers_dir, save_name).replace('\\', '/')
                
                if os.path.exists(target) and os.path.getsize(target) > 500:
                    return (game['id'], target)
                try:
                    if self.download_file(url, target):
                        return (game['id'], target)
                except Exception:
                    pass
                return None

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(worker, g) for g in games]
                for f in as_completed(futures):
                    res = f.result()
                    if res and callback:
                        callback(res[0], res[1])

    def sync_local_covers(self, db):
        if not os.path.exists(self.covers_dir):
            return 0

        synced_count = 0
        consoles = [d for d in os.listdir(self.covers_dir) if os.path.isdir(os.path.join(self.covers_dir, d)) and not d.startswith('.')]

        for console_name in consoles:
            console_dir = os.path.join(self.covers_dir, console_name)
            valid_exts = ('.png', '.jpg', '.jpeg', '.webp')
            images = [f for f in os.listdir(console_dir) if f.lower().endswith(valid_exts)]
            if not images:
                continue

            games = db.get_games({'console': console_name, 'per_page': 10000}).get('games', [])
            if not games:
                continue

            for img in images:
                img_path = os.path.join(console_dir, img).replace('\\', '/')
                img_stem = os.path.splitext(img)[0].lower()

                id_match = re.match(r'^(\d+)_', img)
                matched_game = None

                if id_match:
                    gid = int(id_match.group(1))
                    for g in games:
                        if g['id'] == gid:
                            matched_game = g
                            break

                if not matched_game:
                    for g in games:
                        g_clean = (g.get('clean_name') or '').lower()
                        g_raw = os.path.splitext(g.get('name') or '')[0].lower()
                        if img_stem == g_clean or img_stem == g_raw:
                            matched_game = g
                            break

                if matched_game and matched_game.get('cover_path') != img_path:
                    db.update_game(matched_game['id'], {'cover_path': img_path})
                    matched_game['cover_path'] = img_path
                    synced_count += 1

        return synced_count
