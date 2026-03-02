# ai/triggers.py
"""Интеллектуальный анализ триггеров и паттернов"""

import numpy as np
from datetime import datetime


class TriggerIntelligence:
    """Интеллектуальный анализ триггеров и паттернов"""

    def __init__(self, db):
        self.db = db

    def analyze_emotional_patterns(self, user_id):
        """Глубокий анализ эмоциональных паттернов"""
        try:
            # Получаем данные
            diary_entries = self.db.get_diary_entries(user_id, limit=50)
            mood_entries = self.db.get_mood_entries(user_id, days=60)

            if not diary_entries:
                return {'has_data': False}

            analysis = {
                'has_data': True,
                'total_entries_analyzed': len(diary_entries),
                'patterns': {},
                'insights': [],
                'warning_signs': []
            }

            # Анализ временных паттернов
            time_patterns = self._analyze_time_patterns(diary_entries)
            if time_patterns:
                analysis['patterns']['time'] = time_patterns
                analysis['insights'].extend(self._generate_time_insights(time_patterns))

            # Анализ контекстных триггеров
            context_triggers = self._analyze_context_triggers(diary_entries)
            if context_triggers:
                analysis['patterns']['context'] = context_triggers
                analysis['insights'].extend(self._generate_context_insights(context_triggers))

            # Анализ когнитивных искажений
            distortion_patterns = self._analyze_distortion_patterns(diary_entries)
            if distortion_patterns:
                analysis['patterns']['distortions'] = distortion_patterns
                analysis['insights'].extend(self._generate_distortion_insights(distortion_patterns))

            # Определение предупреждающих знаков
            warning_signs = self._detect_warning_signs(mood_entries, diary_entries)
            analysis['warning_signs'] = warning_signs

            return analysis

        except Exception as e:
            print(f"Ошибка анализа паттернов: {e}")
            return {'has_data': False, 'error': str(e)}

    def _analyze_time_patterns(self, entries):
        """Анализ временных паттернов (дни недели, время суток)"""
        patterns = {
            'weekday_pattern': {},
            'time_of_day': {'утро': 0, 'день': 0, 'вечер': 0, 'ночь': 0}
        }

        for entry in entries:
            created_at = datetime.strptime(entry['created_at'], '%Y-%m-%d %H:%M:%S')
            hour = created_at.hour

            # Время суток
            if 5 <= hour < 12:
                patterns['time_of_day']['утро'] += 1
            elif 12 <= hour < 17:
                patterns['time_of_day']['день'] += 1
            elif 17 <= hour < 22:
                patterns['time_of_day']['вечер'] += 1
            else:
                patterns['time_of_day']['ночь'] += 1

            # День недели
            weekday = created_at.strftime('%A')
            if weekday not in patterns['weekday_pattern']:
                patterns['weekday_pattern'][weekday] = 0
            patterns['weekday_pattern'][weekday] += 1

        return patterns

    def _generate_time_insights(self, time_patterns):
        """Генерация инсайтов на основе временных паттернов"""
        insights = []

        time_of_day = time_patterns.get('time_of_day', {})
        if time_of_day:
            max_time = max(time_of_day.items(), key=lambda x: x[1])
            if max_time[1] > 0:
                insights.append(f"Чаще всего вы делаете записи {max_time[0]} ({max_time[1]} записей)")

        weekday_pattern = time_patterns.get('weekday_pattern', {})
        if weekday_pattern:
            max_day = max(weekday_pattern.items(), key=lambda x: x[1])
            if max_day[1] > 3:
                day_translation = {
                    'Monday': 'понедельник',
                    'Tuesday': 'вторник',
                    'Wednesday': 'среду',
                    'Thursday': 'четверг',
                    'Friday': 'пятницу',
                    'Saturday': 'субботу',
                    'Sunday': 'воскресенье'
                }
                day_rus = day_translation.get(max_day[0], max_day[0])
                insights.append(f"Наиболее активный день для рефлексии: {day_rus}")

        return insights

    def _analyze_context_triggers(self, entries):
        """Продвинутый анализ контекстных триггеров"""
        trigger_keywords = {
            'работа': ['работа', 'начальник', 'коллега', 'задача', 'дедлайн', 'проект', 'офис'],
            'отношения': ['друг', 'подруга', 'парень', 'девушка', 'муж', 'жена', 'семья', 'родители'],
            'учеба': ['учеба', 'экзамен', 'зачет', 'преподаватель', 'студент', 'лекция'],
            'здоровье': ['болезнь', 'врач', 'боль', 'усталость', 'симптом', 'лечение'],
            'финансы': ['деньги', 'зарплата', 'покупка', 'трата', 'долг', 'экономия'],
            'самооценка': ['неудачник', 'неспособен', 'бесполезен', 'недостаточно', 'провал']
        }

        triggers = {}

        for entry in entries:
            situation = entry['situation'].lower()
            emotions = entry['emotions']

            for category, keywords in trigger_keywords.items():
                for keyword in keywords:
                    if keyword in situation:
                        if category not in triggers:
                            triggers[category] = {
                                'count': 0,
                                'avg_emotional_intensity': [],
                                'common_emotions': {}
                            }

                        triggers[category]['count'] += 1

                        for emotion, intensity in emotions.items():
                            if intensity > 0:
                                triggers[category]['avg_emotional_intensity'].append(intensity)

                                if emotion not in triggers[category]['common_emotions']:
                                    triggers[category]['common_emotions'][emotion] = 0
                                triggers[category]['common_emotions'][emotion] += 1

        for category, data in triggers.items():
            if data['avg_emotional_intensity']:
                data['avg_intensity'] = sum(data['avg_emotional_intensity']) / len(data['avg_emotional_intensity'])
                data['main_emotion'] = max(data['common_emotions'].items(), key=lambda x: x[1])[0] if data[
                    'common_emotions'] else None
            else:
                data['avg_intensity'] = 0
                data['main_emotion'] = None

        return triggers

    def _generate_context_insights(self, context_triggers):
        """Генерация инсайтов на основе контекстных триггеров"""
        insights = []

        if not context_triggers:
            return insights

        most_common = max(context_triggers.items(), key=lambda x: x[1]['count'])
        if most_common[1]['count'] > 3:
            insights.append(f"Самый частый триггер: {most_common[0]} ({most_common[1]['count']} раз)")

        high_intensity_triggers = [(cat, data) for cat, data in context_triggers.items()
                                   if data.get('avg_intensity', 0) > 50]
        if high_intensity_triggers:
            high_intensity = max(high_intensity_triggers, key=lambda x: x[1]['avg_intensity'])
            insights.append(
                f"Самый эмоциональный триггер: {high_intensity[0]} (интенсивность: {high_intensity[1]['avg_intensity']:.0f}%)")

        for category, data in list(context_triggers.items())[:3]:
            if data.get('main_emotion'):
                insights.append(f"Для триггера '{category}' характерна эмоция: {data['main_emotion']}")

        return insights

    def _analyze_distortion_patterns(self, entries):
        """Анализ паттернов когнитивных искажений"""
        distortions_count = {}
        distortion_emotions = {}

        for entry in entries:
            distortions = entry.get('distortions', [])
            emotions = entry.get('emotions', {})

            for distortion in distortions:
                distortions_count[distortion] = distortions_count.get(distortion, 0) + 1

                if distortion not in distortion_emotions:
                    distortion_emotions[distortion] = {}

                for emotion, intensity in emotions.items():
                    if intensity > 0:
                        if emotion not in distortion_emotions[distortion]:
                            distortion_emotions[distortion][emotion] = []
                        distortion_emotions[distortion][emotion].append(intensity)

        patterns = {}
        for distortion, count in distortions_count.items():
            patterns[distortion] = {
                'frequency': count,
                'percentage': (count / len(entries)) * 100 if entries else 0,
                'associated_emotions': distortion_emotions.get(distortion, {})
            }

        return patterns

    def _generate_distortion_insights(self, distortion_patterns):
        """Генерация инсайтов на основе когнитивных искажений"""
        insights = []

        if not distortion_patterns:
            return insights

        most_common = max(distortion_patterns.items(), key=lambda x: x[1]['frequency'])
        if most_common[1]['frequency'] > 2:
            insights.append(
                f"Наиболее частое когнитивное искажение: '{most_common[0]}' ({most_common[1]['frequency']} раз)")

        for distortion, data in list(distortion_patterns.items())[:3]:
            emotions = data.get('associated_emotions', {})
            if emotions:
                emotion_counts = {emotion: len(intensities) for emotion, intensities in emotions.items()}
                main_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else None

                if main_emotion:
                    insights.append(f"Искажение '{distortion}' часто связано с эмоцией '{main_emotion}'")

        total_distortions = sum([data['frequency'] for data in distortion_patterns.values()])
        if total_distortions > 10:
            insights.append("Вы хорошо работаете с выявлением когнитивных искажений!")

        return insights

    def _detect_warning_signs(self, mood_entries, diary_entries):
        """Обнаружение предупреждающих знаков"""
        warnings = []

        if len(mood_entries) >= 7:
            recent_moods = [entry['mood_score'] for entry in mood_entries[-7:]]
            if np.mean(recent_moods) < 4:
                warnings.append({
                    'type': 'low_mood',
                    'severity': 'medium',
                    'message': 'Среднее настроение за неделю ниже 4/10'
                })

            if len(mood_entries) >= 2:
                last_mood = mood_entries[-1]['mood_score']
                prev_mood = mood_entries[-2]['mood_score']
                if last_mood - prev_mood < -3:
                    warnings.append({
                        'type': 'sharp_drop',
                        'severity': 'high',
                        'message': 'Резкое падение настроения'
                    })

        negative_keywords = ['безнадежно', 'беспомощно', 'устал', 'невыносимо', 'больше не могу']
        for entry in diary_entries[-10:]:
            text = entry['situation'] + ' ' + entry['thoughts']
            for keyword in negative_keywords:
                if keyword in text.lower():
                    warnings.append({
                        'type': 'negative_language',
                        'severity': 'low',
                        'message': 'Обнаружены сильные негативные формулировки'
                    })
                    break

        if len(diary_entries) >= 5:
            recent_entries = []
            for entry in diary_entries[-5:]:
                created_at = datetime.strptime(entry['created_at'], '%Y-%m-%d %H:%M:%S')
                days_ago = (datetime.now() - created_at).days
                if days_ago <= 7:
                    recent_entries.append(entry)

            if len(recent_entries) == 0 and len(diary_entries) > 10:
                warnings.append({
                    'type': 'inactivity',
                    'severity': 'low',
                    'message': 'Не было записей в течение недели'
                })

        return warnings