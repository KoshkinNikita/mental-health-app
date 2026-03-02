# ai/progress.py
"""Анализатор прогресса и достижения целей"""

import numpy as np
from datetime import datetime


class ProgressAnalyzer:
    """Анализатор прогресса и достижения целей"""

    def __init__(self, db):
        self.db = db

    def analyze_progress_trends(self, user_id):
        """Анализ трендов прогресса"""
        try:
            diary_entries = self.db.get_diary_entries(user_id, limit=50)
            mood_entries = self.db.get_mood_entries(user_id, days=60)
            achievements = self.db.get_user_achievements(user_id)

            if not diary_entries:
                return {'has_data': False}

            analysis = {
                'has_data': True,
                'progress_metrics': {},
                'goals_achieved': [],
                'areas_for_improvement': [],
                'progress_score': 0
            }

            # Анализ темпа записей
            entry_dates = [datetime.strptime(e['created_at'].split()[0], '%Y-%m-%d')
                           for e in diary_entries]

            if len(entry_dates) >= 2:
                intervals = []
                for i in range(1, len(entry_dates)):
                    interval = (entry_dates[i] - entry_dates[i - 1]).days
                    intervals.append(interval)

                avg_interval = sum(intervals) / len(intervals)
                analysis['progress_metrics']['avg_entry_interval'] = avg_interval

                if avg_interval <= 2:
                    analysis['goals_achieved'].append('Регулярное ведение дневника')
                else:
                    analysis['areas_for_improvement'].append('Увеличить частоту записей')

            # Анализ роста самосознания
            if len(diary_entries) >= 10:
                early_entries = diary_entries[:len(diary_entries) // 2]
                recent_entries = diary_entries[len(diary_entries) // 2:]

                early_distortions = sum(len(e.get('distortions', [])) for e in early_entries)
                recent_distortions = sum(len(e.get('distortions', [])) for e in recent_entries)

                if recent_distortions < early_distortions:
                    improvement = ((early_distortions - recent_distortions) / early_distortions * 100) \
                        if early_distortions > 0 else 0
                    analysis['progress_metrics']['distortion_reduction'] = round(improvement, 1)
                    analysis['goals_achieved'].append(f'Уменьшение когнитивных искажений на {round(improvement)}%')

            # Анализ выполнения упражнений
            exercise_stats = self.db.get_exercise_stats(user_id)
            if exercise_stats:
                total_exercises = sum([stat['count'] for stat in exercise_stats])
                analysis['progress_metrics']['exercises_completed'] = total_exercises

                if total_exercises >= 5:
                    analysis['goals_achieved'].append('Регулярное выполнение упражнений КПТ')

            # Рассчитываем общий балл прогресса
            progress_score = 0

            total_entries = len(diary_entries)
            if total_entries >= 20:
                progress_score += 30
            elif total_entries >= 10:
                progress_score += 20
            elif total_entries >= 5:
                progress_score += 10

            completed_achievements = [a for a in achievements if a['completed']]
            progress_score += len(completed_achievements) * 5

            if 'exercises_completed' in analysis['progress_metrics']:
                if analysis['progress_metrics']['exercises_completed'] >= 10:
                    progress_score += 20
                elif analysis['progress_metrics']['exercises_completed'] >= 5:
                    progress_score += 10

            analysis['progress_score'] = min(100, progress_score)

            if progress_score >= 80:
                analysis['progress_level'] = 'Продвинутый'
            elif progress_score >= 50:
                analysis['progress_level'] = 'Средний'
            elif progress_score >= 20:
                analysis['progress_level'] = 'Начинающий'
            else:
                analysis['progress_level'] = 'Новичок'

            if progress_score < 50:
                analysis['areas_for_improvement'].append('Увеличить количество записей')
                analysis['areas_for_improvement'].append('Попробовать больше упражнений КПТ')

            return analysis

        except Exception as e:
            print(f"Ошибка анализа прогресса: {e}")
            return {'has_data': False, 'error': str(e)}

    def generate_progress_goals(self, user_id, period_days=30):
        """Генерация целей на основе текущего прогресса"""
        try:
            goals = []

            diary_stats = self.db.get_diary_stats(user_id)
            user_stats = self.db.get_user_stats(user_id)

            if not diary_stats or not user_stats:
                return goals

            current_entries = diary_stats['total_entries']
            current_streak = user_stats['streak_days']

            if current_entries < 10:
                goal_entries = 10
                goals.append({
                    'type': 'entries',
                    'target': goal_entries,
                    'current': current_entries,
                    'description': f'Достичь {goal_entries} записей в дневнике',
                    'reward_xp': 100
                })
            elif current_entries < 30:
                goal_entries = 30
                goals.append({
                    'type': 'entries',
                    'target': goal_entries,
                    'current': current_entries,
                    'description': f'Достичь {goal_entries} записей в дневнике',
                    'reward_xp': 200
                })

            if current_streak < 7:
                goal_streak = 7
                goals.append({
                    'type': 'streak',
                    'target': goal_streak,
                    'current': current_streak,
                    'description': f'Вести дневник {goal_streak} дней подряд',
                    'reward_xp': 150
                })
            elif current_streak < 30:
                goal_streak = 30
                goals.append({
                    'type': 'streak',
                    'target': goal_streak,
                    'current': current_streak,
                    'description': f'Вести дневник {goal_streak} дней подряд',
                    'reward_xp': 500
                })

            exercise_stats = self.db.get_exercise_stats(user_id)
            total_exercises = sum([stat['count'] for stat in exercise_stats]) if exercise_stats else 0

            if total_exercises < 5:
                goal_exercises = 5
                goals.append({
                    'type': 'exercises',
                    'target': goal_exercises,
                    'current': total_exercises,
                    'description': f'Выполнить {goal_exercises} упражнений КПТ',
                    'reward_xp': 100
                })

            mood_entries = self.db.get_mood_entries(user_id, days=30)
            if mood_entries and len(mood_entries) >= 7:
                mood_scores = [entry['mood_score'] for entry in mood_entries[-7:]]
                avg_mood = sum(mood_scores) / len(mood_scores)

                if avg_mood < 6:
                    goals.append({
                        'type': 'mood',
                        'target': 6,
                        'current': round(avg_mood, 1),
                        'description': f'Повысить среднее настроение до 6/10',
                        'reward_xp': 150
                    })

            return goals

        except Exception as e:
            print(f"Ошибка генерации целей: {e}")
            return []