# ai/predictor.py
"""Интеллектуальный модуль прогнозирования настроения"""

import numpy as np
from datetime import datetime, timedelta


class MoodPredictor:
    """Интеллектуальный модуль прогнозирования настроения"""

    def __init__(self, db):
        self.db = db

    def predict_mood_trend(self, user_id, days_ahead=7):
        """Прогнозирование тренда настроения на N дней вперед"""
        try:
            # Получаем исторические данные
            history = self.db.get_mood_entries(user_id, days=90)  # 3 месяца истории

            if len(history) < 7:
                return {
                    'can_predict': False,
                    'message': 'Недостаточно данных для прогноза',
                    'required_days': 7 - len(history)
                }

            # Подготовка данных
            dates = []
            moods = []

            for entry in history:
                dates.append(datetime.strptime(entry['date'], '%Y-%m-%d'))
                moods.append(entry['mood_score'])

            # Простая линейная регрессия
            x = np.arange(len(moods))
            y = np.array(moods)

            # Рассчитываем линейный тренд
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)

            # Прогноз на будущие дни
            future_x = np.arange(len(moods), len(moods) + days_ahead)
            predictions = p(future_x)

            # Ограничиваем значения от 1 до 10
            predictions = np.clip(predictions, 1, 10)

            # Определяем направление тренда
            trend = 'повышательный' if z[0] > 0.1 else 'понижательный' if z[0] < -0.1 else 'стабильный'

            return {
                'can_predict': True,
                'trend': trend,
                'trend_strength': abs(z[0]),
                'predictions': [round(float(p), 1) for p in predictions],
                'next_week_avg': round(float(np.mean(predictions)), 1),
                'confidence': min(95, max(30, int(100 * (len(moods) / 30)))),
                'pattern': self._detect_patterns(moods),
                'recommendation': self._generate_trend_recommendation(trend, np.mean(predictions))
            }

        except Exception as e:
            print(f"Ошибка прогнозирования: {e}")
            return {'can_predict': False, 'error': str(e)}

    def _detect_patterns(self, mood_sequence):
        """Обнаружение паттернов в последовательности настроений"""
        if len(mood_sequence) < 7:
            return "недостаточно данных"

        # Простая проверка цикличности
        avg_mood = np.mean(mood_sequence)
        std_mood = np.std(mood_sequence)

        if std_mood < 1.5:
            return "стабильное настроение"
        elif std_mood > 2.5:
            return "переменчивое настроение"

        # Проверка на улучшение/ухудшение
        first_week = mood_sequence[:7] if len(mood_sequence) >= 14 else mood_sequence[:len(mood_sequence) // 2]
        last_week = mood_sequence[-7:] if len(mood_sequence) >= 14 else mood_sequence[len(mood_sequence) // 2:]

        if np.mean(last_week) - np.mean(first_week) > 1:
            return "улучшающаяся динамика"
        elif np.mean(first_week) - np.mean(last_week) > 1:
            return "ухудшающаяся динамика"

        return "смешанная динамика"

    def _generate_trend_recommendation(self, trend, avg_predicted):
        """Генерация рекомендаций на основе тренда"""
        if trend == 'повышательный':
            return "Отличная динамика! Продолжайте практики, которые вам помогают."
        elif trend == 'понижательный' and avg_predicted < 5:
            return "Рекомендуется уделить больше времени упражнениям на саморегуляцию."
        else:
            return "Рекомендуется поддерживать текущие практики."