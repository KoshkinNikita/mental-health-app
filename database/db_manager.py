# database/db_manager.py
"""Менеджер базы данных SQLite"""

import sqlite3
import json
import hashlib
import secrets
from datetime import datetime, timedelta
import os


class DatabaseManager:
    """Менеджер базы данных SQLite"""

    def __init__(self, db_name="mental_health.db"):
        # Получаем путь к папке database
        db_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_name = os.path.join(db_dir, db_name)

        print(f"📁 База данных будет в: {self.db_name}")

        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Подключение к базе данных"""
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)

        self.conn.row_factory = sqlite3.Row

    def create_tables(self):
        """Создание таблиц если они не существуют"""
        cursor = self.conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица записей настроения
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mood_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                mood_score INTEGER NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, date)
            )
        ''')

        # Таблица записей дневника
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diary_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                situation TEXT NOT NULL,
                emotions TEXT NOT NULL,
                thoughts TEXT NOT NULL,
                distortions TEXT NOT NULL,
                alternative_thought TEXT,
                reassessment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Таблица упражнений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercise_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exercise_name TEXT NOT NULL,
                duration_minutes INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Таблица достижений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                icon TEXT NOT NULL,
                requirement_type TEXT NOT NULL,
                requirement_value INTEGER NOT NULL,
                xp_reward INTEGER NOT NULL DEFAULT 10
            )
        ''')

        # Таблица прогресса пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,
                progress INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (achievement_id) REFERENCES achievements (id),
                UNIQUE(user_id, achievement_id)
            )
        ''')

        # Таблица опыта и уровней
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                streak_days INTEGER DEFAULT 0,
                last_activity_date DATE,
                total_entries INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Таблица ДНК профиля
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mental_health_dna (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                profile_data TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercise_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                entry_id INTEGER NOT NULL,
                exercise_name TEXT NOT NULL,
                helped INTEGER DEFAULT 0,  -- 1 = помогло, -1 = не помогло, 0 = не оценено
                feedback_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (entry_id) REFERENCES diary_entries (id)
            )
        ''')

        self.create_base_achievements()
        self.conn.commit()

    def create_base_achievements(self):
        """Создание базовых достижений"""
        base_achievements = [
            ("Первый шаг", "Сделайте первую запись в дневнике", "🎯", "total_entries", 1, 50),
            ("Начало пути", "Сделайте 5 записей в дневнике", "📝", "total_entries", 5, 100),
            ("Постоянство", "Сделайте 10 записей в дневнике", "🌟", "total_entries", 10, 200),
            ("Мастер дневника", "Сделайте 50 записей в дневнике", "📚", "total_entries", 50, 500),
            ("Новичок", "3 дня подряд ведения дневника", "🔥", "streak_days", 3, 100),
            ("Последователь", "7 дней подряд ведения дневника", "💫", "streak_days", 7, 250),
            ("Мастер привычки", "30 дней подряд ведения дневника", "🏆", "streak_days", 30, 1000),
            ("Позитивный настрой", "Отметьте настроение 8+ 5 дней подряд", "😊", "high_mood_streak", 5, 150),
            ("Эмоциональный баланс", "Проанализируйте 10 сложных ситуаций", "⚖️", "analyzed_situations", 10, 300),
            ("Детектив мыслей", "Выявите 5 когнитивных искажений", "🕵️", "distortions_found", 5, 200),
            ("Когнитивный эксперт", "Выявите 20 когнитивных искажений", "🧠", "distortions_found", 20, 500),
            ("Практик", "Выполните 5 упражнений КПТ", "🧘", "exercises_completed", 5, 150),
            ("Мастер КПТ", "Выполните 20 упражнений КПТ", "🎖️", "exercises_completed", 20, 600),
        ]

        cursor = self.conn.cursor()
        for name, desc, icon, req_type, req_value, xp in base_achievements:
            cursor.execute('''
                INSERT OR IGNORE INTO achievements (name, description, icon, requirement_type, requirement_value, xp_reward)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, desc, icon, req_type, req_value, xp))

    # ========== МЕТОДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==========

    def create_user(self, username, password, name):
        """Создание нового пользователя"""
        cursor = self.conn.cursor()
        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)

        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, salt, name)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, salt, name))

            user_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO user_stats (user_id, xp, level, streak_days, total_entries)
                VALUES (?, 0, 1, 0, 0)
            ''', (user_id,))

            self.conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None

    def authenticate_user(self, username, password):
        """Аутентификация пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, username, name, password_hash, salt 
            FROM users 
            WHERE username = ?
        ''', (username,))

        user = cursor.fetchone()
        if not user:
            return None

        input_hash = self._hash_password(password, user['salt'])
        if input_hash == user['password_hash']:
            return {
                'id': user['id'],
                'username': user['username'],
                'name': user['name']
            }
        return None

    def _hash_password(self, password, salt):
        """Хэширование пароля"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        ).hex()

    # ========== МЕТОДЫ ДЛЯ НАСТРОЕНИЯ ==========

    def save_mood_entry(self, user_id, date, mood_score, notes=None):
        """Сохранение записи настроения"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO mood_entries (user_id, date, mood_score, notes)
                VALUES (?, ?, ?, ?)
            ''', (user_id, date, mood_score, notes))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка сохранения настроения: {e}")
            return False

    def get_mood_entries(self, user_id, days=7):
        """Получение записей настроения за последние N дней"""
        cursor = self.conn.cursor()
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT date, mood_score, notes 
            FROM mood_entries 
            WHERE user_id = ? AND date >= ?
            ORDER BY date ASC
        ''', (user_id, start_date))

        return cursor.fetchall()

    def get_today_mood(self, user_id):
        """Получение настроения на сегодня"""
        today = datetime.now().strftime('%Y-%m-%d')
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT mood_score FROM mood_entries 
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))

        result = cursor.fetchone()
        return result['mood_score'] if result else None

    # ========== МЕТОДЫ ДЛЯ ДНЕВНИКА ==========

    def save_diary_entry(self, user_id, situation, emotions, thoughts,
                         distortions, alternative_thought=None, reassessment=None):
        """Сохранение записи в дневнике"""
        cursor = self.conn.cursor()
        try:
            emotions_json = json.dumps(emotions)
            distortions_json = json.dumps(distortions)

            cursor.execute('''
                INSERT INTO diary_entries 
                (user_id, situation, emotions, thoughts, distortions, 
                 alternative_thought, reassessment)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, situation, emotions_json, thoughts,
                  distortions_json, alternative_thought, reassessment))

            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Ошибка сохранения дневника: {e}")
            return None

    def get_diary_entries(self, user_id, limit=50):
        """Получение записей дневника"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM diary_entries 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))

        entries = []
        for row in cursor.fetchall():
            entry = dict(row)
            entry['emotions'] = json.loads(entry['emotions'])
            entry['distortions'] = json.loads(entry['distortions'])
            entries.append(entry)

        return entries

    def get_diary_stats(self, user_id):
        """Статистика по дневнику"""
        cursor = self.conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM diary_entries WHERE user_id = ?', (user_id,))
        total = cursor.fetchone()['count']

        cursor.execute('''
            SELECT COUNT(DISTINCT DATE(created_at)) as days 
            FROM diary_entries 
            WHERE user_id = ?
        ''', (user_id,))
        days = cursor.fetchone()['days']

        cursor.execute('''
            SELECT distortions, COUNT(*) as count
            FROM diary_entries 
            WHERE user_id = ?
            GROUP BY distortions
        ''', (user_id,))

        distortions = {}
        for row in cursor.fetchall():
            dist_list = json.loads(row['distortions'])
            for dist in dist_list:
                distortions[dist] = distortions.get(dist, 0) + 1

        return {
            'total_entries': total,
            'days_with_entries': days,
            'common_distortions': distortions
        }

    # ========== МЕТОДЫ ДЛЯ УПРАЖНЕНИЙ ==========

    def save_exercise_log(self, user_id, exercise_name, duration_minutes=None, notes=None):
        """Сохранение лога выполнения упражнения"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO exercise_logs (user_id, exercise_name, duration_minutes, notes)
            VALUES (?, ?, ?, ?)
        ''', (user_id, exercise_name, duration_minutes, notes))
        self.conn.commit()
        return cursor.lastrowid

    def get_exercise_stats(self, user_id):
        """Статистика по упражнениям"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT exercise_name, COUNT(*) as count, 
                   AVG(duration_minutes) as avg_duration
            FROM exercise_logs 
            WHERE user_id = ?
            GROUP BY exercise_name
        ''', (user_id,))

        return cursor.fetchall()

    # ========== МЕТОДЫ ДЛЯ СТАТИСТИКИ ==========

    def get_user_stats(self, user_id):
        """Получение статистики пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM user_stats WHERE user_id = ?', (user_id,))
        stats = cursor.fetchone()

        if not stats:
            cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
            if not cursor.fetchone():
                return None

            cursor.execute('''
                INSERT INTO user_stats (user_id, xp, level, streak_days, total_entries)
                VALUES (?, 0, 1, 0, 0)
            ''', (user_id,))
            self.conn.commit()

            cursor.execute('SELECT * FROM user_stats WHERE user_id = ?', (user_id,))
            stats = cursor.fetchone()

        return dict(stats) if stats else None

    def update_user_stats(self, user_id, updates_dict):
        """Обновление статистики пользователя"""
        cursor = self.conn.cursor()

        set_parts = []
        values = []

        for field, value in updates_dict.items():
            set_parts.append(f"{field} = ?")
            values.append(value)

        values.append(user_id)

        query = f'''
            UPDATE user_stats 
            SET {', '.join(set_parts)}
            WHERE user_id = ?
        '''

        cursor.execute(query, values)
        self.conn.commit()
        self.check_achievements(user_id)

    def get_level_info(self, xp):
        """Получение информации об уровне на основе XP"""
        level = int((xp / 100) ** 0.5) + 1
        xp_for_current = (level - 1) ** 2 * 100
        xp_for_next = level ** 2 * 100
        progress = (xp - xp_for_current) / (xp_for_next - xp_for_current) * 100

        return {
            'level': level,
            'xp': xp,
            'xp_for_current': xp_for_current,
            'xp_for_next': xp_for_next,
            'progress': progress,
            'xp_needed': xp_for_next - xp
        }

    # ========== МЕТОДЫ ДЛЯ ДОСТИЖЕНИЙ ==========

    def check_achievements(self, user_id):
        """Проверка выполнения достижений"""
        cursor = self.conn.cursor()
        stats = self.get_user_stats(user_id)
        if not stats:
            return []

        cursor.execute('SELECT * FROM achievements')
        achievements = cursor.fetchall()

        completed_achievements = []

        for ach in achievements:
            ach_id = ach['id']
            req_type = ach['requirement_type']
            req_value = ach['requirement_value']

            cursor.execute('''
                SELECT * FROM user_achievements 
                WHERE user_id = ? AND achievement_id = ?
            ''', (user_id, ach_id))

            user_ach = cursor.fetchone()

            if user_ach and user_ach['completed']:
                continue

            current_progress = 0
            if req_type == 'total_entries':
                current_progress = stats['total_entries']
            elif req_type == 'streak_days':
                current_progress = stats['streak_days']
            elif req_type == 'high_mood_streak':
                continue
            elif req_type == 'analyzed_situations':
                continue
            elif req_type == 'distortions_found':
                continue
            elif req_type == 'exercises_completed':
                continue

            if user_ach:
                cursor.execute('''
                    UPDATE user_achievements 
                    SET progress = ?
                    WHERE user_id = ? AND achievement_id = ?
                ''', (current_progress, user_id, ach_id))
            else:
                cursor.execute('''
                    INSERT INTO user_achievements (user_id, achievement_id, progress)
                    VALUES (?, ?, ?)
                ''', (user_id, ach_id, current_progress))

            if current_progress >= req_value and not (user_ach and user_ach['completed']):
                cursor.execute('''
                    UPDATE user_achievements 
                    SET completed = TRUE, completed_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND achievement_id = ?
                ''', (user_id, ach_id))

                new_xp = stats['xp'] + ach['xp_reward']
                self.update_user_stats(user_id, {'xp': new_xp})
                stats['xp'] = new_xp

                completed_achievements.append({
                    'name': ach['name'],
                    'description': ach['description'],
                    'icon': ach['icon'],
                    'xp': ach['xp_reward']
                })

        self.conn.commit()
        return completed_achievements

    def get_user_achievements(self, user_id, completed_only=False):
        """Получение достижений пользователя"""
        cursor = self.conn.cursor()

        if completed_only:
            cursor.execute('''
                SELECT a.*, ua.progress, ua.completed, ua.completed_at
                FROM achievements a
                JOIN user_achievements ua ON a.id = ua.achievement_id
                WHERE ua.user_id = ? AND ua.completed = TRUE
                ORDER BY ua.completed_at DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT a.*, ua.progress, ua.completed, ua.completed_at
                FROM achievements a
                LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?
                ORDER BY a.id
            ''', (user_id,))

        return cursor.fetchall()

    # ========== МЕТОДЫ ДЛЯ ДНК ПРОФИЛЯ ==========

    def save_dna_profile(self, user_id, profile_data):
        """Сохранение ДНК профиля"""
        cursor = self.conn.cursor()
        profile_json = json.dumps(profile_data, ensure_ascii=False)

        cursor.execute('''
            INSERT OR REPLACE INTO mental_health_dna (user_id, profile_data)
            VALUES (?, ?)
        ''', (user_id, profile_json))

        self.conn.commit()

    def get_dna_profile(self, user_id):
        """Получение ДНК профиля"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT profile_data FROM mental_health_dna WHERE user_id = ?', (user_id,))

        result = cursor.fetchone()
        if result:
            return json.loads(result['profile_data'])
        return None

    def save_exercise_feedback(self, user_id, entry_id, exercise_name, helped, feedback_text=None):
        """Сохранить обратную связь по упражнению"""
        cursor = self.conn.cursor()
        helped_value = 1 if helped else -1 if helped is not None else 0

        cursor.execute('''
            INSERT INTO exercise_feedback (user_id, entry_id, exercise_name, helped, feedback_text)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, entry_id, exercise_name, helped_value, feedback_text))

        self.conn.commit()
        return cursor.lastrowid

    def get_exercise_feedback_for_entry(self, entry_id):
        """Получить обратную связь для конкретной записи"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM exercise_feedback 
            WHERE entry_id = ?
            ORDER BY created_at DESC
        ''', (entry_id,))
        return cursor.fetchall()

    def get_effectiveness_stats(self, user_id, exercise_name=None):
        """Получить статистику эффективности упражнений"""
        cursor = self.conn.cursor()

        if exercise_name:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN helped = 1 THEN 1 ELSE 0 END) as helped_count,
                    SUM(CASE WHEN helped = -1 THEN 1 ELSE 0 END) as not_helped_count
                FROM exercise_feedback
                WHERE user_id = ? AND exercise_name = ?
            ''', (user_id, exercise_name))
        else:
            cursor.execute('''
                SELECT 
                    exercise_name,
                    COUNT(*) as total,
                    SUM(CASE WHEN helped = 1 THEN 1 ELSE 0 END) as helped_count
                FROM exercise_feedback
                WHERE user_id = ?
                GROUP BY exercise_name
                ORDER BY helped_count DESC
            ''', (user_id,))

        return cursor.fetchall()

    def close(self):
        """Закрытие соединения с БД"""
        if self.conn:
            self.conn.close()