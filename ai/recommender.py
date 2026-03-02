# ai/recommender.py
"""Интеллектуальная система рекомендаций"""

import numpy as np
from datetime import datetime


class IntelligentRecommender:
    """Интеллектуальная система рекомендаций"""

    def __init__(self, db):
        self.db = db

    def generate_personalized_recommendations(self, user_id):
        """Генерация персонализированных рекомендаций"""
        try:
            recommendations = []

            diary_stats = self.db.get_diary_stats(user_id)
            mood_entries = self.db.get_mood_entries(user_id, days=30)
            user_stats = self.db.get_user_stats(user_id)

            if not diary_stats or not user_stats:
                return [{
                    'title': 'Начните использование',
                    'description': 'Создайте первую запись в дневнике, чтобы получить персонализированные рекомендации',
                    'priority': 'medium',
                    'category': 'начало'
                }]

            # 1. Рекомендации по частоте записей
            total_entries = diary_stats['total_entries']
            if total_entries < 5:
                recommendations.append({
                    'title': 'Увеличьте частоту записей',
                    'description': f'У вас {total_entries} записей. Цель: 10 записей для точного анализа',
                    'priority': 'high',
                    'category': 'частота'
                })
            elif total_entries < 20:
                recommendations.append({
                    'title': 'Отличный старт!',
                    'description': f'Уже {total_entries} записей. Продолжайте в том же духе',
                    'priority': 'low',
                    'category': 'частота'
                })

            # 2. Рекомендации по дням подряд
            streak_days = user_stats['streak_days']
            if streak_days >= 3:
                recommendations.append({
                    'title': 'Отличная серия!',
                    'description': f'Вы ведете дневник {streak_days} дней подряд. Так держать!',
                    'priority': 'low',
                    'category': 'привычка'
                })
            elif streak_days == 0:
                recommendations.append({
                    'title': 'Начните серию',
                    'description': 'Попробуйте вести дневник хотя бы 3 дня подряд',
                    'priority': 'medium',
                    'category': 'привычка'
                })

            # 3. Рекомендации по настроению
            if mood_entries:
                mood_scores = [entry['mood_score'] for entry in mood_entries]
                avg_mood = sum(mood_scores) / len(mood_scores)

                if avg_mood < 4:
                    recommendations.append({
                        'title': 'Повышение настроения',
                        'description': f'Среднее настроение: {avg_mood:.1f}/10. Попробуйте упражнения на поднятие настроения',
                        'priority': 'high',
                        'category': 'настроение'
                    })
                elif avg_mood > 7:
                    recommendations.append({
                        'title': 'Отличное настроение!',
                        'description': f'Среднее настроение: {avg_mood:.1f}/10. Продолжайте текущие практики',
                        'priority': 'low',
                        'category': 'настроение'
                    })

                if len(mood_scores) >= 7:
                    mood_std = np.std(mood_scores)
                    if mood_std > 2:
                        recommendations.append({
                            'title': 'Стабильность настроения',
                            'description': 'Настроение сильно колеблется. Попробуйте упражнения на эмоциональную регуляцию',
                            'priority': 'medium',
                            'category': 'стабильность'
                        })

            # 4. Рекомендации по когнитивным искажениям
            if diary_stats.get('common_distortions'):
                most_common_distortion = max(diary_stats['common_distortions'].items(),
                                             key=lambda x: x[1],
                                             default=('', 0))

                if most_common_distortion[1] > 3:
                    distortion_name = most_common_distortion[0]
                    exercises = self._get_exercises_for_distortion(distortion_name)

                    recommendations.append({
                        'title': f'Работа с "{distortion_name}"',
                        'description': f'Обнаружено {most_common_distortion[1]} раз. Упражнения: {", ".join(exercises[:2])}',
                        'priority': 'medium',
                        'category': 'когнитивные искажения',
                        'exercises': exercises
                    })

            # 5. Общие рекомендации на основе времени
            current_hour = datetime.now().hour
            if 22 <= current_hour or current_hour <= 5:
                recommendations.append({
                    'title': 'Время для отдыха',
                    'description': 'Поздний вечер/ночь. Рекомендуется техника расслабления перед сном',
                    'priority': 'medium',
                    'category': 'время суток'
                })

            # Сортируем по приоритету
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            recommendations.sort(key=lambda x: priority_order[x['priority']])

            return recommendations[:5]

        except Exception as e:
            print(f"Ошибка генерации рекомендаций: {e}")
            return [{
                'title': 'Общая рекомендация',
                'description': 'Регулярно ведите дневник для получения персонализированных советов',
                'priority': 'medium',
                'category': 'общее'
            }]

    def _get_exercises_for_distortion(self, distortion_name):
        """Получение упражнений для конкретного когнитивного искажения"""
        exercises_map = {
            'катастрофизация': ['Дектастрофизация', 'Шкала вероятности', 'Наихудший сценарий'],
            'чёрно-белое мышление': ['Континуум мышления', 'Поиск исключений', 'Оттенки серого'],
            'долженствование': ['Гибкие правила', 'Переформулирование "должен"', 'Разрешение себе'],
            'персонализация': ['Круг влияния', 'Мультипричинность', 'Внешние факторы'],
            'чтение мыслей': ['Проверка доказательств', 'Альтернативные объяснения', 'Прямой вопрос']
        }
        return exercises_map.get(distortion_name, ['Когнитивная реструктуризация', 'Анализ мыслей'])