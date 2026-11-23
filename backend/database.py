import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consoles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    icon TEXT,
                    rom_count INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emulators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    console_id INTEGER,
                    name TEXT,
                    exe_path TEXT,
                    args_template TEXT,
                    FOREIGN KEY(console_id) REFERENCES consoles(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    clean_name TEXT NOT NULL,
                    console_id INTEGER,
                    file_path TEXT UNIQUE NOT NULL,
                    file_size INTEGER,
                    file_extension TEXT,
                    cover_path TEXT,
                    genre TEXT,
                    year INTEGER,
                    rating INTEGER DEFAULT 0,
                    is_favorite BOOLEAN DEFAULT 0,
                    date_added TIMESTAMP,
                    date_last_played TIMESTAMP,
                    play_count INTEGER DEFAULT 0,
                    FOREIGN KEY(console_id) REFERENCES consoles(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_tags (
                    game_id INTEGER,
                    tag_id INTEGER,
                    PRIMARY KEY (game_id, tag_id),
                    FOREIGN KEY(game_id) REFERENCES games(id),
                    FOREIGN KEY(tag_id) REFERENCES tags(id)
                )
            ''')
            
            conn.commit()

    def add_game(self, game_dict):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ensure console exists
            cursor.execute('INSERT OR IGNORE INTO consoles (name) VALUES (?)', (game_dict['console'],))
            cursor.execute('SELECT id FROM consoles WHERE name = ?', (game_dict['console'],))
            console_id = cursor.fetchone()['id']
            
            # Upsert game by file_path
            cursor.execute('SELECT id FROM games WHERE file_path = ?', (game_dict['file_path'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update but preserve user data like rating, favorite, play_count
                cursor.execute('''
                    UPDATE games SET
                        name = ?, clean_name = ?, console_id = ?, file_size = ?, file_extension = ?
                    WHERE file_path = ?
                ''', (
                    game_dict['name'], game_dict['clean_name'], console_id,
                    game_dict['file_size'], game_dict['file_extension'], game_dict['file_path']
                ))
            else:
                cursor.execute('''
                    INSERT INTO games (
                        name, clean_name, console_id, file_path, file_size, file_extension, date_added
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    game_dict['name'], game_dict['clean_name'], console_id, game_dict['file_path'],
                    game_dict['file_size'], game_dict['file_extension'], datetime.now()
                ))
            
            # Update console rom_count
            cursor.execute('''
                UPDATE consoles SET rom_count = (
                    SELECT COUNT(*) FROM games WHERE console_id = consoles.id
                )
            ''')
            
            conn.commit()

    def get_games(self, filters_dict):
        with self.get_connection() as conn:
            query = '''
                SELECT g.*, c.name as console_name 
                FROM games g
                LEFT JOIN consoles c ON g.console_id = c.id
                WHERE 1=1
            '''
            params = []
            
            if 'console' in filters_dict and filters_dict['console']:
                query += ' AND c.name = ?'
                params.append(filters_dict['console'])
                
            if 'search' in filters_dict and filters_dict['search']:
                query += ' AND (g.name LIKE ? OR g.clean_name LIKE ?)'
                search_term = f"%{filters_dict['search']}%"
                params.extend([search_term, search_term])
                
            if 'favorite' in filters_dict and str(filters_dict['favorite']) == '1':
                query += ' AND g.is_favorite = 1'
                
            sort_map = {
                'name': 'g.clean_name',
                'size': 'g.file_size',
                'date': 'g.date_added',
                'rating': 'g.rating'
            }
            sort_by = sort_map.get(filters_dict.get('sort'), 'g.clean_name')
            order = 'DESC' if (filters_dict.get('order') or '').lower() == 'desc' else 'ASC'
            
            query += f' ORDER BY {sort_by} {order}'
            
            # Pagination
            page = int(filters_dict.get('page', 1))
            per_page = int(filters_dict.get('per_page', 50))
            offset = (page - 1) * per_page
            
            # Count total for pagination
            count_query = query.replace('SELECT g.*, c.name as console_name', 'SELECT COUNT(*)')
            cursor = conn.cursor()
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            query += ' LIMIT ? OFFSET ?'
            params.extend([per_page, offset])
            
            cursor.execute(query, params)
            games = [dict(row) for row in cursor.fetchall()]
            
            import math
            total_pages = math.ceil(total / per_page) if per_page else 1

            return {
                'games': games,
                'total': total,
                'pages': total_pages,
                'page': page,
                'per_page': per_page
            }

    def get_game(self, game_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT g.*, c.name as console_name 
                FROM games g
                LEFT JOIN consoles c ON g.console_id = c.id
                WHERE g.id = ?
            ''', (game_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_game(self, game_id, updates_dict):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            valid_keys = ['cover_path', 'genre', 'year', 'date_last_played', 'play_count']
            set_clauses = []
            params = []
            for k, v in updates_dict.items():
                if k in valid_keys:
                    set_clauses.append(f"{k} = ?")
                    params.append(v)
                    
            if set_clauses:
                query = f"UPDATE games SET {', '.join(set_clauses)} WHERE id = ?"
                params.append(game_id)
                cursor.execute(query, params)
                conn.commit()
            return self.get_game(game_id)

    def toggle_favorite(self, game_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE games SET is_favorite = NOT is_favorite WHERE id = ?', (game_id,))
            conn.commit()
            return self.get_game(game_id)

    def set_rating(self, game_id, rating):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE games SET rating = ? WHERE id = ?', (rating, game_id))
            conn.commit()
            return self.get_game(game_id)

    def get_consoles(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM consoles ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            stats = {}
            cursor.execute('SELECT COUNT(*) FROM games')
            stats['total_games'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(file_size) FROM games')
            stats['total_size'] = cursor.fetchone()[0] or 0
            
            cursor.execute('''
                SELECT c.name, COUNT(g.id) 
                FROM consoles c 
                LEFT JOIN games g ON c.id = g.console_id 
                GROUP BY c.id
            ''')
            stats['by_console'] = dict(cursor.fetchall())
            return stats

    def search_games(self, query):
        return self.get_games({'search': query, 'per_page': 100})
