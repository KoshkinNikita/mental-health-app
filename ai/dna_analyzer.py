# ai/dna_analyzer.py
"""Анализатор для создания индивидуального профиля ментального здоровья"""

import numpy as np
from datetime import datetime


class MentalHealthDNAAnalyzer:
    """Анализатор для создания индивидуального профиля ментального здоровья"""

    def __init__(self, db):
        self.db = db

    def generate_dna_profile(self, user_id):
        """Генерация профиля ДНК ментального здоровья"""
        # Собираем данные за последние 30 дней
        diary_entries = self.db.get_diary_entries(user_id, limit=100)
        mood_entries = self.db.get_mood_entries(user_id, days=30)
        exercise_logs = self.db.get_exercise_stats(user_id)

        profile = {
            'user_id': user_id,
            'generated_at': datetime.now().isoformat(),
            'data_period_days': 30,
            'total_entries': len(diary_entries),

            # 1. ПАТТЕРНЫ МЫШЛЕНИЯ
            'thinking_patterns': self._analyze_thinking_patterns(diary_entries),

            # 2. ЭМОЦИОНАЛЬНЫЙ ЛАНДШАФТ
            'emotional_landscape': self._analyze_emotions(diary_entries, mood_entries),

            # 3. ТРИГГЕРЫ И РЕАКЦИИ
            'triggers': self._analyze_triggers(diary_entries),

            # 4. ЭФФЕКТИВНЫЕ СТРАТЕГИИ
            'effective_strategies': self._analyze_strategies(diary_entries, exercise_logs),

            # 5. ЦИКЛЫ И ТРЕНДЫ
            'cycles_trends': self._analyze_cycles(mood_entries),

            # 6. РЕКОМЕНДАЦИИ
            'personalized_recommendations': []
        }

        # Генерация рекомендаций
        profile['personalized_recommendations'] = self._generate_recommendations(profile)

        return profile

    def _analyze_thinking_patterns(self, entries):
        """Анализ паттернов мышления"""
        if not entries:
            return {}

        distortions_count = {}
        situations_by_distortion = {}

        for entry in entries:
            distortions = entry.get('distortions', [])
            situation = entry.get('situation', '')

            for distortion in distortions:
                distortions_count[distortion] = distortions_count.get(distortion, 0) + 1

                if distortion not in situations_by_distortion:
                    situations_by_distortion[distortion] = []
                situations_by_distortion[distortion].append(situation[:100])

        total_distortions = sum(distortions_count.values())
        patterns = {}

        for distortion, count in distortions_count.items():
            percentage = (count / total_distortions * 100) if total_distortions > 0 else 0
            typical_situations = situations_by_distortion.get(distortion, [])[:3]

            patterns[distortion] = {
                'frequency': count,
                'percentage': round(percentage, 1),
                'strength': 'высокая' if percentage > 30 else 'средняя' if percentage > 15 else 'низкая',
                'typical_situations': typical_situations,
                'description': self._get_distortion_description(distortion)
            }

        sorted_patterns = dict(sorted(patterns.items(),
                                      key=lambda x: x[1]['frequency'],
                                      reverse=True))

        return {
            'dominant_patterns': dict(list(sorted_patterns.items())[:3]),
            'all_patterns': sorted_patterns,
            'total_analyzed': len(entries)
        }

    def _analyze_emotions(self, diary_entries, mood_entries):
        """Анализ эмоционального ландшафта"""
        emotion_intensity = {}
        emotion_frequency = {}

        for entry in diary_entries:
            emotions = entry.get('emotions', {})
            for emotion, intensity in emotions.items():
                if intensity > 0:
                    emotion_frequency[emotion] = emotion_frequency.get(emotion, 0) + 1
                    if emotion not in emotion_intensity:
                        emotion_intensity[emotion] = []
                    emotion_intensity[emotion].append(intensity)

        mood_scores = [entry['mood_score'] for entry in mood_entries] if mood_entries else []
        avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0

        avg_intensity = {}
        for emotion, intensities in emotion_intensity.items():
            avg_intensity[emotion] = sum(intensities) / len(intensities)

        dominant_emotions = {}
        if emotion_frequency:
            total_entries = len(diary_entries)
            for emotion, freq in emotion_frequency.items():
                percentage = (freq / total_entries * 100) if total_entries > 0 else 0
                dominant_emotions[emotion] = {
                    'frequency': freq,
                    'percentage': round(percentage, 1),
                    'avg_intensity': round(avg_intensity.get(emotion, 0), 1),
                    'strength': 'сильная' if avg_intensity.get(emotion, 0) > 70
                    else 'средняя' if avg_intensity.get(emotion, 0) > 40
                    else 'слабая'
                }

        sorted_emotions = dict(sorted(dominant_emotions.items(),
                                      key=lambda x: x[1]['frequency'],
                                      reverse=True))

        return {
            'dominant_emotions': dict(list(sorted_emotions.items())[:5]),
            'mood_analysis': {
                'avg_mood': round(avg_mood, 1),
                'mood_stability': self._calculate_mood_stability(mood_scores),
                'best_day': max(mood_scores) if mood_scores else 0,
                'worst_day': min(mood_scores) if mood_scores else 0
            },
            'emotional_range': len(dominant_emotions)
        }

    def _analyze_triggers(self, entries):
        """Анализ триггеров"""
        if not entries:
            return {}

        trigger_categories = {
            'работа': ['работа', 'коллега', 'начальник', 'задача', 'проект', 'дедлайн'],
            'отношения': ['друг', 'подруга', 'парень', 'девушка', 'муж', 'жена', 'семья', 'родители'],
            'учеба': ['учеба', 'экзамен', 'зачет', 'преподаватель', 'студент'],
            'здоровье': ['здоровье', 'болезнь', 'врач', 'боль', 'усталость'],
            'финансы': ['деньги', 'зарплата', 'покупка', 'трата', 'экономия']
        }

        triggers = {}

        for entry in entries:
            situation = entry.get('situation', '').lower()
            emotions = entry.get('emotions', {})

            for category, keywords in trigger_categories.items():
                for keyword in keywords:
                    if keyword in situation:
                        if category not in triggers:
                            triggers[category] = {
                                'count': 0,
                                'typical_emotions': {},
                                'examples': []
                            }

                        triggers[category]['count'] += 1

                        for emotion, intensity in emotions.items():
                            if intensity > 0:
                                triggers[category]['typical_emotions'][emotion] = \
                                    triggers[category]['typical_emotions'].get(emotion, 0) + intensity

                        if len(triggers[category]['examples']) < 3:
                            triggers[category]['examples'].append(situation[:50] + '...')
                        break

        for category, data in triggers.items():
            total_emotions = sum(data['typical_emotions'].values())
            emotion_count = len(data['typical_emotions'])

            if emotion_count > 0:
                data['avg_emotional_intensity'] = round(total_emotions / emotion_count, 1)

                if data['typical_emotions']:
                    main_emotion = max(data['typical_emotions'].items(), key=lambda x: x[1])
                    data['main_emotion'] = {
                        'name': main_emotion[0],
                        'intensity': main_emotion[1]
                    }

        return triggers

    def _analyze_strategies(self, diary_entries, exercise_logs):
        """Анализ эффективных стратегий"""
        strategies = {}

        for entry in diary_entries:
            alternative = entry.get('alternative_thought')

            if alternative:
                strategy_type = self._classify_strategy(alternative)

                if strategy_type not in strategies:
                    strategies[strategy_type] = {
                        'count': 0,
                        'examples': [],
                        'effectiveness': []
                    }

                strategies[strategy_type]['count'] += 1

                if len(strategies[strategy_type]['examples']) < 3:
                    strategies[strategy_type]['examples'].append(alternative[:100] + '...')

        exercise_effectiveness = {}
        if exercise_logs:
            for log in exercise_logs:
                exercise = log['exercise_name']
                exercise_effectiveness[exercise] = exercise_effectiveness.get(exercise, 0) + 1

        return {
            'cognitive_strategies': strategies,
            'exercise_preferences': exercise_effectiveness,
            'most_used_strategy': max(strategies.items(), key=lambda x: x[1]['count'])[0] if strategies else None
        }

    def _analyze_cycles(self, mood_entries):
        """Анализ циклов и трендов"""
        if not mood_entries or len(mood_entries) < 7:
            return {'insufficient_data': True}

        days_of_week = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        mood_by_day = {day: [] for day in days_of_week}

        for entry in mood_entries:
            date_obj = datetime.strptime(entry['date'], '%Y-%m-%d')
            day_index = date_obj.weekday()
            day_name = days_of_week[day_index]
            mood_by_day[day_name].append(entry['mood_score'])

        avg_by_day = {}
        for day, scores in mood_by_day.items():
            if scores:
                avg_by_day[day] = sum(scores) / len(scores)

        if avg_by_day:
            best_day = max(avg_by_day.items(), key=lambda x: x[1])
            worst_day = min(avg_by_day.items(), key=lambda x: x[1])
        else:
            best_day = worst_day = (None, 0)

        mood_scores = [entry['mood_score'] for entry in mood_entries]
        if len(mood_scores) >= 2:
            trend = mood_scores[-1] - mood_scores[0]
            trend_direction = 'улучшение' if trend > 0.5 else 'ухудшение' if trend < -0.5 else 'стабильно'
        else:
            trend_direction = 'недостаточно данных'

        return {
            'weekly_pattern': avg_by_day,
            'best_day': {'day': best_day[0], 'mood': round(best_day[1], 1)} if best_day[0] else None,
            'worst_day': {'day': worst_day[0], 'mood': round(worst_day[1], 1)} if worst_day[0] else None,
            'trend': trend_direction,
            'consistency': self._calculate_consistency(mood_scores)
        }

    def _generate_recommendations(self, profile):
        """Генерация персонализированных рекомендаций"""
        recommendations = []

        thinking_patterns = profile['thinking_patterns'].get('dominant_patterns', {})
        for pattern, data in thinking_patterns.items():
            if data['strength'] == 'высокая':
                recommendations.append({
                    'type': 'thinking_pattern',
                    'priority': 'high',
                    'title': f'Работа с "{pattern}"',
                    'description': self._get_pattern_recommendation(pattern),
                    'exercises': self._get_exercises_for_pattern(pattern)
                })

        emotions = profile['emotional_landscape'].get('dominant_emotions', {})
        for emotion, data in emotions.items():
            if data['avg_intensity'] > 60:
                recommendations.append({
                    'type': 'emotion',
                    'priority': 'medium',
                    'title': f'Управление {emotion.lower()}',
                    'description': f'Вы часто испытываете {emotion.lower()} высокой интенсивности',
                    'exercises': ['Дыхание 4-7-8', 'Техника заземления']
                })

        triggers = profile['triggers']
        if triggers:
            main_trigger = max(triggers.items(), key=lambda x: x[1]['count'])[0]
            recommendations.append({
                'type': 'trigger',
                'priority': 'medium',
                'title': f'Триггер: {main_trigger}',
                'description': f'Чаще всего сложные ситуации связаны с {main_trigger.lower()}',
                'suggestion': 'Проанализируйте, что именно в этой сфере вызывает реакции'
            })

        if profile['emotional_landscape'].get('mood_analysis', {}).get('avg_mood', 0) < 5:
            recommendations.append({
                'type': 'general',
                'priority': 'high',
                'title': 'Повышение общего настроения',
                'description': 'Среднее настроение ниже 5/10',
                'exercises': ['Визуализация позитивного образа', 'Дневник благодарности']
            })

        return recommendations[:5]

    def _calculate_mood_stability(self, mood_scores):
        if len(mood_scores) < 2:
            return 0
        return round(10 - np.std(mood_scores), 1)

    def _calculate_consistency(self, values):
        if len(values) < 2:
            return 0
        avg = sum(values) / len(values)
        deviations = sum(abs(v - avg) for v in values)
        return round(100 - (deviations / len(values) * 10), 1)

    def _get_distortion_description(self, distortion):
        descriptions = {
            'катастрофизация': 'Склонность преувеличивать негативные последствия',
            'долженствование': 'Использование жёстких правил "должен/обязан"',
            'чёрно-белое мышление': 'Видение ситуаций только в крайностях',
            'персонализация': 'Принятие событий на свой счёт',
            'чтение мыслей': 'Уверенность в знании мыслей других'
        }
        return descriptions.get(distortion, 'Когнитивное искажение')

    def _classify_strategy(self, text):
        text_lower = text.lower()
        if 'возможно' in text_lower or 'может быть' in text_lower:
            return 'гибкое мышление'
        elif 'альтернатива' in text_lower or 'другой взгляд' in text_lower:
            return 'рассмотрение альтернатив'
        elif 'важно' in text_lower or 'ценность' in text_lower:
            return 'фокусировка на ценностях'
        else:
            return 'когнитивная переоценка'

    def _get_pattern_recommendation(self, pattern):
        recommendations = {
            'катастрофизация': 'Попробуйте технику "Наихудший/наилучший/реалистичный сценарий"',
            'долженствование': 'Замените "должен" на "хотел бы" или "предпочитаю"',
            'чёрно-белое мышление': 'Ищите оттенки серого - что между крайностями?',
            'персонализация': 'Спросите: "Какие другие факторы могли повлиять?"',
            'чтение мыслей': 'Проверяйте предположения, задавайте вопросы'
        }
        return recommendations.get(pattern, 'Практикуйте когнитивную реструктуризацию')

    def _get_exercises_for_pattern(self, pattern):
        exercises = {
            'катастрофизация': ['Дектастрофизация', 'Шкала вероятности'],
            'долженствование': ['Гибкие правила', 'Переформулирование "должен"'],
            'чёрно-белое мышление': ['Континуум мышления', 'Поиск исключений'],
            'персонализация': ['Круг влияния', 'Мультипричинность'],
            'чтение мыслей': ['Проверка доказательств', 'Альтернативные объяснения']
        }
        return exercises.get(pattern, ['Когнитивная реструктуризация'])