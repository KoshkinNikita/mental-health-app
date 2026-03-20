# ai/similarity_analyzer.py
"""Анализ похожих ситуаций и рекомендации на основе прошлого опыта"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime, timedelta


class SimilarityAnalyzer:
    """Анализатор похожих ситуаций для интеллектуальных подсказок"""

    def __init__(self, db):
        self.db = db
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words=['и', 'в', 'на', 'с', 'по', 'для', 'что', 'это', 'как', 'но', 'не']
        )

    def find_similar_situations(self, user_id, current_situation, limit=3):
        """
        Поиск похожих ситуаций из прошлых записей
        Возвращает список похожих записей с оценкой схожести
        """
        try:
            # Получаем все записи пользователя
            entries = self.db.get_diary_entries(user_id, limit=100)

            if len(entries) < 2:
                return []

            # Подготавливаем тексты для сравнения
            situations = [e['situation'] for e in entries]
            all_texts = situations + [current_situation]

            # Векторизуем тексты
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)

            # Вычисляем схожесть
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # Индекс текущей ситуации
            current_idx = len(entries)

            # Получаем схожесть со всеми прошлыми записями
            similarities = list(enumerate(similarity_matrix[current_idx][:-1]))

            # Сортируем по убыванию схожести
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Берем топ-3 с схожестью > 0.3
            similar_entries = []
            for idx, score in similarities[:limit]:
                if score > 0.3:  # Порог схожести
                    entry = entries[idx]
                    similar_entries.append({
                        'entry': entry,
                        'similarity': round(score * 100, 1),
                        'date': entry['created_at'][:10],
                        'situation': entry['situation'][:100] + '...' if len(entry['situation']) > 100 else entry[
                            'situation']
                    })

            for item in similar_entries:
                entry_id = item['entry']['id']
                cursor = self.db.conn.cursor()
                cursor.execute('''
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN helped = 1 THEN 1 ELSE 0 END) as helped_count
                        FROM exercise_feedback 
                        WHERE entry_id = ?
                    ''', (entry_id,))
                stats = cursor.fetchone()

                if stats and stats['total'] > 0:
                    item['effectiveness'] = (stats['helped_count'] / stats['total']) * 100
                else:
                    item['effectiveness'] = None

            similar_entries.sort(key=lambda x: (
                    x['similarity'] * 0.6 +
                    (x.get('effectiveness', 0) * 0.4 if x.get('effectiveness') else 0)
            ), reverse=True)

            return similar_entries[:limit]



        except Exception as e:
            print(f"Ошибка анализа схожести: {e}")
            return []

    def get_recommendations_from_past(self, user_id, current_situation):
        """
        Получить рекомендации на основе прошлого опыта
        """
        similar = self.find_similar_situations(user_id, current_situation, limit=5)

        if not similar:
            return None

        recommendations = []

        for item in similar:
            entry = item['entry']

            # Анализируем, что помогло в прошлый раз
            strategies = []

            if entry.get('alternative_thought'):
                strategies.append({
                    'type': 'alternative_thought',
                    'text': entry['alternative_thought'][:100] + '...',
                    'effectiveness': self._estimate_effectiveness(entry)
                })

            if entry.get('reassessment'):
                strategies.append({
                    'type': 'reassessment',
                    'text': entry['reassessment'][:100] + '...',
                    'effectiveness': self._estimate_effectiveness(entry)
                })

            # Определяем, какие искажения были выявлены
            distortions = entry.get('distortions', [])

            recommendations.append({
                'similarity': item['similarity'],
                'date': item['date'],
                'situation': entry['situation'][:100] + '...',
                'strategies': strategies,
                'distortions': distortions,
                'emotions': entry.get('emotions', {})
            })

        # Сортируем по эффективности и схожести
        recommendations.sort(key=lambda x: (
                max([s['effectiveness'] for s in x['strategies']], default=0) * 0.6 +
                x['similarity'] * 0.4
        ), reverse=True)

        return recommendations[:3]  # Топ-3 рекомендации

    def _estimate_effectiveness(self, entry):
        """Оценка эффективности стратегии"""
        score = 50  # Базовый балл

        # Если есть переоценка эмоций, проверяем изменение
        if entry.get('reassessment'):
            # Чем длиннее переоценка, тем вероятнее, что она помогла
            score += min(30, len(entry['reassessment']) / 2)

        # Если есть альтернативная мысль
        if entry.get('alternative_thought'):
            score += 20

        # Если были выявлены искажения
        if entry.get('distortions'):
            score += len(entry['distortions']) * 5

        return min(100, score)

    def get_tips_for_situation(self, user_id, situation, emotions=None):
        """
        Генерация подсказок для текущей записи
        """
        recommendations = self.get_recommendations_from_past(user_id, situation)

        if not recommendations:
            return None

        tips = []

        for rec in recommendations:
            tip = {
                'similarity': rec['similarity'],
                'message': f"📅 {rec['date']} была похожая ситуация",
                'details': []
            }

            # Добавляем информацию об эмоциях
            if rec['emotions']:
                top_emotions = sorted(rec['emotions'].items(), key=lambda x: x[1], reverse=True)[:2]
                if top_emotions:
                    tip['details'].append(f"Эмоции: {', '.join([f'{e[0]} ({e[1]}%)' for e in top_emotions])}")

            # Добавляем информацию об искажениях
            if rec['distortions']:
                tip['details'].append(f"Искажения: {', '.join(rec['distortions'])}")

            # Добавляем информацию о том, что помогло
            for strategy in rec['strategies']:
                if strategy['type'] == 'alternative_thought':
                    tip['details'].append(f"💡 Помогла альтернативная мысль: {strategy['text']}")
                elif strategy['type'] == 'reassessment':
                    tip['details'].append(f"✨ Переоценка: {strategy['text']}")

            tips.append(tip)

        return tips