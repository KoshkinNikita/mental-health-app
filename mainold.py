# app_qt.py


import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout, Bidirectional
import pickle
import os

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder
import re
from collections import Counter
import sys
import random
import json
import hashlib
import secrets
from datetime import datetime, timedelta

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import matplotlib

matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np
import sqlite3


try:
    import pygame
except ImportError:
    pygame = None
    print("Pygame не установлен. Музыка будет в демо-режиме.")

class AnimatedStackedWidget(QStackedWidget):
    """StackedWidget с анимацией перехода между окнами"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation_duration = 400  # длительность в ms
        self.next_index = None
        self.current_animation = None

    def setCurrentIndexWithAnimation(self, index):
        """Плавный переход к окну с индексом index"""
        if index == self.currentIndex():
            return

        # Если уже есть анимация, останавливаем
        if self.current_animation:
            self.current_animation.stop()

        self.next_index = index
        self.start_animation()

    def start_animation(self):
        """Запуск анимации перехода"""
        current_widget = self.currentWidget()
        next_widget = self.widget(self.next_index)

        if not current_widget or not next_widget:
            super().setCurrentIndex(self.next_index)
            return

        # Позиционируем следующее окно
        if self.next_index > self.currentIndex():
            # Переход ВПРАВО (новое окно справа)
            next_widget.move(self.width(), 0)
        else:
            # Переход ВЛЕВО (новое окно слева)
            next_widget.move(-self.width(), 0)

        next_widget.show()
        next_widget.raise_()

        # Анимация текущего окна (уходит)
        anim_current = QPropertyAnimation(current_widget, b"pos")
        anim_current.setDuration(self.animation_duration)
        anim_current.setStartValue(QPoint(0, 0))

        if self.next_index > self.currentIndex():
            anim_current.setEndValue(QPoint(-self.width(), 0))
        else:
            anim_current.setEndValue(QPoint(self.width(), 0))

        anim_current.setEasingCurve(QEasingCurve.OutCubic)

        # Анимация следующего окна (приходит)
        anim_next = QPropertyAnimation(next_widget, b"pos")
        anim_next.setDuration(self.animation_duration)
        anim_next.setStartValue(next_widget.pos())
        anim_next.setEndValue(QPoint(0, 0))
        anim_next.setEasingCurve(QEasingCurve.OutCubic)

        # Завершаем переход
        anim_next.finished.connect(lambda: self.finish_animation())

        # Запускаем анимации
        anim_current.start()
        anim_next.start()

        self.current_animation = anim_next

    def finish_animation(self):
        """Завершение анимации"""
        if self.current_animation:
            self.current_animation.stop()
            self.current_animation = None

        super().setCurrentIndex(self.next_index)

        # Возвращаем все окна в нормальное положение
        for i in range(self.count()):
            widget = self.widget(i)
            widget.move(0, 0)


class AchievementsWidget(QWidget):
    """Виджет для отображения достижений"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Заголовок
        title_label = QLabel("🏆 Достижения")
        title_label.setProperty("class", "TitleMedium")
        layout.addWidget(title_label)

        # Прокручиваемая область для достижений
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        self.achievements_layout = QVBoxLayout(content_widget)
        self.achievements_layout.setSpacing(10)

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

    def update_achievements(self, user_id):
        """Обновление списка достижений"""
        # Очищаем старые достижения
        while self.achievements_layout.count():
            item = self.achievements_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not user_id:
            return

        # Получаем достижения пользователя
        achievements = self.parent_app.db.get_user_achievements(user_id)

        if not achievements:
            no_achievements = QLabel("Начните использовать приложение, чтобы получить достижения!")
            no_achievements.setProperty("class", "TextSecondary")
            no_achievements.setAlignment(Qt.AlignCenter)
            self.achievements_layout.addWidget(no_achievements)
            return

        for ach in achievements:
            achievement_card = self.create_achievement_card(ach)
            self.achievements_layout.addWidget(achievement_card)

        self.achievements_layout.addStretch()

    def create_achievement_card(self, achievement):
        """Создание карточки достижения"""
        card = QFrame()
        card.setProperty("class", "Card")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Иконка
        icon_label = QLabel(achievement['icon'])
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                min-width: 50px;
            }
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Информация
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(5)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Название
        name_label = QLabel(achievement['name'])
        name_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #5A5A5A;
            }
        """)
        info_layout.addWidget(name_label)

        # Описание
        desc_label = QLabel(achievement['description'])
        desc_label.setProperty("class", "TextSecondary")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        # Прогресс
        if achievement['completed']:
            progress_text = f"✅ Выполнено!"
            if achievement['completed_at']:
                date = achievement['completed_at'].split()[0]
                progress_text += f" ({date})"
        else:
            progress = achievement['progress'] or 0
            required = achievement['requirement_value']
            percentage = min(100, int((progress / required) * 100))
            progress_text = f"Прогресс: {progress}/{required} ({percentage}%)"

        progress_label = QLabel(progress_text)
        progress_label.setProperty("class", "TextLight")
        info_layout.addWidget(progress_label)

        layout.addWidget(info_widget, 1)

        # XP
        if achievement['completed']:
            xp_label = QLabel(f"+{achievement['xp_reward']} XP")
            xp_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #FFD166;
                    background-color: rgba(255, 209, 102, 0.1);
                    padding: 5px 10px;
                    border-radius: 10px;
                }
            """)
            layout.addWidget(xp_label)

        return card


class DNAProfileWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.analyzer = MentalHealthDNAAnalyzer(parent.db)
        self.visualization = DNAVisualizationWidget()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Верхняя панель
        top_bar = self.create_top_bar()
        layout.addWidget(top_bar)

        # Загрузка/генерация
        load_frame = QFrame()
        load_layout = QHBoxLayout(load_frame)

        generate_btn = QPushButton("🔄 Сгенерировать профиль")
        generate_btn.setProperty("class", "PrimaryButton")
        generate_btn.clicked.connect(self.generate_profile)
        load_layout.addWidget(generate_btn)

        export_btn = QPushButton("📤 Экспорт в PDF")
        export_btn.setProperty("class", "SecondaryButton")
        export_btn.clicked.connect(self.export_profile)
        load_layout.addWidget(export_btn)

        layout.addWidget(load_frame)

        # Визуализация
        layout.addWidget(self.visualization)

    def create_top_bar(self):
        """Создание верхней панели"""
        top_bar = QFrame()
        top_bar.setFixedHeight(70)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #F8F2E9;
                border-bottom: 1px solid #E8DFD8;
            }
        """)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(30, 0, 30, 0)

        # Кнопка назад
        back_btn = QPushButton("← Назад")
        back_btn.setProperty("class", "SecondaryButton")
        back_btn.clicked.connect(
            lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(1)
        )
        top_layout.addWidget(back_btn)

        top_layout.addStretch()

        # Название
        title = QLabel("🧬 Профиль ДНК ментального здоровья")
        title.setProperty("class", "TitleMedium")
        top_layout.addWidget(title)

        top_layout.addStretch()

        # Заглушка для выравнивания
        dummy_btn = QPushButton()
        dummy_btn.setFixedSize(back_btn.sizeHint())
        dummy_btn.setVisible(False)
        top_layout.addWidget(dummy_btn)

        return top_bar

    def generate_profile(self):
        if not self.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему")
            return

        # Показываем индикатор загрузки
        progress = QProgressDialog("Анализ ваших данных...", "Отмена", 0, 100, self)
        progress.setWindowTitle("Генерация профиля")
        progress.show()

        # Генерация профиля (в отдельном потоке для больших данных)
        profile = self.analyzer.generate_dna_profile(self.parent.current_user['id'])

        # Сохранение в БД
        self.parent.db.save_dna_profile(self.parent.current_user['id'], profile)

        progress.close()

        # Обновление визуализации
        self.visualization.update_profile(profile)

        QMessageBox.information(self, "Готово", "Профиль успешно сгенерирован!")

    def export_profile(self):
        """Экспорт профиля в PDF"""
        QMessageBox.information(self, "Экспорт", "Функция экспорта в PDF будет доступна в следующем обновлении")

    def update_profile(self):
        """Обновление отображения профиля"""
        if not self.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему для просмотра профиля")
            return

        # Получаем профиль из БД
        profile = self.parent.db.get_dna_profile(self.parent.current_user['id'])

        if profile:
            # Обновляем визуализацию
            self.visualization.update_profile(profile)
            QMessageBox.information(self, "Профиль загружен", "Ваш профиль успешно загружен из базы данных")
        else:
            QMessageBox.information(self, "Профиль не найден",
                                    "У вас пока нет сгенерированного профиля.\n\n"
                                    "Нажмите 'Сгенерировать профиль' для создания анализа")


class ProgressWidget(QWidget):
    """Виджет прогресса пользователя"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # Карточка прогресса
        self.progress_card = QFrame()
        self.progress_card.setProperty("class", "MintCard")

        card_layout = QVBoxLayout(self.progress_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # Уровень
        self.level_label = QLabel("Уровень 1")
        self.level_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #5A5A5A;
            }
        """)
        self.level_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.level_label)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 20px;
                border-radius: 10px;
                background-color: #E8DFD8;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #B5E5CF;
                border-radius: 10px;
            }
        """)
        card_layout.addWidget(self.progress_bar)

        # XP
        self.xp_label = QLabel("0/100 XP")
        self.xp_label.setProperty("class", "TextRegular")
        self.xp_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.xp_label)

        layout.addWidget(self.progress_card)

        # Статистика
        stats_frame = QFrame()
        stats_frame.setProperty("class", "WarmCard")

        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(15, 15, 15, 15)
        stats_layout.setSpacing(10)

        stats_title = QLabel("📊 Ваша статистика")
        stats_title.setProperty("class", "TitleSmall")
        stats_layout.addWidget(stats_title)

        # Показатели
        self.stats_labels = {}
        stats_data = [
            ("🔥", "Дней подряд", "streak_days"),
            ("📝", "Всего записей", "total_entries"),
            ("🏆", "Достижений", "achievements_completed"),
            ("🎯", "Текущий уровень", "level"),
        ]

        for icon, text, key in stats_data:
            stat_frame = QFrame()
            stat_layout = QHBoxLayout(stat_frame)
            stat_layout.setContentsMargins(0, 0, 0, 0)

            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 16px;")
            stat_layout.addWidget(icon_label)

            text_label = QLabel(text)
            text_label.setProperty("class", "TextSecondary")
            stat_layout.addWidget(text_label)

            stat_layout.addStretch()

            value_label = QLabel("0")
            value_label.setProperty("class", "TextRegular")
            value_label.setStyleSheet("font-weight: bold;")
            stat_layout.addWidget(value_label)

            self.stats_labels[key] = value_label
            stats_layout.addWidget(stat_frame)

        layout.addWidget(stats_frame)

    def update_progress(self, user_id):
        """Обновление прогресса пользователя"""
        if not user_id:
            return

        stats = self.parent_app.db.get_user_stats(user_id)
        if not stats:
            return

        # Получаем информацию об уровне
        level_info = self.parent_app.db.get_level_info(stats['xp'])

        # Обновляем уровень
        self.level_label.setText(f"Уровень {level_info['level']}")
        self.progress_bar.setValue(int(level_info['progress']))
        self.xp_label.setText(f"{stats['xp']}/{level_info['xp_for_next']} XP")

        # Обновляем статистику
        self.stats_labels['streak_days'].setText(str(stats['streak_days']))
        self.stats_labels['total_entries'].setText(str(stats['total_entries']))
        self.stats_labels['level'].setText(str(level_info['level']))

        # Получаем количество выполненных достижений
        cursor = self.parent_app.db.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM user_achievements 
            WHERE user_id = ? AND completed = TRUE
        ''', (user_id,))
        completed_count = cursor.fetchone()['count']
        self.stats_labels['achievements_completed'].setText(str(completed_count))


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
                situations_by_distortion[distortion].append(situation[:100])  # Первые 100 символов

        # Определяем доминирующие искажения
        total_distortions = sum(distortions_count.values())
        patterns = {}

        for distortion, count in distortions_count.items():
            percentage = (count / total_distortions * 100) if total_distortions > 0 else 0

            # Типичные ситуации для этого искажения
            typical_situations = situations_by_distortion.get(distortion, [])[:3]  # 3 примера

            patterns[distortion] = {
                'frequency': count,
                'percentage': round(percentage, 1),
                'strength': 'высокая' if percentage > 30 else 'средняя' if percentage > 15 else 'низкая',
                'typical_situations': typical_situations,
                'description': self._get_distortion_description(distortion)
            }

        # Сортируем по частоте
        sorted_patterns = dict(sorted(patterns.items(),
                                      key=lambda x: x[1]['frequency'],
                                      reverse=True))

        return {
            'dominant_patterns': dict(list(sorted_patterns.items())[:3]),  # Топ-3
            'all_patterns': sorted_patterns,
            'total_analyzed': len(entries)
        }

    def _analyze_emotions(self, diary_entries, mood_entries):
        """Анализ эмоционального ландшафта"""
        emotion_intensity = {}
        emotion_frequency = {}

        # Анализ из записей дневника
        for entry in diary_entries:
            emotions = entry.get('emotions', {})
            for emotion, intensity in emotions.items():
                if intensity > 0:
                    emotion_frequency[emotion] = emotion_frequency.get(emotion, 0) + 1
                    if emotion not in emotion_intensity:
                        emotion_intensity[emotion] = []
                    emotion_intensity[emotion].append(intensity)

        # Анализ настроения
        mood_scores = [entry['mood_score'] for entry in mood_entries] if mood_entries else []
        avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0

        # Рассчитываем среднюю интенсивность
        avg_intensity = {}
        for emotion, intensities in emotion_intensity.items():
            avg_intensity[emotion] = sum(intensities) / len(intensities)

        # Определяем доминирующие эмоции
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

        # Сортируем
        sorted_emotions = dict(sorted(dominant_emotions.items(),
                                      key=lambda x: x[1]['frequency'],
                                      reverse=True))

        return {
            'dominant_emotions': dict(list(sorted_emotions.items())[:5]),  # Топ-5
            'mood_analysis': {
                'avg_mood': round(avg_mood, 1),
                'mood_stability': self._calculate_mood_stability(mood_scores),
                'best_day': max(mood_scores) if mood_scores else 0,
                'worst_day': min(mood_scores) if mood_scores else 0
            },
            'emotional_range': len(dominant_emotions)
        }

    def _analyze_triggers(self, entries):
        """Анализ триггеров (что вызывает реакции)"""
        if not entries:
            return {}

        # Простой анализ ключевых слов в ситуациях
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

            # Ищем категории триггеров
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

                        # Запоминаем эмоции для этой категории
                        for emotion, intensity in emotions.items():
                            if intensity > 0:
                                triggers[category]['typical_emotions'][emotion] = \
                                    triggers[category]['typical_emotions'].get(emotion, 0) + intensity

                        # Сохраняем пример (первые 50 символов)
                        if len(triggers[category]['examples']) < 3:
                            triggers[category]['examples'].append(situation[:50] + '...')
                        break

        # Рассчитываем среднюю интенсивность эмоций
        for category, data in triggers.items():
            total_emotions = sum(data['typical_emotions'].values())
            emotion_count = len(data['typical_emotions'])

            if emotion_count > 0:
                data['avg_emotional_intensity'] = round(total_emotions / emotion_count, 1)

                # Основная эмоция для этого триггера
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

        # Анализ альтернативных мыслей (что помогло)
        for entry in diary_entries:
            alternative = entry.get('alternative_thought')
            reassessment = entry.get('reassessment')

            if alternative:
                # Простая классификация стратегий по содержанию
                strategy_type = self._classify_strategy(alternative)

                if strategy_type not in strategies:
                    strategies[strategy_type] = {
                        'count': 0,
                        'examples': [],
                        'effectiveness': []
                    }

                strategies[strategy_type]['count'] += 1

                # Сохраняем примеры
                if len(strategies[strategy_type]['examples']) < 3:
                    strategies[strategy_type]['examples'].append(alternative[:100] + '...')

        # Анализ выполненных упражнений
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

        # Группируем по дням недели
        days_of_week = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        mood_by_day = {day: [] for day in days_of_week}

        for entry in mood_entries:
            date_obj = datetime.strptime(entry['date'], '%Y-%m-%d')
            day_index = date_obj.weekday()  # 0=Пн, 6=Вс
            day_name = days_of_week[day_index]
            mood_by_day[day_name].append(entry['mood_score'])

        # Рассчитываем среднее по дням
        avg_by_day = {}
        for day, scores in mood_by_day.items():
            if scores:
                avg_by_day[day] = sum(scores) / len(scores)

        # Определяем лучший/худший день
        if avg_by_day:
            best_day = max(avg_by_day.items(), key=lambda x: x[1])
            worst_day = min(avg_by_day.items(), key=lambda x: x[1])
        else:
            best_day = worst_day = (None, 0)

        # Анализ тренда
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

        # Рекомендации по паттернам мышления
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

        # Рекомендации по эмоциям
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

        # Рекомендации по триггерам
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

        # Общие рекомендации
        if profile['emotional_landscape'].get('mood_analysis', {}).get('avg_mood', 0) < 5:
            recommendations.append({
                'type': 'general',
                'priority': 'high',
                'title': 'Повышение общего настроения',
                'description': 'Среднее настроение ниже 5/10',
                'exercises': ['Визуализация позитивного образа', 'Дневник благодарности']
            })

        return recommendations[:5]  # Ограничиваем 5 рекомендациями

    # Вспомогательные методы
    def _calculate_mood_stability(self, mood_scores):
        if len(mood_scores) < 2:
            return 0
        import numpy as np
        return round(10 - np.std(mood_scores), 1)  # Обратная стандартному отклонению

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


class DNAVisualizationWidget(QWidget):
    """Виджет для визуализации ДНК профиля"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("🧬 Ваш профиль ментального здоровья")
        title.setProperty("class", "TitleMedium")
        layout.addWidget(title)

        # Контейнер для визуализации
        self.visualization_container = QScrollArea()
        self.visualization_container.setWidgetResizable(True)
        self.visualization_container.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(25)

        self.visualization_container.setWidget(self.content_widget)
        layout.addWidget(self.visualization_container)

        if not self.profile:
            no_data_label = QLabel("Сгенерируйте профиль для просмотра данных")
            no_data_label.setProperty("class", "TextSecondary")
            no_data_label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(no_data_label)

    def update_profile(self, profile):
        """Обновление отображения профиля"""
        self.profile = profile
        self._clear_layout()
        self._render_profile()

    def _clear_layout(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render_profile(self):
        if not self.profile:
            return

        # 1. Сводка
        self._render_summary()

        # 2. Паттерны мышления (визуальная спираль)
        self._render_thinking_patterns()

        # 3. Эмоциональный ландшафт (градиент)
        self._render_emotional_landscape()

        # 4. Триггеры (тепловая карта)
        self._render_triggers()

        # 5. Рекомендации
        self._render_recommendations()

    def _render_summary(self):
        card = QFrame()
        card.setProperty("class", "MintCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок с датой
        date_str = datetime.fromisoformat(self.profile['generated_at']).strftime("%d.%m.%Y")
        title = QLabel(f"Профиль от {date_str}")
        title.setProperty("class", "TitleSmall")
        layout.addWidget(title)

        # Статистика
        stats = [
            ("📊 Анализировано записей", str(self.profile['total_entries'])),
            ("📅 Период анализа", f"{self.profile['data_period_days']} дней"),
            ("🧠 Выявлено паттернов", str(len(self.profile['thinking_patterns'].get('all_patterns', {})))),
            ("💖 Доминирующих эмоций", str(len(self.profile['emotional_landscape'].get('dominant_emotions', {}))))
        ]

        for label, value in stats:
            stat_frame = QFrame()
            stat_layout = QHBoxLayout(stat_frame)
            stat_layout.setContentsMargins(0, 0, 0, 0)

            label_widget = QLabel(label)
            label_widget.setProperty("class", "TextRegular")
            stat_layout.addWidget(label_widget)

            stat_layout.addStretch()

            value_widget = QLabel(value)
            value_widget.setStyleSheet("font-weight: bold;")
            stat_layout.addWidget(value_widget)

            layout.addWidget(stat_frame)

        self.content_layout.addWidget(card)

    def _render_thinking_patterns(self):
        card = QFrame()
        card.setProperty("class", "Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🧠 Паттерны мышления")
        title.setProperty("class", "TitleSmall")
        layout.addWidget(title)

        patterns = self.profile['thinking_patterns'].get('dominant_patterns', {})

        if not patterns:
            no_data = QLabel("Недостаточно данных для анализа")
            no_data.setProperty("class", "TextSecondary")
            layout.addWidget(no_data)
            self.content_layout.addWidget(card)
            return

        # Визуализация в виде "генов"
        for pattern, data in patterns.items():
            pattern_frame = QFrame()
            pattern_layout = QVBoxLayout(pattern_frame)
            pattern_layout.setSpacing(5)

            # Название и процент
            header_frame = QFrame()
            header_layout = QHBoxLayout(header_frame)
            header_layout.setContentsMargins(0, 0, 0, 0)

            name_label = QLabel(pattern)
            name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            header_layout.addWidget(name_label)

            header_layout.addStretch()

            percent_label = QLabel(f"{data['percentage']}%")
            percent_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")
            header_layout.addWidget(percent_label)

            pattern_layout.addWidget(header_frame)

            # Прогресс-бар
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(int(data['percentage']))
            progress.setTextVisible(False)
            progress.setStyleSheet("""
                QProgressBar {
                    height: 8px;
                    border-radius: 4px;
                    background-color: #E8DFD8;
                }
                QProgressBar::chunk {
                    background-color: #FF6B6B;
                    border-radius: 4px;
                }
            """)
            pattern_layout.addWidget(progress)

            # Описание
            desc_label = QLabel(data['description'])
            desc_label.setProperty("class", "TextSecondary")
            desc_label.setWordWrap(True)
            pattern_layout.addWidget(desc_label)

            # Примеры ситуаций
            if data.get('typical_situations'):
                examples_label = QLabel("Примеры: " + ", ".join(data['typical_situations'][:2]))
                examples_label.setProperty("class", "TextLight")
                examples_label.setWordWrap(True)
                pattern_layout.addWidget(examples_label)

            layout.addWidget(pattern_frame)

        self.content_layout.addWidget(card)

    def _render_emotional_landscape(self):
        """Визуализация эмоционального ландшафта"""
        card = QFrame()
        card.setProperty("class", "SoftPinkCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("💖 Эмоциональный ландшафт")
        title.setProperty("class", "TitleSmall")
        layout.addWidget(title)

        emotions = self.profile['emotional_landscape'].get('dominant_emotions', {})

        if not emotions:
            no_data = QLabel("Недостаточно данных для анализа эмоций")
            no_data.setProperty("class", "TextSecondary")
            layout.addWidget(no_data)
            self.content_layout.addWidget(card)
            return

        for emotion, data in emotions.items():
            emotion_frame = QFrame()
            emotion_layout = QVBoxLayout(emotion_frame)
            emotion_layout.setSpacing(5)

            # Название и частота
            header_frame = QFrame()
            header_layout = QHBoxLayout(header_frame)
            header_layout.setContentsMargins(0, 0, 0, 0)

            name_label = QLabel(emotion)
            name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            header_layout.addWidget(name_label)

            header_layout.addStretch()

            freq_label = QLabel(f"{data['frequency']} раз ({data['percentage']}%)")
            freq_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")
            header_layout.addWidget(freq_label)

            emotion_layout.addWidget(header_frame)

            # Интенсивность
            intensity_label = QLabel(f"Интенсивность: {data['avg_intensity']}/100 ({data['strength']})")
            intensity_label.setProperty("class", "TextSecondary")
            emotion_layout.addWidget(intensity_label)

            layout.addWidget(emotion_frame)

        self.content_layout.addWidget(card)

    def _render_triggers(self):
        """Визуализация триггеров"""
        card = QFrame()
        card.setProperty("class", "MintCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🎯 Триггеры и реакции")
        title.setProperty("class", "TitleSmall")
        layout.addWidget(title)

        triggers = self.profile.get('triggers', {})

        if not triggers:
            no_data = QLabel("Недостаточно данных для анализа триггеров")
            no_data.setProperty("class", "TextSecondary")
            layout.addWidget(no_data)
            self.content_layout.addWidget(card)
            return

        for trigger, data in triggers.items():
            trigger_frame = QFrame()
            trigger_layout = QVBoxLayout(trigger_frame)
            trigger_layout.setSpacing(5)

            # Название и количество
            header_frame = QFrame()
            header_layout = QHBoxLayout(header_frame)
            header_layout.setContentsMargins(0, 0, 0, 0)

            name_label = QLabel(trigger.capitalize())
            name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            header_layout.addWidget(name_label)

            header_layout.addStretch()

            count_label = QLabel(f"{data['count']} случаев")
            count_label.setStyleSheet("color: #06D6A0; font-weight: bold;")
            header_layout.addWidget(count_label)

            trigger_layout.addWidget(header_frame)

            # Основная эмоция
            if 'main_emotion' in data:
                emotion_label = QLabel(
                    f"Основная эмоция: {data['main_emotion']['name']} ({data['main_emotion']['intensity']}%)")
                emotion_label.setProperty("class", "TextSecondary")
                trigger_layout.addWidget(emotion_label)

            # Примеры
            if data.get('examples'):
                examples_text = "Примеры: " + "; ".join(data['examples'])
                examples_label = QLabel(examples_text)
                examples_label.setProperty("class", "TextLight")
                examples_label.setWordWrap(True)
                trigger_layout.addWidget(examples_label)

            layout.addWidget(trigger_frame)

        self.content_layout.addWidget(card)

    def _render_recommendations(self):
        card = QFrame()
        card.setProperty("class", "WarmCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🎯 Персонализированные рекомендации")
        title.setProperty("class", "TitleSmall")
        layout.addWidget(title)

        recommendations = self.profile.get('personalized_recommendations', [])

        if not recommendations:
            no_rec = QLabel("Продолжайте вести дневник для получения рекомендаций")
            no_rec.setProperty("class", "TextSecondary")
            layout.addWidget(no_rec)
        else:
            for i, rec in enumerate(recommendations, 1):
                rec_frame = QFrame()
                rec_layout = QVBoxLayout(rec_frame)
                rec_layout.setSpacing(8)

                # Приоритет (цветная полоска)
                priority_color = "#FF6B6B" if rec['priority'] == 'high' else "#FFD166" if rec[
                                                                                              'priority'] == 'medium' else "#06D6A0"

                rec_frame.setStyleSheet(f"""
                    QFrame {{
                        border-left: 4px solid {priority_color};
                        padding-left: 10px;
                    }}
                """)

                # Заголовок
                title_label = QLabel(f"{i}. {rec['title']}")
                title_label.setStyleSheet("font-weight: bold; font-size: 15px;")
                rec_layout.addWidget(title_label)

                # Описание
                desc_label = QLabel(rec['description'])
                desc_label.setProperty("class", "TextRegular")
                desc_label.setWordWrap(True)
                rec_layout.addWidget(desc_label)

                # Упражнения
                if rec.get('exercises'):
                    exercises_label = QLabel("💡 Упражнения: " + ", ".join(rec['exercises']))
                    exercises_label.setProperty("class", "TextSecondary")
                    exercises_label.setWordWrap(True)
                    rec_layout.addWidget(exercises_label)

                layout.addWidget(rec_frame)

        self.content_layout.addWidget(card)


class AchievementsWindow(QWidget):
    """Окно достижений и прогресса"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Верхняя панель
        self.create_top_bar(main_layout)

        # Контент
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(25)
        content_layout.setContentsMargins(40, 30, 40, 40)

        # Заголовок
        header_label = QLabel("🎮 Прогресс и достижения")
        header_label.setProperty("class", "TitleLarge")
        content_layout.addWidget(header_label)

        # Виджет прогресса
        self.progress_widget = ProgressWidget(self.parent)
        content_layout.addWidget(self.progress_widget)

        # Табы для переключения
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: #F8F2E9;
                padding: 10px 20px;
                margin-right: 5px;
                border-radius: 8px;
                color: #8B7355;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #B5E5CF;
                color: #5A5A5A;
            }
            QTabBar::tab:hover {
                background-color: #E8DFD8;
            }
        """)

        # Вкладка всех достижений
        self.all_achievements_widget = AchievementsWidget(self.parent)
        self.tab_widget.addTab(self.all_achievements_widget, "Все достижения")

        # Вкладка выполненных достижений
        self.completed_achievements_widget = AchievementsWidget(self.parent)
        self.tab_widget.addTab(self.completed_achievements_widget, "Выполненные")

        content_layout.addWidget(self.tab_widget)

        # Прокручиваемая область
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidget(content_widget)

        main_layout.addWidget(scroll_area)

    def create_top_bar(self, parent_layout):
        """Создание верхней панели"""
        top_bar = QFrame()
        top_bar.setFixedHeight(70)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #F8F2E9;
                border-bottom: 1px solid #E8DFD8;
            }
        """)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(30, 0, 30, 0)

        # Кнопка назад
        back_btn = QPushButton("← Назад")
        back_btn.setProperty("class", "SecondaryButton")
        back_btn.clicked.connect(
            lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(1)
        )
        top_layout.addWidget(back_btn)

        top_layout.addStretch()

        # Название
        title = QLabel("Достижения")
        title.setProperty("class", "TitleMedium")
        top_layout.addWidget(title)

        top_layout.addStretch()

        # Заглушка для выравнивания
        dummy_btn = QPushButton()
        dummy_btn.setFixedSize(back_btn.sizeHint())
        dummy_btn.setVisible(False)
        top_layout.addWidget(dummy_btn)

        parent_layout.addWidget(top_bar)

    def update_display(self):
        """Обновление отображения"""
        if self.parent.current_user:
            user_id = self.parent.current_user['id']
            self.progress_widget.update_progress(user_id)
            self.all_achievements_widget.update_achievements(user_id)


class AnimatedButton(QPushButton):
    """Кнопка с анимацией нажатия и отпускания"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.animation_duration = 150

    def mousePressEvent(self, event):
        # Анимация нажатия
        self.animate_press()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # Анимация отпускания
        self.animate_release()
        super().mouseReleaseEvent(event)

    def animate_press(self):
        """Анимация при нажатии"""
        animation = QPropertyAnimation(self, b"geometry")
        animation.setDuration(self.animation_duration)

        current = self.geometry()
        pressed = QRect(
            current.x(),
            current.y() + 2,  # Опускаем на 2px
            current.width(),
            current.height()
        )

        animation.setStartValue(current)
        animation.setEndValue(pressed)
        animation.setEasingCurve(QEasingCurve.OutQuad)
        animation.start()

    def animate_release(self):
        """Анимация при отпускании"""
        animation = QPropertyAnimation(self, b"geometry")
        animation.setDuration(self.animation_duration)

        current = self.geometry()
        released = QRect(
            current.x(),
            current.y() - 2,  # Поднимаем обратно
            current.width(),
            current.height()
        )

        animation.setStartValue(current)
        animation.setEndValue(released)
        animation.setEasingCurve(QEasingCurve.OutQuad)
        animation.start()


class MoodButton(QPushButton):
    """Специальная кнопка для шкалы настроения с анимацией"""

    def __init__(self, number, parent=None):
        super().__init__(str(number), parent)
        self.number = number
        self.is_checked = False
        self.parent_window = parent

        # Настройка стилей
        self.update_style()

        # Анимация
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutBack)

    def update_style(self):
        """Обновление стиля в зависимости от состояния"""
        if self.is_checked:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #{self.get_color()};
                    color: #5A5A5A;
                    border-radius: 21px;
                    border: 3px solid #9BD1B8;
                    font-weight: bold;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #{self.get_hover_color()};
                    border: 3px solid #80BCA0;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #{self.get_color()};
                    color: #5A5A5A;
                    border-radius: 21px;
                    border: 2px solid #E8DFD8;
                    font-weight: 600;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: #{self.get_hover_color()};
                    border: 2px solid #D7CCC8;
                }}
            """)

    def get_color(self):
        """Получить цвет в зависимости от номера"""
        # Градиент от грусти к радости
        colors = [
            "FFD6DC",  # 1 - очень грустно (розовый)
            "FFE2C6",  # 2
            "FFEEC6",  # 3
            "FFF3C6",  # 4
            "FFF8C6",  # 5
            "F5FFC6",  # 6
            "E5FFC6",  # 7
            "D5FFC6",  # 8
            "C5FFC6",  # 9
            "B5E5CF",  # 10 - очень радостно (мятный)
        ]
        return colors[self.number - 1]

    def get_hover_color(self):
        """Цвет при наведении"""
        base_color = self.get_color()
        # Слегка затемняем цвет
        return self.darken_color(base_color)

    def darken_color(self, hex_color):
        """Затемнить HEX цвет на 20%"""
        # Преобразуем HEX в RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Уменьшаем яркость
        r = max(0, int(r * 0.8))
        g = max(0, int(g * 0.8))
        b = max(0, int(b * 0.8))

        # Возвращаем HEX
        return f"{r:02X}{g:02X}{b:02X}"

    def setChecked(self, checked):
        """Установить состояние с анимацией"""
        self.is_checked = checked

        # Анимация масштабирования
        current = self.geometry()
        if checked:
            target = QRect(
                current.x() - 3,
                current.y() - 3,
                current.width() + 6,
                current.height() + 6
            )
        else:
            target = current

        self.scale_animation.setStartValue(current)
        self.scale_animation.setEndValue(target)
        self.scale_animation.start()

        self.update_style()

    def mousePressEvent(self, event):
        """Анимация при нажатии"""
        # Временное уменьшение
        self.scale_animation.setDuration(100)
        current = self.geometry()
        pressed = QRect(
            current.x() + 2,
            current.y() + 2,
            current.width() - 4,
            current.height() - 4
        )

        self.scale_animation.setStartValue(current)
        self.scale_animation.setEndValue(pressed)
        self.scale_animation.start()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Восстановление после нажатия"""
        self.setChecked(not self.is_checked)

        # Проверяем, есть ли пользователь
        if not hasattr(self.parent_window, 'parent') or not self.parent_window.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему для сохранения настроения")
            self.setChecked(False)
            super().mouseReleaseEvent(event)
            return

        # Сохраняем в БД
        if self.is_checked:
            parent_app = self.parent_window.parent
            if parent_app.current_user:
                today = datetime.now().strftime('%Y-%m-%d')
                success = parent_app.db.save_mood_entry(
                    parent_app.current_user['id'],
                    today,
                    self.number
                )

                if success:

                    # Обновляем график
                    if hasattr(self.parent_window, 'mood_chart'):
                        entries = parent_app.db.get_mood_entries(
                            parent_app.current_user['id'],
                            days=7
                        )
                        self.parent_window.mood_chart.update_with_real_data(entries)
                    if hasattr(parent_app, 'main_menu'):
                        parent_app.main_menu.update_display()

                        # Проверяем достижения
                    new_achievements = parent_app.db.check_achievements(parent_app.current_user['id'])
                    if new_achievements:
                        # Показываем уведомление
                        self.show_achievement_notification(new_achievements)


                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось сохранить настроение")

        super().mouseReleaseEvent(event)

    def show_achievement_notification(self, achievements):
        """Показать уведомление о новых достижениях"""
        # Находим родительское окно для показа диалога
        parent_window = self.parent_window
        while parent_window and not isinstance(parent_window, (QMainWindow, QDialog)):
            if hasattr(parent_window, 'parent'):
                parent_window = parent_window.parent
            else:
                break

        if not parent_window:
            return

        dialog = QDialog(parent_window)
        dialog.setWindowTitle("🎉 Новое достижение!")
        dialog.setFixedSize(400, 300)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #FFFBF6;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Анимация конфетти
        confetti_label = QLabel("🎊")
        confetti_label.setStyleSheet("font-size: 48px;")
        confetti_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(confetti_label)

        # Заголовок
        title = QLabel("Поздравляем!")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #5A5A5A;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Достижения
        for ach in achievements:
            ach_frame = QFrame()
            ach_layout = QHBoxLayout(ach_frame)
            ach_layout.setSpacing(15)

            # Иконка
            icon_label = QLabel(ach['icon'])
            icon_label.setStyleSheet("font-size: 24px;")
            ach_layout.addWidget(icon_label)

            # Информация
            info_widget = QWidget()
            info_layout = QVBoxLayout(info_widget)
            info_layout.setSpacing(5)

            name_label = QLabel(ach['name'])
            name_label.setStyleSheet("font-weight: bold; font-size: 16px;")
            info_layout.addWidget(name_label)

            desc_label = QLabel(ach['description'])
            desc_label.setProperty("class", "TextSecondary")
            info_layout.addWidget(desc_label)

            xp_label = QLabel(f"+{ach['xp']} XP")
            xp_label.setStyleSheet("color: #FFD166; font-weight: bold;")
            info_layout.addWidget(xp_label)

            ach_layout.addWidget(info_widget, 1)

            layout.addWidget(ach_frame)

        layout.addStretch()

        # Кнопка
        ok_btn = QPushButton("Отлично!")
        ok_btn.setProperty("class", "PrimaryButton")
        ok_btn.clicked.connect(dialog.close)
        layout.addWidget(ok_btn)

        dialog.exec_()


class MoodChartWidget(QWidget):
    """Виджет для отображения графика настроения"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(300)  # Фиксированная высота
        self.init_ui()

    def init_ui(self):
        # Основной layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Создаем matplotlib figure
        self.figure = Figure(figsize=(10, 2.5), dpi=100, facecolor='#FFFBF6')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")

        layout.addWidget(self.canvas, 1)

        # Кнопка деталей
        details_btn = QPushButton("📊 Подробная статистика")
        details_btn.setProperty("class", "SecondaryButton")
        details_btn.setFixedHeight(35)
        details_btn.clicked.connect(self.show_detailed_stats)
        layout.addWidget(details_btn)

        # Генерируем демо-данные
        self.generate_sample_data()
        self.plot_chart()

    def show_detailed_stats(self):
        """Показать подробную статистику"""
        dialog = QDialog(self)
        dialog.setWindowTitle("📊 Подробная статистика настроения")
        dialog.setFixedSize(500, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #FFFBF6;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title = QLabel("Статистика настроения")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #5A5A5A;
        """)
        layout.addWidget(title)

        # Показатели
        stats = [
            ("Среднее за неделю:", f"{np.mean(self.mood_values):.1f}/10"),
            ("Лучший день:", f"{np.max(self.mood_values)}/10"),
            ("Стабильность:", f"{(10 - np.std(self.mood_values)):.1f}/10"),
            ("Тренд:", "↗️ Улучшение" if self.mood_values[-1] > self.mood_values[0] else "➡️ Стабильно"),
            ("Рекомендация:", "Продолжайте практики!" if np.mean(self.mood_values) > 5 else "Попробуйте упражнения")
        ]

        for label, value in stats:
            stat_frame = QFrame()
            stat_layout = QHBoxLayout(stat_frame)
            stat_layout.setContentsMargins(0, 0, 0, 0)

            label_widget = QLabel(label)
            label_widget.setProperty("class", "TextRegular")
            label_widget.setStyleSheet("font-weight: 600;")
            stat_layout.addWidget(label_widget)

            stat_layout.addStretch()

            value_widget = QLabel(value)
            value_widget.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #5A5A5A;
            """)
            stat_layout.addWidget(value_widget)

            layout.addWidget(stat_frame)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #E8DFD8;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # Подсказка
        tip_label = QLabel("💡 Совет: Регулярное отслеживание настроения помогает замечать закономерности")
        tip_label.setProperty("class", "TextSecondary")
        tip_label.setWordWrap(True)
        layout.addWidget(tip_label)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setProperty("class", "PrimaryButton")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec_()

    def generate_sample_data(self):
        """Генерация демо-данных (в реальном приложении - из БД)"""
        # Последние 7 дней
        self.days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

        # Случайные значения настроения (от 1 до 10)
        np.random.seed(42)  # Для воспроизводимости
        self.mood_values = np.random.randint(3, 9, 7)

        # Сегодняшний день - последний
        self.mood_values[-1] = 6  # Сегодня выбрали 6

        # Цвета для каждой точки в зависимости от настроения
        self.colors = []
        for value in self.mood_values:
            if value <= 3:
                self.colors.append('#FF6B6B')  # Красный
            elif value <= 5:
                self.colors.append('#FFD166')  # Желтый
            elif value <= 7:
                self.colors.append('#06D6A0')  # Зеленый
            else:
                self.colors.append('#118AB2')  # Синий

    def plot_chart(self):
        """Отрисовка графика"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Настройка внешнего вида
        ax.set_facecolor('#FFFBF6')
        self.figure.patch.set_facecolor('#FFFBF6')

        # Ограничения осей
        ax.set_ylim(0, 10.5)

        # Линия графика
        line, = ax.plot(self.days, self.mood_values,
                        color='#9BD1B8',
                        linewidth=2.5,
                        marker='o',
                        markersize=8,
                        markerfacecolor='white',
                        markeredgewidth=2)

        # Заливка под графиком
        ax.fill_between(self.days, self.mood_values,
                        color='#9BD1B8',
                        alpha=0.1)

        # Точки с цветами
        for i, (day, value, color) in enumerate(zip(self.days, self.mood_values, self.colors)):
            ax.scatter(day, value,
                       color=color,
                       s=100,
                       zorder=5,
                       edgecolors='white',
                       linewidths=2)

            # Подписи значений
            ax.text(day, value + 0.3, str(value),
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    fontweight='bold',
                    color='#5A5A5A')

        # Настройка осей
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#E8DFD8')
        ax.spines['bottom'].set_color('#E8DFD8')

        # Цвета подписей
        ax.tick_params(axis='x', colors='#8B7355', labelsize=11)
        ax.tick_params(axis='y', colors='#8B7355', labelsize=11)

        # Заголовок и метки
        ax.set_title('📈 Ваше настроение за неделю',
                     fontsize=14,
                     fontweight='bold',
                     color='#5A5A5A',
                     pad=15)

        ax.set_xlabel('Дни', fontsize=11, color='#8B7355', labelpad=10)
        ax.set_ylabel('Настроение (1-10)', fontsize=11, color='#8B7355', labelpad=10)

        # Сетка
        ax.grid(True, alpha=0.2, linestyle='--', color='#C4B6A6')

        # Легенда настроения
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w',
                       label='Плохое (1-3)',
                       markerfacecolor='#FF6B6B', markersize=8),
            plt.Line2D([0], [0], marker='o', color='w',
                       label='Среднее (4-5)',
                       markerfacecolor='#FFD166', markersize=8),
            plt.Line2D([0], [0], marker='o', color='w',
                       label='Хорошее (6-7)',
                       markerfacecolor='#06D6A0', markersize=8),
            plt.Line2D([0], [0], marker='o', color='w',
                       label='Отличное (8-10)',
                       markerfacecolor='#118AB2', markersize=8)
        ]

        ax.legend(handles=legend_elements,
                  loc='upper right',
                  fontsize=9,
                  frameon=False,
                  labelcolor='#5A5A5A')

        # Автонастройка layout
        self.figure.tight_layout()
        self.canvas.draw()

    def update_chart(self, new_value=None):
        """Обновить график новым значением"""
        if new_value is not None:
            # В реальном приложении добавляем в БД
            # Для демо просто обновляем последнее значение
            self.mood_values[-1] = new_value
            self.plot_chart()

    def update_with_real_data(self, entries):
        """Обновление с реальными данными из БД"""
        if not entries:
            self.generate_sample_data()  # Если нет данных, показываем демо
        else:
            # Преобразуем данные из БД
            self.days = []
            self.mood_values = []

            for entry in entries:
                # entry - это sqlite3.Row объект
                date_str = entry['date']
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')

                # Сокращенное название дня недели
                day_name = date_obj.strftime('%a')
                day_name_rus = {
                    'Mon': 'Пн', 'Tue': 'Вт', 'Wed': 'Ср',
                    'Thu': 'Чт', 'Fri': 'Пт', 'Sat': 'Сб', 'Sun': 'Вс'
                }.get(day_name, day_name)

                self.days.append(day_name_rus)
                self.mood_values.append(entry['mood_score'])

            # Если данных меньше 7 дней, дополняем пустыми
            while len(self.days) < 7:
                self.days.insert(0, "")
                self.mood_values.insert(0, 0)

            # Обновляем цвета
            self.update_colors()
            self.plot_chart()

    def show_prediction_chart(self, user_id):
        """Показать график с прогнозом"""
        try:
            if not self.parent.current_user:
                return

            # Получаем исторические данные
            entries = self.parent.db.get_mood_entries(user_id, days=14)

            if not entries or len(entries) < 7:
                return

            # Создаем предсказатель
            predictor = MoodPredictor(self.parent.db)
            prediction = predictor.predict_mood_trend(user_id, days_ahead=7)

            if not prediction['can_predict']:
                return

            # Создаем новый график с прогнозом
            dialog = QDialog(self)
            dialog.setWindowTitle("📊 Прогноз настроения")
            dialog.setFixedSize(600, 400)

            layout = QVBoxLayout(dialog)

            # Создаем matplotlib figure
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
            from matplotlib.figure import Figure

            fig = Figure(figsize=(8, 4), dpi=100, facecolor='#FFFBF6')
            canvas = FigureCanvasQTAgg(fig)
            ax = fig.add_subplot(111)

            # Исторические данные
            historical_days = list(range(len(entries)))
            historical_moods = [entry['mood_score'] for entry in entries]

            # Прогноз
            forecast_days = list(range(len(entries), len(entries) + 7))
            forecast_moods = prediction['predictions']

            # Построение графика
            ax.plot(historical_days, historical_moods, 'o-', color='#9BD1B8',
                    linewidth=2, label='История', markersize=8)
            ax.plot(forecast_days, forecast_moods, 'o--', color='#FFB38E',
                    linewidth=2, label='Прогноз', markersize=8)

            # Заливка области прогноза
            ax.fill_between(forecast_days, forecast_moods,
                            alpha=0.1, color='#FFB38E')

            ax.set_title('Прогноз настроения на 7 дней')
            ax.set_xlabel('Дни')
            ax.set_ylabel('Настроение')
            ax.legend()
            ax.grid(True, alpha=0.3)

            fig.tight_layout()

            layout.addWidget(canvas)

            # Информация
            info_label = QLabel(f"Тренд: {prediction['trend']} | Точность: {prediction['confidence']}%")
            info_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(info_label)

            # Кнопка закрытия
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)

            dialog.exec_()

        except Exception as e:
            print(f"Ошибка создания графика прогноза: {e}")

    def update_colors(self):
        """Обновление цветов на основе реальных значений"""
        self.colors = []
        for value in self.mood_values:
            if value == 0:  # Нет данных
                self.colors.append('#E8DFD8')
            elif value <= 3:
                self.colors.append('#FF6B6B')
            elif value <= 5:
                self.colors.append('#FFD166')
            elif value <= 7:
                self.colors.append('#06D6A0')
            else:
                self.colors.append('#118AB2')


class DatabaseManager:
    """Менеджер базы данных SQLite"""

    def __init__(self):
        self.db_name = "mental_health.db"
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Подключение к базе данных"""
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Для доступа к полям по имени

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
                emotions TEXT NOT NULL,  -- JSON строка
                thoughts TEXT NOT NULL,
                distortions TEXT NOT NULL,  -- JSON строка
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mental_health_dna (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                profile_data TEXT,  -- JSON с профилем
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        self.create_base_achievements()

        self.conn.commit()

    def create_base_achievements(self):
        """Создание базовых достижений"""
        base_achievements = [
            # Начальные достижения
            ("Первый шаг", "Сделайте первую запись в дневнике", "🎯", "total_entries", 1, 50),
            ("Начало пути", "Сделайте 5 записей в дневнике", "📝", "total_entries", 5, 100),
            ("Постоянство", "Сделайте 10 записей в дневнике", "🌟", "total_entries", 10, 200),
            ("Мастер дневника", "Сделайте 50 записей в дневнике", "📚", "total_entries", 50, 500),

            # Достижения по дням подряд
            ("Новичок", "3 дня подряд ведения дневника", "🔥", "streak_days", 3, 100),
            ("Последователь", "7 дней подряд ведения дневника", "💫", "streak_days", 7, 250),
            ("Мастер привычки", "30 дней подряд ведения дневника", "🏆", "streak_days", 30, 1000),

            # Достижения по настроению
            ("Позитивный настрой", "Отметьте настроение 8+ 5 дней подряд", "😊", "high_mood_streak", 5, 150),
            ("Эмоциональный баланс", "Проанализируйте 10 сложных ситуаций", "⚖️", "analyzed_situations", 10, 300),

            # Достижения по искажениям
            ("Детектив мыслей", "Выявите 5 когнитивных искажений", "🕵️", "distortions_found", 5, 200),
            ("Когнитивный эксперт", "Выявите 20 когнитивных искажений", "🧠", "distortions_found", 20, 500),

            # Достижения по упражнениям
            ("Практик", "Выполните 5 упражнений КПТ", "🧘", "exercises_completed", 5, 150),
            ("Мастер КПТ", "Выполните 20 упражнений КПТ", "🎖️", "exercises_completed", 20, 600),
        ]

        cursor = self.conn.cursor()
        for name, desc, icon, req_type, req_value, xp in base_achievements:
            cursor.execute('''
                INSERT OR IGNORE INTO achievements (name, description, icon, requirement_type, requirement_value, xp_reward)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, desc, icon, req_type, req_value, xp))

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

    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С НАСТРОЕНИЕМ ==========

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
            # Преобразуем словари в JSON строки
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
            # Парсим JSON поля
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

            # Создаем начальную статистику
            cursor.execute('''
                        INSERT INTO user_stats (user_id, xp, level, streak_days, total_entries)
                        VALUES (?, 0, 1, 0, 0)
                    ''', (user_id,))

            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Пользователь уже существует

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

        # Проверяем пароль
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

    def get_average_mood(self, user_id, days=30):
        """Получение среднего настроения за период"""
        cursor = self.conn.cursor()
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT AVG(mood_score) as avg_mood 
            FROM mood_entries 
            WHERE user_id = ? AND date >= ? AND mood_score > 0
        ''', (user_id, start_date))

        result = cursor.fetchone()
        return result['avg_mood'] if result and result['avg_mood'] else 0

    # В класс DatabaseManager добавляем методы:

    def get_user_stats(self, user_id):
        """Получение статистики пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM user_stats WHERE user_id = ?', (user_id,))
        stats = cursor.fetchone()

        if not stats:

            # Проверяем существует ли пользователь
            cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
            if not cursor.fetchone():
                return None

            # Создаем запись если нет
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

        # Формируем SET часть запроса
        set_parts = []
        values = []

        for field, value in updates_dict.items():
            set_parts.append(f"{field} = ?")
            values.append(value)

        values.append(user_id)  # Для WHERE условия

        # Выполняем запрос
        query = f'''
                UPDATE user_stats 
                SET {', '.join(set_parts)}
                WHERE user_id = ?
            '''

        cursor.execute(query, values)
        self.conn.commit()

        # Проверяем достижения
        self.check_achievements(user_id)

    def check_achievements(self, user_id):
        """Проверка выполнения достижений"""
        cursor = self.conn.cursor()

        # Получаем текущую статистику
        stats = self.get_user_stats(user_id)
        if not stats:
            return []

        # Получаем все достижения
        cursor.execute('SELECT * FROM achievements')
        achievements = cursor.fetchall()

        completed_achievements = []

        for ach in achievements:
            ach_id = ach['id']
            req_type = ach['requirement_type']
            req_value = ach['requirement_value']

            # Проверяем, есть ли уже запись о достижении
            cursor.execute('''
                SELECT * FROM user_achievements 
                WHERE user_id = ? AND achievement_id = ?
            ''', (user_id, ach_id))

            user_ach = cursor.fetchone()

            if user_ach and user_ach['completed']:
                continue  # Уже выполнено

            # Определяем текущий прогресс
            current_progress = 0
            if req_type == 'total_entries':
                current_progress = stats['total_entries']
            elif req_type == 'streak_days':
                current_progress = stats['streak_days']
            elif req_type == 'high_mood_streak':
                # TODO: реализовать отдельно
                continue
            elif req_type == 'analyzed_situations':
                # TODO: реализовать отдельно
                continue
            elif req_type == 'distortions_found':
                # TODO: реализовать отдельно
                continue
            elif req_type == 'exercises_completed':
                # TODO: реализовать отдельно
                continue

            # Обновляем или создаем запись
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

            # Проверяем выполнение
            if current_progress >= req_value and not (user_ach and user_ach['completed']):
                cursor.execute('''
                    UPDATE user_achievements 
                    SET completed = TRUE, completed_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND achievement_id = ?
                ''', (user_id, ach_id))

                # Начисляем XP
                new_xp = stats['xp'] + ach['xp_reward']
                self.update_user_stats(user_id, {'xp': new_xp})

                # Обновляем stats для следующей итерации
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

    def get_level_info(self, xp):
        """Получение информации об уровне на основе XP"""
        # Формула уровня: level = floor(sqrt(xp/100)) + 1
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

    def close(self):
        """Закрытие соединения с БД"""
        if self.conn:
            self.conn.close()


class MentalHealthApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тёплое убежище - поддержка ментального здоровья")
        self.setGeometry(100, 100, 1200, 800)

        # Инициализация базы данных
        self.db = DatabaseManager()
        self.current_user = None  # Текущий пользователь

        self.stacked_widget = AnimatedStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Инициализация интеллектуальных модулей
        self.mood_predictor = MoodPredictor(self.db)
        self.trigger_intelligence = TriggerIntelligence(self.db)

        # Инициализация окон
        self.init_ui()

        # Показываем окно входа
        self.stacked_widget.setCurrentIndex(0)

        # Устанавливаем стили
        self.setup_styles()

        # Устанавливаем иконку окна
        self.setWindowIcon(QIcon())

    def set_current_user(self, user):
        """Установка текущего пользователя"""
        self.current_user = user
        # Обновляем все окна при смене пользователя
        if hasattr(self, 'main_menu'):
            self.main_menu.set_current_user(user)
        if hasattr(self, 'history_window'):
            self.history_window.set_current_user(user)
        if hasattr(self, 'diary_window'):
            self.diary_window.set_current_user(user)

    def setup_styles(self):
        """Настройка стилей приложения с теплой цветовой схемой"""
        self.setStyleSheet("""
            /* ===== ОСНОВНЫЕ ЦВЕТА ===== */
            QMainWindow {
                background-color: #FFFBF6;  /* Теплый кремовый */
            }

            /* ===== ОБЩИЕ СТИЛИ ===== */
            QWidget {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                color: #5A5A5A;
            }

            /* ===== КНОПКИ ===== */
            QPushButton {
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }

            QPushButton:hover {
                opacity: 0.9;
            }

            QPushButton:pressed {
                opacity: 0.8;
                padding-top: 13px;
                padding-bottom: 11px;
            }

            /* Primary Button (Мятный) */
            .PrimaryButton {
                background-color: #B5E5CF;  /* Мятный */
                color: #5A5A5A;
                border: 1px solid #9BD1B8;
            }

            .PrimaryButton:hover {
                background-color: #9BD1B8;
                border-color: #80BCA0;
            }

            /* Secondary Button (Теплый беж) */
            .SecondaryButton {
                background-color: #F8F2E9;  /* Светлый беж */
                color: #8B7355;
                border: 1px solid #E8DFD8;
            }

            .SecondaryButton:hover {
                background-color: #F0E6DC;
                border-color: #D7CCC8;
            }

            /* Emergency Button (Нежно-розовый) */
            .EmergencyButton {
                background-color: #FFD6DC;  /* Нежно-розовый */
                color: #5A5A5A;
                border: 1px solid #FFC8D6;
            }

            .EmergencyButton:hover {
                background-color: #FFC8D6;
                border-color: #FFA8A8;
            }

            /* ===== КАРТОЧКИ ===== */
            .Card {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E8DFD8;
            }

            .WarmCard {
                background-color: #F8F2E9;  /* Светлый беж */
                border-radius: 12px;
                border: 1px solid #E8DFD8;
            }

            .MintCard {
                background-color: #B5E5CF;  /* Мятный */
                border-radius: 12px;
                border: none;
            }

            .PeachCard {
                background-color: #FFB38E;  /* Персиковый */
                border-radius: 12px;
                border: none;
            }

            .SoftPinkCard {
                background-color: #FFD6DC;  /* Нежно-розовый */
                border-radius: 12px;
                border: none;
            }

            /* ===== МЕТКИ ===== */
            .TitleLarge {
                font-size: 28px;
                font-weight: 700;
                color: #5A5A5A;
            }

            .TitleMedium {
                font-size: 20px;
                font-weight: 600;
                color: #5A5A5A;
            }

            .TitleSmall {
                font-size: 16px;
                font-weight: 600;
                color: #5A5A5A;
            }

            .TextRegular {
                font-size: 14px;
                color: #5A5A5A;
            }

            .TextSecondary {
                font-size: 13px;
                color: #8B7355;
            }

            .TextLight {
                font-size: 12px;
                color: #C4B6A6;
            }

            /* ===== ПРОКРУТКА ===== */
            QScrollArea {
                border: none;
                background-color: transparent;
            }

            QScrollBar:vertical {
                border: none;
                background-color: #F8F2E9;
                width: 10px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background-color: #C4B6A6;
                border-radius: 5px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #8B7355;
            }

            /* ===== ФРЕЙМЫ И РАЗДЕЛИТЕЛИ ===== */
            QFrame[frameShape="4"] {
                border: 1px solid #E8DFD8;
            }

            /* ===== СПЕЦИАЛЬНЫЕ ВИДЖЕТЫ ===== */
            .MoodButton {
                background-color: #FFFFFF;
                border: 2px solid #E8DFD8;
                border-radius: 15px;
            }

            .MoodButton:checked {
                background-color: #B5E5CF;
                border: 2px solid #9BD1B8;
            }

            .MoodButton:hover {
                background-color: #F8F2E9;
            }

            .ActionCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E8DFD8;
            }

            .ActionCard:hover {
                background-color: #F8F2E9;
                border: 1px solid #B5E5CF;
            }

            .FunctionCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border-left: 6px solid #B5E5CF;
            }

            .FunctionCard:hover {
                background-color: #F8F2E9;
            }

            /* ===== COMBOBOX ===== */
        QComboBox {
            background-color: white;
            border: 1px solid #E8DFD8;
            border-radius: 6px;
            padding: 8px;
            color: #5A5A5A;
            font-size: 14px;
            min-height: 20px;
        }

        QComboBox:hover {
            border: 1px solid #B5E5CF;
        }

        QComboBox::drop-down {
            border: none;
            width: 30px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #8B7355;
            width: 0;
            height: 0;
            margin-right: 10px;
        }

        QComboBox QAbstractItemView {
            background-color: white;
            border: 1px solid #E8DFD8;
            border-radius: 6px;
            selection-background-color: #B5E5CF;
            selection-color: #5A5A5A;
            padding: 5px;
        }

        QComboBox QAbstractItemView::item {
            padding: 8px;
            border-radius: 4px;
        }

        QComboBox QAbstractItemView::item:hover {
            background-color: #F8F2E9;
        }

        QComboBox QAbstractItemView::item:selected {
            background-color: #B5E5CF;
        }
        """)

    def show(self):
        """Показ окна с анимацией"""
        super().show()
        self.center_on_screen()

    def center_on_screen(self):
        """Центрирование окна на экране"""
        try:
            screen = QApplication.primaryScreen().geometry()
            window_geometry = self.frameGeometry()
            center_point = screen.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())
        except Exception as e:
            print(f"Ошибка центрирования: {e}")

    def init_ui(self):
        """Инициализация всех окон"""
        print("=" * 50)
        print("ИНИЦИАЛИЗАЦИЯ ОКОН")
        print("=" * 50)

        # Окно входа
        self.login_window = LoginWindow(self)
        self.stacked_widget.addWidget(self.login_window)
        print(f"Добавлено окно входа: индекс 0")

        # Главное меню
        self.main_menu = MainMenuWindow(self)
        self.stacked_widget.addWidget(self.main_menu)
        print(f"Добавлено главное меню: индекс 1")

        # Окно дневника мыслей
        self.diary_window = DiaryWindow(self)
        self.stacked_widget.addWidget(self.diary_window)
        print(f"Добавлено окно дневника: индекс 2")

        # Окно упражнений КПТ
        self.exercises_window = ExercisesWindow(self)
        self.stacked_widget.addWidget(self.exercises_window)
        print(f"Добавлено окно упражнений: индекс 3")

        # Окно истории записей
        self.history_window = HistoryWindow(self)
        self.stacked_widget.addWidget(self.history_window)
        print(f"Добавлено окно истории: индекс 4")

        # Окно достижений
        self.achievements_window = AchievementsWindow(self)
        self.stacked_widget.addWidget(self.achievements_window)
        print(f"Добавлено окно достижений: индекс 5")

        # Окно ДНК профиля
        self.dna_window = DNAProfileWindow(self)
        self.stacked_widget.addWidget(self.dna_window)
        print(f"Добавлено окно ДНК профиля: индекс {self.stacked_widget.count() - 1}")

        # Окно интеллектуального анализа
        self.intelligence_window = IntelligenceDashboard(self)
        self.stacked_widget.addWidget(self.intelligence_window)
        print(f"Добавлено окно интеллектуального анализа: индекс {self.stacked_widget.count() - 1}")

        print(f"Всего окон: {self.stacked_widget.count()}")
        print("=" * 50)


class LoginWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса окна входа - УПРОЩЕННАЯ ВЕРСИЯ"""
        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(0)

        # Фон
        self.setStyleSheet("background-color: #FFFBF6;")

        # Контейнер
        container = QFrame()
        container.setFixedWidth(400)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(30)
        container_layout.setAlignment(Qt.AlignCenter)

        # Заголовок
        title_label = QLabel("Тёплое убежище")
        title_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #5A5A5A;
            margin: 0;
            padding: 0;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title_label)

        # Подзаголовок
        subtitle_label = QLabel("Поддержка ментального здоровья через КПТ")
        subtitle_label.setStyleSheet("""
            font-size: 14px;
            color: #8B7355;
            margin: 0;
            padding: 0;
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(subtitle_label)

        # Добавляем отступ
        container_layout.addSpacing(20)

        # Карточка формы входа
        form_card = QFrame()
        form_card.setStyleSheet("""
            background-color: white;
            border-radius: 12px;
            border: 1px solid #E8DFD8;
        """)
        form_card.setFixedSize(400, 350)

        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(40, 30, 40, 30)
        form_layout.setSpacing(25)

        # Заголовок формы
        form_title = QLabel("Вход в систему")
        form_title.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
            color: #5A5A5A;
            margin: 0;
            padding: 0;
        """)
        form_title.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(form_title)

        # Поле логина
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин")
        self.username_input.setFixedHeight(45)
        self.username_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E8DFD8;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #B5E5CF;
            }
        """)
        form_layout.addWidget(self.username_input)

        # Поле пароля
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(45)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E8DFD8;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #B5E5CF;
            }
        """)
        form_layout.addWidget(self.password_input)

        # Кнопка входа
        login_btn = QPushButton("Войти с заботой ❤️")
        login_btn.setFixedHeight(50)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #B5E5CF;
                color: #5A5A5A;
                border-radius: 8px;
                border: none;
                font-weight: 600;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #9BD1B8;
            }
        """)
        login_btn.clicked.connect(self.login)
        form_layout.addWidget(login_btn)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #E8DFD8;")
        separator.setFixedHeight(1)
        form_layout.addWidget(separator)

        # Ссылка на регистрацию
        register_btn = QPushButton("Создать аккаунт")
        register_btn.setFixedHeight(45)
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8B7355;
                border: 1px solid #E8DFD8;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F8F2E9;
            }
        """)
        register_btn.clicked.connect(self.register)
        form_layout.addWidget(register_btn)

        # Добавляем карточку в контейнер
        container_layout.addWidget(form_card)

        # Демо-подсказка
        demo_label = QLabel("Для демо-входа: логин: demo, пароль: demo123")
        demo_label.setStyleSheet("""
            font-size: 12px;
            color: #C4B6A6;
            font-style: italic;
            margin-top: 20px;
        """)
        demo_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(demo_label)

        # Добавляем контейнер в основной layout
        main_layout.addWidget(container)

        # Обработка Enter
        self.password_input.returnPressed.connect(self.login)
        self.username_input.setFocus()

    def login(self):
        """Обработка входа пользователя"""
        try:
            username = self.username_input.text()
            password = self.password_input.text()

            if not username or not password:
                QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
                return

            # Сначала пробуем стандартную аутентификацию
            user = self.parent.db.authenticate_user(username, password)

            if user:
                self.parent.set_current_user(user)
                self.parent.stacked_widget.setCurrentIndexWithAnimation(1)
                return

            # Демо-вход
            if username == "demo" and password == "demo123":
                user = self.parent.db.authenticate_user("demo", "demo123")

                if not user:
                    # Если демо-пользователя нет, создаем его
                    print("Создаем демо-пользователя...")
                    user_id = self.parent.db.create_user("demo", "demo123", "Демо Пользователь")

                    if user_id:
                        # Создаем демо-данные
                        self.create_demo_data(user_id)
                        user = self.parent.db.authenticate_user("demo", "demo123")

                if user:
                    # Устанавливаем пользователя
                    self.parent.set_current_user(user)
                    # Переходим на главное меню
                    self.parent.stacked_widget.setCurrentIndexWithAnimation(1)
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось создать демо-аккаунт")
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
        except Exception as e:
            print(f"Ошибка входа: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка входа: {str(e)}")

    def create_demo_data(self, user_id):
        """Создание демо-данных для нового пользователя"""
        try:
            print(f"Создание демо-данных для пользователя {user_id}")

            # Демо записи настроения за последние 7 дней
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                mood = random.randint(4, 8)
                self.parent.db.save_mood_entry(user_id, date, mood, "Демо-запись")

            # Демо записи дневника
            demo_entries = [
                {
                    'situation': 'Коллега не ответил на мое приветствие',
                    'emotions': {'Тревога': 80, 'Грусть': 60},
                    'thoughts': 'Он меня ненавидит, я сделал что-то не так',
                    'distortions': ['Чтение мыслей', 'Катастрофизация'],
                    'alternative': 'Возможно, он был занят или не заметил меня'
                },
                {
                    'situation': 'Не получилось выполнить задачу идеально',
                    'emotions': {'Стыд': 90, 'Гнев': 40},
                    'thoughts': 'Я неудачник, у меня никогда ничего не получается',
                    'distortions': ['Черно-белое мышление', 'Персонализация'],
                    'alternative': 'Это одна задача из многих, я учусь и совершенствуюсь'
                }
            ]

            for entry in demo_entries:
                self.parent.db.save_diary_entry(
                    user_id=user_id,
                    situation=entry['situation'],
                    emotions=entry['emotions'],
                    thoughts=entry['thoughts'],
                    distortions=entry['distortions'],
                    alternative_thought=entry['alternative']
                )

            print("Демо-данные созданы")
        except Exception as e:
            print(f"Ошибка создания демо-данных: {e}")

    def register(self):
        """Открытие диалога регистрации"""
        try:
            dialog = RegistrationDialog(self.parent.db, self)
            if dialog.exec_():
                QMessageBox.information(self, "Успешно", "Аккаунт создан! Можете войти.")
        except Exception as e:
            print(f"Ошибка регистрации: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка регистрации: {str(e)}")


class RegistrationDialog(QDialog):
    """Диалог регистрации нового пользователя"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Создание аккаунта")
        self.setFixedSize(400, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("🌱 Создание аккаунта")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #5A5A5A;
        """)
        layout.addWidget(title)

        # Поле имени
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ваше имя")
        self.name_input.setFixedHeight(40)
        layout.addWidget(self.name_input)

        # Поле логина
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин (мин. 3 символа)")
        self.username_input.setFixedHeight(40)
        layout.addWidget(self.username_input)

        # Поле пароля
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль (мин. 6 символов)")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(40)
        layout.addWidget(self.password_input)

        # Подтверждение пароля
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Подтвердите пароль")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setFixedHeight(40)
        layout.addWidget(self.confirm_input)

        layout.addSpacing(10)

        # Кнопки
        buttons_layout = QHBoxLayout()

        register_btn = QPushButton("Создать аккаунт")
        register_btn.setProperty("class", "PrimaryButton")
        register_btn.clicked.connect(self.register)
        buttons_layout.addWidget(register_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setProperty("class", "SecondaryButton")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def register(self):
        """Регистрация нового пользователя"""
        try:
            name = self.name_input.text().strip()
            username = self.username_input.text().strip()
            password = self.password_input.text()
            confirm = self.confirm_input.text()

            # Валидация
            if not name or not username or not password:
                QMessageBox.warning(self, "Ошибка", "Заполните все поля")
                return

            if len(username) < 3:
                QMessageBox.warning(self, "Ошибка", "Логин должен быть не менее 3 символов")
                return

            if len(password) < 6:
                QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 6 символов")
                return

            if password != confirm:
                QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
                return

            # Создание пользователя
            user_id = self.db.create_user(username, password, name)

            if user_id:
                QMessageBox.information(self, "Успешно", "Аккаунт создан!")
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином уже существует")
        except Exception as e:
            print(f"Ошибка регистрации: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка регистрации: {str(e)}")


class MainMenuWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent  # Это MentalHealthApp
        self.current_user = None
        self.mood_chart = None
        self.mood_buttons = []
        self.welcome_label = None
        self.user_info_label = None
        self.logout_btn = None
        self.stats_widgets = {}
        self.music_button = None
        self.init_ui()

    def set_current_user(self, user):
        """Установка текущего пользователя (вызывается из MentalHealthApp)"""
        self.current_user = user
        self.update_display()
        self.update_user_info()  # Обновляем информацию в верхней панели

    def update_display(self):
        """Обновление отображения главного меню"""
        try:
            print(f"MainMenuWindow: обновление для пользователя {self.current_user}")

            if not self.current_user:
                # Если пользователя нет, показываем "Гость" или скрываем элементы
                name = "Гость"
                if hasattr(self, 'welcome_label') and self.welcome_label:
                    self.welcome_label.setText(f"Добро пожаловать, {name}! 🌼")
                return

            # Обновляем приветствие
            name = self.current_user.get('name', 'Пользователь')
            if hasattr(self, 'welcome_label') and self.welcome_label:
                self.welcome_label.setText(f"Добро пожаловать, {name}! 🌼")

            # Обновляем настроение
            self.update_mood_display()

            # Обновляем график
            if self.mood_chart:
                self.update_chart_data()

            self.update_stats_section()

            self.update_insights()

        except Exception as e:
            print(f"Ошибка обновления отображения: {e}")

    def update_insights(self):
        """Обновление карточки с инсайтами"""
        try:
            # Находим карточку инсайтов (если существует)
            if hasattr(self, 'insights_card'):
                # Пересоздаем инсайты
                insights = self.generate_insights()

                # Очищаем старые инсайты
                layout = self.insights_card.layout()
                if layout:
                    # Удаляем все виджеты кроме заголовка
                    while layout.count() > 1:
                        item = layout.takeAt(1)
                        if item.widget():
                            item.widget().deleteLater()

                    # Добавляем новые инсайты
                    for insight in insights:
                        insight_frame = QFrame()
                        insight_layout = QHBoxLayout(insight_frame)
                        insight_layout.setContentsMargins(0, 0, 0, 0)
                        insight_layout.setSpacing(10)

                        # Иконка
                        icon = QLabel("✨")
                        icon.setStyleSheet("font-size: 16px;")
                        insight_layout.addWidget(icon)

                        # Текст инсайта
                        text_label = QLabel(insight)
                        text_label.setProperty("class", "TextRegular")
                        text_label.setWordWrap(True)
                        insight_layout.addWidget(text_label, 1)

                        layout.addWidget(insight_frame)
        except Exception as e:
            print(f"Ошибка обновления инсайтов: {e}")

    def open_dna_profile(self):
        """Открытие окна профиля ДНК"""
        try:
            if not self.parent.current_user:
                QMessageBox.warning(self, "Ошибка", "Войдите в систему для доступа к профилю ДНК")
                return

            # Создаем окно если еще не создано
            if not hasattr(self.parent, 'dna_window'):
                self.parent.dna_window = DNAProfileWindow(self.parent)
                self.parent.stacked_widget.addWidget(self.parent.dna_window)

            # Обновляем данные перед показом
            self.parent.dna_window.update_profile()

            # Переходим
            index = self.parent.stacked_widget.indexOf(self.parent.dna_window)
            self.parent.stacked_widget.setCurrentIndexWithAnimation(index)

        except Exception as e:
            print(f"Ошибка при открытии профиля ДНК: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть профиль ДНК")

    def open_chat_bot(self):
        """Открыть чат с ботом"""
        try:
            if not hasattr(self.parent, 'enhanced_chat_window'):
                self.parent.enhanced_chat_window = EnhancedChatBotWindow(self.parent)
                self.parent.stacked_widget.addWidget(self.parent.enhanced_chat_window)

            index = self.parent.stacked_widget.indexOf(self.parent.enhanced_chat_window)
            self.parent.stacked_widget.setCurrentIndexWithAnimation(index)

        except Exception as e:
            print(f"Ошибка при открытии чата: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть чат")

    def update_user_info(self):
        """Обновление информации о пользователе в верхней панели"""
        try:
            if hasattr(self, 'user_info_label') and self.user_info_label:
                if self.current_user:
                    name = self.current_user.get('name', 'Пользователь')
                    self.user_info_label.setText(f"👤 {name}")
                    self.user_info_label.setProperty("class", "TextRegular")
                    if hasattr(self, 'logout_btn') and self.logout_btn:
                        self.logout_btn.setVisible(True)
                else:
                    self.user_info_label.setText("👤 Гость")
                    self.user_info_label.setProperty("class", "TextLight")
                    if hasattr(self, 'logout_btn') and self.logout_btn:
                        self.logout_btn.setVisible(False)
        except Exception as e:
            print(f"Ошибка обновления информации пользователя: {e}")

    def update_mood_display(self):
        """Обновление отображения настроения"""
        try:
            if not self.current_user:
                # Сбрасываем кнопки настроения для гостя
                for btn in self.mood_buttons:
                    btn.setChecked(False)
                return

            # Получаем сегодняшнее настроение из БД
            today_mood = self.parent.db.get_today_mood(self.current_user['id'])

            # Сбрасываем все кнопки
            for btn in self.mood_buttons:
                btn.setChecked(False)

            # Устанавливаем выбранное значение
            if today_mood and 1 <= today_mood <= 10:
                self.mood_buttons[today_mood - 1].setChecked(True)
        except Exception as e:
            print(f"Ошибка обновления настроения: {e}")

    def update_chart_data(self):
        """Обновление данных графика"""
        try:
            if not self.current_user:
                return

            if self.mood_chart:
                # Получаем реальные данные из БД
                entries = self.parent.db.get_mood_entries(self.current_user['id'], days=7)

                if entries:
                    # Передаем реальные данные в график
                    self.mood_chart.update_with_real_data(entries)
                else:
                    # Если данных нет, показываем сообщение
                    print(f"Нет данных настроения для пользователя {self.current_user['id']}")
                    # Можно показать демо-данные или сообщение
                    self.mood_chart.generate_sample_data()
                    self.mood_chart.plot_chart()
        except Exception as e:
            print(f"Ошибка обновления графика: {e}")

    def init_ui(self):
        """Инициализация интерфейса главного меню"""
        # Сначала создаем график настроения
        self.mood_chart = MoodChartWidget()

        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Верхняя панель
        self.create_top_bar(main_layout)

        # Прокручиваемая область
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)
        main_layout.addWidget(scroll_area)

        # Контент внутри прокрутки
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(30)
        content_layout.setContentsMargins(40, 30, 40, 40)

        # Приветствие и настроение
        self.create_welcome_section(content_layout)

        # Быстрые действия
        self.create_quick_actions(content_layout)

        # Основные функции
        self.create_main_functions(content_layout)

        # Нижняя часть (2 колонки)
        self.create_bottom_section(content_layout)

        self.music_button = MusicButton(self)
        self.update_music_button_position()
    def create_top_bar(self, parent_layout):
        """Создание верхней панели"""
        top_bar = QFrame()
        top_bar.setFixedHeight(70)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #F8F2E9;
                border-bottom: 1px solid #E8DFD8;
            }
        """)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(30, 0, 30, 0)

        # Инициализируем метку пользователя (будет обновлена позже)
        self.user_info_label = QLabel("👤 Гость")
        self.user_info_label.setProperty("class", "TextRegular")
        top_layout.addWidget(self.user_info_label)

        # Логотип и название
        logo_frame = QFrame()
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(15)

        emoji = QLabel("🌿")
        emoji.setStyleSheet("font-size: 24px;")
        logo_layout.addWidget(emoji)

        title = QLabel("Тёплое убежище")
        title.setProperty("class", "TitleMedium")
        logo_layout.addWidget(title)

        top_layout.addWidget(logo_frame)
        top_layout.addStretch()

        # Кнопка выхода
        self.logout_btn = QPushButton("Выйти")
        self.logout_btn.setProperty("class", "SecondaryButton")
        self.logout_btn.clicked.connect(self.logout)
        top_layout.addWidget(self.logout_btn)

        parent_layout.addWidget(top_bar)

        # Сразу обновляем отображение пользователя
        self.update_user_info()

    def resizeEvent(self, event):
        """Обновление позиции при изменении размера"""
        super().resizeEvent(event)
        self.update_music_button_position()

    def update_music_button_position(self):
        """Обновление позиции музыкальной кнопки (правый нижний угол)"""
        if self.music_button:
            self.music_button.move(self.width() - 70, self.height() - 70)
            self.music_button.raise_()

    def logout(self):
        """Выход из аккаунта"""
        try:
            self.parent.set_current_user(None)
            self.parent.stacked_widget.setCurrentIndexWithAnimation(0)
            self.update_user_info()  # Обновляем отображение после выхода
        except Exception as e:
            print(f"Ошибка выхода: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка выхода: {str(e)}")

    def create_welcome_section(self, parent_layout):
        """Создание секции приветствия"""
        welcome_frame = QFrame()
        welcome_frame.setStyleSheet("background-color: transparent;")

        welcome_layout = QVBoxLayout(welcome_frame)
        welcome_layout.setSpacing(15)

        # Приветствие
        name = "Гость" if not self.current_user else self.current_user.get('name', 'Пользователь')
        self.welcome_label = QLabel(f"Добро пожаловать, {name}! 🌼")
        self.welcome_label.setProperty("class", "TitleLarge")
        welcome_layout.addWidget(self.welcome_label)

        # Дата
        date_label = QLabel(datetime.now().strftime("%d %B %Y"))
        date_label.setProperty("class", "TextSecondary")
        welcome_layout.addWidget(date_label)

        # Добавляем график настроения (теперь он точно существует)
        welcome_layout.addWidget(self.mood_chart)

        # Карточка выбора настроения (ниже графика)
        mood_card = self.create_mood_card()
        welcome_layout.addWidget(mood_card)

        # Карточка с инсайтами
        insights_card = self.create_insights_card()
        welcome_layout.addWidget(insights_card)

        parent_layout.addWidget(welcome_frame)

    def create_mood_card(self):
        """Создание карточки выбора настроения"""
        card = QFrame()
        card.setProperty("class", "WarmCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(20)

        # Заголовок
        title_frame = QFrame()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)

        emoji = QLabel("🌱")
        emoji.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(emoji)

        title = QLabel("Как вы себя чувствуете сегодня?")
        title.setProperty("class", "TitleSmall")
        title_layout.addWidget(title)
        title_layout.addStretch()

        card_layout.addWidget(title_frame)

        # Шкала настроения
        scale_widget = self.create_mood_scale()
        card_layout.addWidget(scale_widget)

        # Кнопка сохранения
        save_btn = QPushButton("💾 Сохранить настроение")
        save_btn.setProperty("class", "SecondaryButton")
        save_btn.clicked.connect(lambda: self.show_success_message("Настроение сохранено! 🌈"))
        card_layout.addWidget(save_btn)

        return card

    def create_mood_scale(self):
        """Создание шкалы настроения"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # Круги настроения
        circles_frame = QFrame()
        circles_layout = QHBoxLayout(circles_frame)
        circles_layout.setSpacing(8)
        circles_layout.setAlignment(Qt.AlignCenter)

        self.mood_buttons = []
        for i in range(10):
            btn = MoodButton(i + 1, self)
            btn.setFixedSize(42, 42)

            # Автоматически выбираем 6-ю точку
            if i == 5:
                btn.setChecked(True)

            circles_layout.addWidget(btn)
            self.mood_buttons.append(btn)

        layout.addWidget(circles_frame)

        # Подписи
        labels_frame = QFrame()
        labels_layout = QHBoxLayout(labels_frame)
        labels_layout.setContentsMargins(0, 0, 0, 0)

        left_label = QLabel("грусть")
        left_label.setProperty("class", "TextLight")
        labels_layout.addWidget(left_label)

        labels_layout.addStretch()

        right_label = QLabel("радость")
        right_label.setProperty("class", "TextLight")
        labels_layout.addWidget(right_label)

        layout.addWidget(labels_frame)

        return widget

    def create_quick_actions(self, parent_layout):
        """Создание секции быстрых действий"""
        frame = QFrame()
        frame.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout(frame)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("🚀 Быстрые действия")
        title.setProperty("class", "TitleMedium")
        layout.addWidget(title)

        # Кнопки действий
        actions_frame = QFrame()
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setSpacing(20)

        actions = [
            ("📝", "Новая запись", lambda: self.show_message("Переход к новой записи")),
            ("😊", "Настроение", lambda: self.show_mood_dialog()),
            ("🌬️", "Дыхание", self.open_breathing_exercise),
            ("📊", "Статистика", lambda: self.show_message("Просмотр статистики")),
        ]

        for emoji, text, callback in actions:
            action_card = self.create_action_card(emoji, text, callback)
            actions_layout.addWidget(action_card)

        layout.addWidget(actions_frame)
        parent_layout.addWidget(frame)

    def open_breathing_exercise(self):
        """Открыть дыхательное упражнение"""
        try:
            if not hasattr(self.parent, 'breathing_window'):
                self.parent.breathing_window = SimpleBreathingExercise(self.parent)

            self.parent.breathing_window.show()

        except Exception as e:
            print(f"Ошибка открытия дыхательного упражнения: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть упражнение")

    def create_action_card(self, emoji, text, callback):
        """Создание карточки действия"""
        card = QPushButton()
        card.setFixedSize(130, 130)
        card.clicked.connect(callback)
        card.setProperty("class", "ActionCard")

        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(12)

        emoji_label = QLabel(emoji)
        emoji_label.setStyleSheet("font-size: 36px;")
        card_layout.addWidget(emoji_label)

        text_label = QLabel(text)
        text_label.setProperty("class", "TextRegular")
        text_label.setStyleSheet("font-weight: 600;")
        text_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(text_label)

        return card

    def create_main_functions(self, parent_layout):
        """Создание секции основных функций"""
        frame = QFrame()
        frame.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout(frame)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("📋 Основные функции")
        title.setProperty("class", "TitleMedium")
        layout.addWidget(title)

        # Функции
        functions = [
            ("Дневник мыслей", "Запись и анализ автоматических мыслей", "#B5E5CF", self.open_diary),
            ("Упражнения КПТ", "Практики для работы с эмоциями", "#FFD6DC", self.open_exercises),
            ("История записей", "Просмотр вашего прогресса", "#FFB38E", self.open_history),
            ("Достижения", "Ваш прогресс и награды", "FFD166", self.open_achievements),
            ("🧬 Профиль здоровья", "Ваш индивидуальный профиль ментального здоровья", "#9B59B6", self.open_dna_profile),
            ("🤖 Интеллектуальный анализ", "Глубокий анализ и прогнозы", "#9B59B6", self.open_intelligence_dashboard),
            ("📊 Экспорт данных", "Сохраните отчеты в PDF, CSV", "#3498DB", self.open_exporter),
            ("📅 Календарь настроения", "Визуализация по дням", "#E67E22", self.open_calendar),
            ("🌙 Темная тема", "Переключение темы оформления", "#2C3E50", self.toggle_theme),
            ("👥 Групповая поддержка", "Общайтесь с единомышленниками", "#8E44AD", self.open_groups),
            ("💬 Душевный помощник", "Поговори с поддерживающим ботом", "#9B59B6", self.open_chat_bot),
            (
            "Настройки", "Настройте приложение под себя", "#E8DFD8", lambda: self.show_message("Скоро будет доступно")),
        ]

        for func_title, description, color, callback in functions:
            func_card = self.create_function_card(func_title, description, color, callback)
            layout.addWidget(func_card)

        parent_layout.addWidget(frame)

    def create_function_card(self, title, description, color, callback):
        """Создание анимированной карточки функции"""
        card = AnimatedButton(title, parent=self)
        card.setCursor(Qt.PointingHandCursor)
        card.clicked.connect(callback)

        # Цвета
        darker_color = self.darken_color(color)

        # Стили с плавными переходами
        card.setStyleSheet(f"""
            AnimatedButton {{
                background-color: #FFFFFF;
                border-radius: 16px;
                border-left: 8px solid {color};
                border-right: 1px solid #E8DFD8;
                border-top: 1px solid #E8DFD8;
                border-bottom: 1px solid #E8DFD8;
                padding: 24px;
                text-align: left;
                transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            }}
            AnimatedButton:hover {{
                background-color: #F8F2E9;
                border-left: 8px solid {darker_color};
                border-right: 1px solid {darker_color};
                border-top: 1px solid {darker_color};
                border-bottom: 1px solid {darker_color};
                transform: translateY(-4px);
                box-shadow: 0 12px 24px rgba(139, 115, 85, 0.12);
            }}
        """)

        # Создаем layout внутри кнопки
        layout = QHBoxLayout(card)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        # Текст
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setSpacing(10)
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 700;
                color: #5A5A5A;
                margin: 0;
                padding: 0;
            }
        """)
        text_layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #8B7355;
                margin: 0;
                padding: 0;
                line-height: 1.4;
            }
        """)
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)

        layout.addWidget(text_widget, 1)

        # Анимированная стрелка
        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                color: #C4B6A6;
                font-weight: bold;
                transition: all 0.3s ease;
            }
        """)
        layout.addWidget(arrow_label)

        # Анимация стрелки при наведении
        def on_hover():
            arrow_label.setStyleSheet("""
                QLabel {
                    font-size: 32px;
                    color: #9BD1B8;
                    font-weight: bold;
                    transform: translateX(4px);
                }
            """)

        def on_leave():
            arrow_label.setStyleSheet("""
                QLabel {
                    font-size: 28px;
                    color: #C4B6A6;
                    font-weight: bold;
                }
            """)

        # Подключаем события
        card.enterEvent = lambda e: on_hover()
        card.leaveEvent = lambda e: on_leave()

        # Устанавливаем фиксированную высоту
        card.setFixedHeight(120)

        return card

    def open_diary(self):
        """Открытие дневника мыслей с анимацией"""
        try:
            self.parent.stacked_widget.setCurrentIndexWithAnimation(2)
        except Exception as e:
            print(f"Ошибка при открытии дневника: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть дневник")

    def open_exporter(self):
        """Открыть экспорт данных"""
        dialog = DataExporter(self.parent)
        dialog.show()

    def open_calendar(self):
        """Открыть календарь настроения"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("📅 Календарь настроения")
        dialog.setFixedSize(800, 600)

        layout = QVBoxLayout(dialog)
        calendar = MoodCalendar(self.parent)
        layout.addWidget(calendar)

        dialog.exec_()

    def toggle_theme(self):
        """Переключение темы"""
        if not hasattr(self.parent, 'theme_manager'):
            self.parent.theme_manager = ThemeManager(self.parent)
        self.parent.theme_manager.toggle_theme()

    def open_groups(self):
        """Открыть групповую поддержку"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("👥 Групповая поддержка")
        dialog.setFixedSize(600, 500)

        layout = QVBoxLayout(dialog)
        groups = GroupSupportWidget(self.parent)
        layout.addWidget(groups)

        dialog.exec_()

    def open_exercises(self):
        """Открытие окна упражнений с анимацией"""
        try:
            self.parent.stacked_widget.setCurrentIndexWithAnimation(3)
        except Exception as e:
            print(f"Ошибка при открытии упражнений: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть упражнения")

    def open_history(self):
        """Открытие окна истории с анимацией"""
        try:
            # Просто переходим на окно истории
            self.parent.stacked_widget.setCurrentIndexWithAnimation(4)

            # Обновление произойдет автоматически в HistoryWindow.showEvent()
            # или можно вызвать здесь:
            if hasattr(self.parent, 'history_window'):
                self.parent.history_window.update_display()

        except Exception as e:
            print(f"Ошибка при открытии истории: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть историю")

    def open_achievements(self):
        """Открытие окна достижений"""
        try:
            # Создаем окно достижений если еще не создано
            if not hasattr(self.parent, 'achievements_window'):
                self.parent.achievements_window = AchievementsWindow(self.parent)
                self.parent.stacked_widget.addWidget(self.parent.achievements_window)

            # Обновляем данные
            self.parent.achievements_window.update_display()

            # Переходим
            index = self.parent.stacked_widget.indexOf(self.parent.achievements_window)
            self.parent.stacked_widget.setCurrentIndexWithAnimation(index)
        except Exception as e:
            print(f"Ошибка при открытии достижений: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть достижения")

    def open_intelligence_dashboard(self):
        """Открытие расширенного дашборда интеллектуального анализа"""
        try:
            if not self.parent.current_user:
                QMessageBox.warning(self, "Ошибка", "Войдите в систему для доступа к анализу")
                return

            if not hasattr(self.parent, 'intelligence_window'):
                self.parent.intelligence_window = IntelligenceDashboard(self.parent)
                self.parent.stacked_widget.addWidget(self.parent.intelligence_window)

            # Обновляем все данные
            self.parent.intelligence_window.load_intelligence_data()

            # Переходим
            index = self.parent.stacked_widget.indexOf(self.parent.intelligence_window)
            self.parent.stacked_widget.setCurrentIndexWithAnimation(index)

        except Exception as e:
            print(f"Ошибка при открытии интеллектуального анализа: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть интеллектуальный анализ")

    def create_insights_card(self):
        """Карточка с инсайтами на основе данных"""
        self.insights_card = QFrame()
        self.insights_card.setProperty("class", "SoftPinkCard")

        layout = QVBoxLayout(self.insights_card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Заголовок
        title_frame = QFrame()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)

        emoji = QLabel("💡")
        emoji.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(emoji)

        title = QLabel("Ваши инсайты")
        title.setProperty("class", "TitleSmall")
        title_layout.addWidget(title)
        title_layout.addStretch()

        layout.addWidget(title_frame)

        # Генерация инсайтов на основе "данных"
        insights = self.generate_insights()

        for insight in insights:
            insight_frame = QFrame()
            insight_layout = QHBoxLayout(insight_frame)
            insight_layout.setContentsMargins(0, 0, 0, 0)
            insight_layout.setSpacing(10)

            # Иконка
            icon = QLabel("✨")
            icon.setStyleSheet("font-size: 16px;")
            insight_layout.addWidget(icon)

            # Текст инсайта
            text_label = QLabel(insight)
            text_label.setProperty("class", "TextRegular")
            text_label.setWordWrap(True)
            insight_layout.addWidget(text_label, 1)

            layout.addWidget(insight_frame)

        return self.insights_card

    def generate_insights(self):
        """Генерация персональных инсайтов на основе реальных данных"""
        insights = []

        if not self.current_user:
            # Инсайты для гостя
            return [
                "Войдите в систему, чтобы увидеть персональные инсайты",
                "Регулярное ведение дневника помогает отслеживать прогресс",
                "Начните с записи сегодняшнего настроения"
            ]

        try:
            # Получаем реальные данные
            mood_entries = self.parent.db.get_mood_entries(self.current_user['id'], days=7)
            diary_stats = self.parent.db.get_diary_stats(self.current_user['id'])

            # Генерация инсайтов на основе данных
            if mood_entries and len(mood_entries) > 1:
                mood_scores = [entry['mood_score'] for entry in mood_entries]
                avg_mood = sum(mood_scores) / len(mood_scores)

                if avg_mood > 7:
                    insights.append(f"Ваше среднее настроение: {avg_mood:.1f}/10 - отличный результат! 🌟")
                elif avg_mood > 5:
                    insights.append(f"Ваше среднее настроение: {avg_mood:.1f}/10 - хороший уровень 👍")
                else:
                    insights.append(
                        f"Ваше среднее настроение: {avg_mood:.1f}/10 - попробуйте упражнения для поднятия настроения")

                # Анализ тренда
                if len(mood_scores) >= 2:
                    trend = mood_scores[-1] - mood_scores[0]
                    if trend > 1:
                        insights.append("Настроение улучшается - продолжайте в том же духе! ↗️")
                    elif trend < -1:
                        insights.append("Заметили спад настроения - возможно, стоит отдохнуть 📉")

            if diary_stats['total_entries'] > 0:
                insights.append(f"Вы сделали {diary_stats['total_entries']} записей - это отлично! 📝")

                if diary_stats['common_distortions']:
                    most_common = max(diary_stats['common_distortions'].items(), key=lambda x: x[1], default=None)
                    if most_common:
                        insights.append(f"Частое искажение: {most_common[0]} ({most_common[1]} раз)")

            if not insights:
                insights.append("Начните вести дневник для получения персональных инсайтов")
                insights.append("Отмечайте настроение каждый день для лучшего анализа")
                insights.append("Попробуйте упражнения КПТ для работы с мыслями")

        except Exception as e:
            print(f"Ошибка генерации инсайтов: {e}")
            insights = [
                "Анализ данных временно недоступен",
                "Продолжайте использовать приложение",
                "Ваши данные сохраняются безопасно"
            ]

        return insights[:3]

    def update_stats_section(self):
        """Обновление статистики на главной странице (новая версия)"""
        try:
            if not self.parent or not self.parent.current_user:
                print("DEBUG: Нет пользователя для обновления статистики")
                return

            user_id = self.parent.current_user['id']
            print(f"DEBUG: Обновление статистики для user_id={user_id}")

            # Получаем статистику
            diary_stats = self.parent.db.get_diary_stats(user_id)
            print(f"DEBUG: diary_stats = {diary_stats}")

            if not diary_stats:
                print("DEBUG: Нет статистики")
                return

            # Получаем статистику настроения
            mood_entries = self.parent.db.get_mood_entries(user_id, days=30)
            print(f"DEBUG: mood_entries count = {len(mood_entries) if mood_entries else 0}")

            # Рассчитываем среднее настроение
            avg_mood = 0
            if mood_entries and len(mood_entries) > 0:
                mood_scores = [entry['mood_score'] for entry in mood_entries if entry['mood_score'] > 0]
                avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0

            print(f"DEBUG: avg_mood = {avg_mood}")

            # Обновляем виджеты статистики
            if 'total_entries' in self.stats_widgets:
                self.stats_widgets['total_entries'].setText(str(diary_stats.get('total_entries', 0)))
                print(f"DEBUG: Обновлено Всего записей: {diary_stats.get('total_entries', 0)}")

            if 'days_with_entries' in self.stats_widgets:
                self.stats_widgets['days_with_entries'].setText(str(diary_stats.get('days_with_entries', 0)))
                print(f"DEBUG: Обновлено Дней с записями: {diary_stats.get('days_with_entries', 0)}")

            if 'avg_mood' in self.stats_widgets:
                self.stats_widgets['avg_mood'].setText(f"{avg_mood:.1f}/10")
                print(f"DEBUG: Обновлено Среднее настроение: {avg_mood:.1f}/10")

            if 'common_distortion' in self.stats_widgets:
                common_distortions = diary_stats.get('common_distortions', {})
                if common_distortions and isinstance(common_distortions, dict) and common_distortions:
                    most_common = max(common_distortions.items(), key=lambda x: x[1], default=("Нет данных", 0))
                    self.stats_widgets['common_distortion'].setText(f"{most_common[0]} ({most_common[1]} раз)")
                    print(f"DEBUG: Обновлено Частое искажение: {most_common[0]}")
                else:
                    self.stats_widgets['common_distortion'].setText("Нет данных")

            print("DEBUG: Статистика обновлена успешно")

        except Exception as e:
            print(f"Ошибка обновления статистики: {e}")
            import traceback
            traceback.print_exc()

    def create_bottom_section(self, parent_layout):
        """Создание нижней секции с реальной статистикой"""
        frame = QFrame()
        frame.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout(frame)
        layout.setSpacing(30)

        # Левая колонка - цитата
        quote_card = QFrame()
        quote_card.setProperty("class", "MintCard")

        quote_layout = QVBoxLayout(quote_card)
        quote_layout.setContentsMargins(25, 25, 25, 25)
        quote_layout.setSpacing(20)

        quote_emoji = QLabel("💭")
        quote_emoji.setStyleSheet("font-size: 32px;")
        quote_emoji.setAlignment(Qt.AlignCenter)
        quote_layout.addWidget(quote_emoji)

        quote_text = QLabel(self.get_daily_quote())
        quote_text.setStyleSheet("""
            font-size: 16px;
            color: #5A5A5A;
            font-style: italic;
            line-height: 1.4;
        """)
        quote_text.setWordWrap(True)
        quote_text.setAlignment(Qt.AlignCenter)
        quote_layout.addWidget(quote_text)

        layout.addWidget(quote_card)

        # Правая колонка - статистика и помощь
        right_column = QFrame()
        right_column.setStyleSheet("background-color: transparent;")
        right_layout = QVBoxLayout(right_column)
        right_layout.setSpacing(20)

        # Статистика (реальная)
        self.stats_card = QFrame()
        self.stats_card.setProperty("class", "WarmCard")

        stats_layout = QVBoxLayout(self.stats_card)
        stats_layout.setContentsMargins(25, 25, 25, 25)
        stats_layout.setSpacing(20)

        stats_title = QLabel("📊 Ваша статистика")
        stats_title.setProperty("class", "TitleSmall")
        stats_layout.addWidget(stats_title)

        # Получаем реальную статистику
        if self.current_user:
            try:
                diary_stats = self.parent.db.get_diary_stats(self.current_user['id'])
                mood_entries = self.parent.db.get_mood_entries(self.current_user['id'], days=30)

                # Расчет дней подряд
                consecutive_days = self.calculate_consecutive_days()

                if mood_entries:
                    mood_scores = [entry['mood_score'] for entry in mood_entries]
                    avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0
                else:
                    avg_mood = 0

                stats = [
                    ("Дней подряд", str(consecutive_days)),
                    ("Всего записей", str(diary_stats['total_entries'])),
                    ("Среднее настроение", f"{avg_mood:.1f}/10"),
                ]
            except Exception as e:
                print(f"Ошибка получения статистики: {e}")
                stats = [
                    ("Дней подряд", "0"),
                    ("Всего записей", "0"),
                    ("Среднее настроение", "0/10"),
                ]
        else:
            stats = [
                ("Дней подряд", "0"),
                ("Всего записей", "0"),
                ("Среднее настроение", "0/10"),
            ]

        for label, value in stats:
            stat_frame = QFrame()
            stat_layout = QHBoxLayout(stat_frame)
            stat_layout.setContentsMargins(0, 0, 0, 0)

            label_widget = QLabel(label)
            label_widget.setProperty("class", "TextSecondary")
            stat_layout.addWidget(label_widget)

            stat_layout.addStretch()

            value_widget = QLabel(value)
            value_widget.setProperty("class", "TextRegular")
            value_widget.setStyleSheet("font-weight: bold;")
            stat_layout.addWidget(value_widget)

            stats_layout.addWidget(stat_frame)

        right_layout.addWidget(self.stats_card)

        # Кнопка помощи
        help_btn = QPushButton("💝 Мне нужна поддержка")
        help_btn.setProperty("class", "EmergencyButton")
        help_btn.setMinimumHeight(60)
        help_btn.clicked.connect(self.show_emergency_help)
        right_layout.addWidget(help_btn)

        layout.addWidget(right_column)

        parent_layout.addWidget(frame)

    def calculate_consecutive_days(self):
        """Расчет дней подряд с записями настроения"""
        if not self.current_user:
            return 0

        try:
            entries = self.parent.db.get_mood_entries(self.current_user['id'], days=30)
            if not entries:
                return 0

            # Сортируем по дате
            dates = sorted([datetime.strptime(entry['date'], '%Y-%m-%d') for entry in entries])

            # Проверяем последовательные дни
            consecutive = 1
            for i in range(len(dates) - 1, 0, -1):
                if (dates[i] - dates[i - 1]).days == 1:
                    consecutive += 1
                else:
                    break

            return consecutive
        except Exception as e:
            print(f"Ошибка расчета дней подряд: {e}")
            return 0

    def get_daily_quote(self):
        """Получение случайной цитаты"""
        quotes = [
            "Забота о себе — не эгоизм, а необходимость.",
            "Маленькие шаги приводят к большим переменам.",
            "Твои чувства важны и имеют значение.",
            "Сегодня ты сделал всё, что мог, и это достаточно.",
            "Ты не один на этом пути. 💝"
        ]
        return random.choice(quotes)

    def darken_color(self, hex_color):
        """Затемнить цвет"""
        colors = {
            "#B5E5CF": "#9BD1B8",
            "#FFD6DC": "#FFC8D6",
            "#FFB38E": "#FF9E70",
            "#E8DFD8": "#D7CCC8",
        }
        return colors.get(hex_color, hex_color)

    def show_success_message(self, text):
        """Показать стилизованное успешное сообщение"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(text)
        msg_box.setWindowTitle("Успешно")
        msg_box.setStandardButtons(QMessageBox.Ok)

        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #FFFBF6;
                border: 1px solid #E8DFD8;
                border-radius: 12px;
            }
            QMessageBox QLabel {
                color: #5A5A5A;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #B5E5CF;
                color: #5A5A5A;
                border-radius: 6px;
                padding: 8px 20px;
                border: 1px solid #9BD1B8;
                font-weight: 600;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #9BD1B8;
            }
        """)

        msg_box.exec_()

    def show_message(self, text):
        """Показать информационное сообщение"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(text)
        msg_box.setWindowTitle("Информация")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def show_mood_dialog(self):
        """Показать диалог настроения"""
        self.show_message("Откройте дневник для записи настроения")

    def show_breathing_exercise(self):
        """Показать упражнение на дыхание"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Упражнение на дыхание")
        msg_box.setText("""
            <h3>🌬 Упражнение на дыхание</h3>
            <p>1. Сядьте удобно, положите руку на живот</p>
            <p>2. Медленно вдохните через нос на 4 счета</p>
            <p>3. Задержите дыхание на 4 счета</p>
            <p>4. Медленно выдохните через рот на 6 счетов</p>
            <p>5. Повторите 5 раз</p>
            <br>
            <p><i>Это упражнение поможет снизить тревожность.</i></p>
        """)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def show_emergency_help(self):
        """Показать экстренную помощь"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Поддержка здесь")
        msg_box.setText("""
            <h3>💝 Если вам прямо сейчас тяжело:</h3>
            <p>1. <b>🌬 Сделайте 3 глубоких вдоха</b><br>
            &nbsp;&nbsp;&nbsp;Вдох на 4, задержка на 4, выдох на 6</p>

            <p>2. <b>📞 Позвоните на горячую линию</b><br>
            &nbsp;&nbsp;&nbsp;8-800-2000-122 (бесплатно по России)</p>

            <p>3. <b>🌿 Найдите 5 вещей вокруг вас</b><br>
            &nbsp;&nbsp;&nbsp;5 вещей, которые видите<br>
            &nbsp;&nbsp;&nbsp;4 вещи, которые чувствуете<br>
            &nbsp;&nbsp;&nbsp;3 звука, которые слышите</p>

            <p>4. <b>📝 Запишите всё, что чувствуете</b></p>

            <br>
            <p><i>Обращение за помощью — это признак силы.</i></p>
        """)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()


class MentalHealthBot:
    """Интеллектуальный чат-бот для поддержки ментального здоровья"""

    def __init__(self, db, user_id=None):
        self.db = db
        self.user_id = user_id
        self.context = {
            'last_topic': None,
            'user_mood': None,
            'conversation_history': [],
            'suggested_exercises': [],
            'emergency_mode': False
        }

        # Приветствия
        self.greetings = [
            "Привет! Как ты сегодня? 🌼",
            "Здравствуй! Рада тебя видеть. Как настроение? 🌸",
            "Приветствую! Чем могу помочь сегодня? 💫",
            "Здравствуй! Как проходит твой день? 🌿"
        ]

        # Словарь ответов по темам
        self.responses = {
            'тревога': [
                "Я слышу, что ты испытываешь тревогу. Это нормальная реакция. Давай попробуем дыхательное упражнение? 🌬️",
                "Тревога может быть очень тяжелой. Помни, что это временное состояние. Хочешь сделать упражнение на заземление? 🌱",
                "Когда тревога накрывает, попробуй технику 5-4-3-2-1. Назови 5 вещей, которые видишь, 4, которые чувствуешь, 3 звука, 2 запаха и 1 вкус."
            ],
            'грусть': [
                "Грустить — это нормально. Ты не один. Что обычно помогает тебе почувствовать себя лучше? 💙",
                "Мне жаль, что тебе грустно. Хочешь поговорить о том, что случилось? Иногда просто выговориться помогает.",
                "Грусть — как волна, она приходит и уходит. Помни, что за дождем всегда выходит солнце. ☀️"
            ],
            'гнев': [
                "Злость — это сигнал, что что-то не так. Попробуй сделать глубокий вдох и медленный выдох. 🔥",
                "Когда чувствуешь гнев, важно не подавлять его, но и не выплескивать разрушительно. Может, побить подушку? 💢",
                "Гнев часто маскирует другие чувства — боль, страх, обиду. Что стоит за твоим гневом?"
            ],
            'усталость': [
                "Усталость — сигнал, что нужен отдых. Разреши себе pause. 🌙",
                "Ты много делаешь! Помни, что отдых так же важен, как работа. Хочешь технику быстрого расслабления?",
                "Даже 5 минут тишины могут восстановить силы. Попробуй закрыть глаза и просто посидеть в тишине."
            ],
            'одиночество': [
                "Чувство одиночества знакомо многим. Помни, что ты не один, даже если сейчас так кажется. 🤗",
                "Даже среди людей можно чувствовать себя одиноким. Что обычно приносит тебе чувство связи с другими?",
                "Одиночество — это не про количество людей вокруг, а про качество связей. Ты важен и ценен сам по себе."
            ]
        }

        # Мотивирующие цитаты
        self.quotes = [
            "«Ты сильнее, чем думаешь, и смелее, чем кажется»",
            "«Маленькие шаги каждый день ведут к большим переменам»",
            "«Забота о себе — не эгоизм, а необходимость»",
            "«Сегодня ты сделал все, что мог, и этого достаточно»",
            "«Ты не обязан быть идеальным, чтобы быть ценным»",
            "«Лучший способ предсказать будущее — создать его»",
            "«Будь добр к себе — ты делаешь все, что в твоих силах»",
            "«Ты заслуживаешь покоя и счастья прямо сейчас»"
        ]

        # Упражнения КПТ
        self.exercises = {
            'дыхание': {
                'name': '🌬️ Дыхание 4-7-8',
                'instructions': [
                    "Сядь удобно, выпрями спину",
                    "Вдохни через нос на 4 счета",
                    "Задержи дыхание на 7 счетов",
                    "Медленно выдохни через рот на 8 счетов",
                    "Повтори 4 раза"
                ]
            },
            'заземление': {
                'name': '🌱 Техника 5-4-3-2-1',
                'instructions': [
                    "Назови 5 вещей, которые видишь вокруг",
                    "Назови 4 вещи, которые чувствуешь (текстуры, температура)",
                    "Назови 3 звука, которые слышишь",
                    "Назови 2 запаха, которые чувствуешь",
                    "Назови 1 вкус, который ощущаешь"
                ]
            },
            'мысли': {
                'name': '🧠 Анализ автоматических мыслей',
                'instructions': [
                    "Запиши ситуацию, которая вызвала дискомфорт",
                    "Запиши автоматическую мысль, которая пришла",
                    "Найди доказательства ЗА эту мысль",
                    "Найди доказательства ПРОТИВ этой мысли",
                    "Сформулируй более сбалансированную мысль"
                ]
            },
            'благодарность': {
                'name': '💝 Дневник благодарности',
                'instructions': [
                    "Запиши 3 вещи, за которые ты благодарен сегодня",
                    "Они могут быть очень простыми (вкусный чай, солнце, улыбка прохожего)",
                    "Почувствуй благодарность в теле"
                ]
            }
        }

    def get_response(self, message):
        """Получить ответ бота на сообщение пользователя"""
        message = message.lower().strip()

        # Сохраняем в историю
        self.context['conversation_history'].append({
            'user': message,
            'timestamp': datetime.now()
        })

        # Проверка на экстренную ситуацию
        if self.is_emergency(message):
            self.context['emergency_mode'] = True
            return self.get_emergency_response()

        # Проверка на запрос упражнения
        if any(word in message for word in ['упражнение', 'упражнения', 'помоги', 'помощь', 'сделать']):
            return self.suggest_exercise(message)

        # Проверка на приветствие
        if any(word in message for word in ['привет', 'здравствуй', 'хай', 'здарова']):
            return random.choice(self.greetings)

        # Проверка на эмоции
        for emotion, responses in self.responses.items():
            if emotion in message:
                self.context['last_topic'] = emotion
                return random.choice(responses)

        # Проверка на цитату
        if any(word in message for word in ['цитата', 'мотивация', 'вдохновение']):
            return self.get_random_quote()

        # Проверка на состояние
        if any(word in message for word in ['как дела', 'как ты', 'что нового']):
            return self.get_mood_check_response()

        # Если ничего не подошло, используем общие ответы
        return self.get_general_response(message)

    def is_emergency(self, message):
        """Проверка на экстренную ситуацию"""
        emergency_words = [
            'плохо', 'умираю', 'убью', 'ненавижу', 'не хочу жить',
            'самоубийство', 'больно', 'крик', 'тошно', 'терпеть нет сил',
            'плохая мысль', 'страшно', 'кошмар'
        ]
        return any(word in message for word in emergency_words)

    def get_emergency_response(self):
        """Ответ в экстренной ситуации"""
        return """🚨 **Если тебе прямо сейчас очень плохо:**

1. **Позвони на горячую линию**: 8-800-2000-122 (круглосуточно, бесплатно)
2. **Напиши в чат помощи**: https://psyhelp.ru/chat
3. **Сделай заземление**: Назови 5 вещей, которые видишь вокруг
4. **Дыши глубоко**: Вдох на 4, задержка на 4, выдох на 6

Ты не один. Пожалуйста, обратись за помощью. 💝

Хочешь, я предложу упражнение, которое поможет прямо сейчас?"""

    def suggest_exercise(self, message):
        """Предложить упражнение"""
        if 'дыхание' in message:
            exercise = self.exercises['дыхание']
        elif 'заземление' in message or '5-4-3-2-1' in message:
            exercise = self.exercises['заземление']
        elif 'мысл' in message:
            exercise = self.exercises['мысли']
        elif 'благодарность' in message:
            exercise = self.exercises['благодарность']
        else:
            # Выбираем случайное
            exercise = random.choice(list(self.exercises.values()))

        response = f"**{exercise['name']}**\n\n"
        for i, step in enumerate(exercise['instructions'], 1):
            response += f"{i}. {step}\n"

        # Сохраняем в контекст
        self.context['suggested_exercises'].append(exercise['name'])

        return response

    def get_random_quote(self):
        """Получить случайную цитату"""
        return f"💭 {random.choice(self.quotes)}"

    def get_mood_check_response(self):
        """Ответ на вопрос о состоянии"""
        if self.user_id and self.db:
            # Проверяем сегодняшнее настроение
            today_mood = self.db.get_today_mood(self.user_id)

            if today_mood:
                mood_icons = {1: '😔', 2: '😕', 3: '😐', 4: '🙂', 5: '😊',
                              6: '😄', 7: '😁', 8: '😎', 9: '🤗', 10: '🥳'}
                icon = mood_icons.get(today_mood, '😐')
                return f"Сегодня твое настроение: {icon} {today_mood}/10\n\nА как у меня? Я здесь, чтобы поддерживать тебя! 🌟"

        return "У меня все отлично! Я здесь, чтобы помогать тебе. Расскажи, как ты? 🌼"

    def get_general_response(self, message):
        """Общий ответ на непонятное сообщение"""
        general_responses = [
            f"Расскажи подробнее, я слушаю 👂",
            f"Как ты к этому относишься?",
            f"Я здесь, чтобы поддержать тебя. Что ты чувствуешь сейчас?",
            f"Хочешь поговорить об этом или сделать упражнение?",
            f"Это важно. Расскажи, что еще ты чувствуешь?",
            f"Спасибо, что делишься. Как я могу помочь тебе сейчас?"
        ]
        return random.choice(general_responses)

    def analyze_sentiment(self, message):
        """Простой анализ тональности сообщения"""
        positive_words = ['хорошо', 'радостно', 'счастье', 'круто', 'отлично', 'прекрасно']
        negative_words = ['плохо', 'грустно', 'тоскливо', 'ужасно', 'больно', 'страшно']

        message_lower = message.lower()

        pos_count = sum(1 for word in positive_words if word in message_lower)
        neg_count = sum(1 for word in negative_words if word in message_lower)

        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'

    def get_personalized_recommendation(self):
        """Получить персонализированную рекомендацию на основе истории"""
        if not self.user_id or not self.db:
            return None

        # Получаем статистику пользователя
        mood_entries = self.db.get_mood_entries(self.user_id, days=7)

        if len(mood_entries) >= 3:
            avg_mood = sum(e['mood_score'] for e in mood_entries) / len(mood_entries)

            if avg_mood < 4:
                return "📉 Я вижу, что настроение в последнее время ниже среднего. Хочешь попробовать упражнение на поднятие настроения?"
            elif avg_mood > 7:
                return "📈 Отличная динамика! Рад, что у тебя хорошее настроение. Продолжай в том же духе!"

        return None


class ChatBotWindow(QWidget):
    """Окно чата с ботом"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.bot = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Устанавливаем общий стиль для окна чата
        self.setStyleSheet("""
                EnhancedChatBotWindow {
                    background-color: #FFFBF6;
                }

                QScrollArea {
                    border: none;
                    background-color: transparent;
                }

                QScrollBar:vertical {
                    border: none;
                    background-color: #F8F2E9;
                    width: 10px;
                    border-radius: 5px;
                }

                QScrollBar::handle:vertical {
                    background-color: #C4B6A6;
                    border-radius: 5px;
                    min-height: 20px;
                }

                QScrollBar::handle:vertical:hover {
                    background-color: #8B7355;
                }

                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    border: none;
                    background: none;
                }
            """)

        # Верхняя панель
        self.create_top_bar(layout)

        # Основная область
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Левая панель - история
        self.create_history_panel(main_layout)

        # Правая панель - чат
        self.create_chat_panel(main_layout)

        layout.addWidget(main_widget)

        # Инициализируем бота при наличии пользователя
        self.init_bot()

    def create_top_bar(self, parent_layout):
        """Создание верхней панели"""
        top_bar = QFrame()
        top_bar.setFixedHeight(70)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #F8F2E9;
                border-bottom: 1px solid #E8DFD8;
            }
        """)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(30, 0, 30, 0)

        # Кнопка назад
        back_btn = QPushButton("← Назад")
        back_btn.setProperty("class", "SecondaryButton")
        back_btn.clicked.connect(
            lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(1)
        )
        top_layout.addWidget(back_btn)

        top_layout.addStretch()

        # Название с аватаркой
        title_frame = QFrame()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(15)

        avatar = QLabel("🤖")
        avatar.setStyleSheet("font-size: 28px;")
        title_layout.addWidget(avatar)

        title = QLabel("Душевный помощник")
        title.setProperty("class", "TitleMedium")
        title_layout.addWidget(title)

        title_layout.addStretch()
        top_layout.addWidget(title_frame)

        top_layout.addStretch()

        # Кнопка очистки истории
        clear_btn = QPushButton("🗑️ Очистить")
        clear_btn.setProperty("class", "SecondaryButton")
        clear_btn.clicked.connect(self.clear_chat)
        top_layout.addWidget(clear_btn)

        parent_layout.addWidget(top_bar)

    def create_history_panel(self, parent_layout):
        """Создание панели истории"""
        history_widget = QFrame()
        history_widget.setFixedWidth(250)
        history_widget.setProperty("class", "WarmCard")

        history_layout = QVBoxLayout(history_widget)
        history_layout.setSpacing(15)

        # Заголовок
        history_title = QLabel("📋 История")
        history_title.setProperty("class", "TitleSmall")
        history_layout.addWidget(history_title)

        # Список прошлых диалогов
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #E8DFD8;
            }
            QListWidget::item:hover {
                background-color: rgba(181, 229, 207, 0.3);
            }
        """)

        # Добавляем примеры
        self.history_list.addItems([
            "Сегодня 10:30 - Тревога",
            "Вчера 22:15 - Грусть",
            "Вчера 14:20 - Усталость",
            "Позавчера - Цитата дня"
        ])

        history_layout.addWidget(self.history_list)

        # Быстрые действия
        quick_actions = QFrame()
        quick_layout = QVBoxLayout(quick_actions)
        quick_layout.setSpacing(10)

        actions_title = QLabel("⚡ Быстрые действия")
        actions_title.setProperty("class", "TextRegular")
        actions_title.setStyleSheet("font-weight: bold;")
        quick_layout.addWidget(actions_title)

        quote_btn = QPushButton("💭 Цитата дня")
        quote_btn.setProperty("class", "SecondaryButton")
        quote_btn.clicked.connect(self.get_quote)
        quick_layout.addWidget(quote_btn)

        exercise_btn = QPushButton("🧘 Случайное упражнение")
        exercise_btn.setProperty("class", "SecondaryButton")
        exercise_btn.clicked.connect(self.get_random_exercise)
        quick_layout.addWidget(exercise_btn)

        mood_btn = QPushButton("📊 Анализ настроения")
        mood_btn.setProperty("class", "SecondaryButton")
        mood_btn.clicked.connect(self.analyze_mood)
        quick_layout.addWidget(mood_btn)

        history_layout.addWidget(quick_actions)
        history_layout.addStretch()

        parent_layout.addWidget(history_widget)

    def create_chat_panel(self, parent_layout):
        """Создание панели чата"""
        chat_widget = QFrame()
        chat_widget.setProperty("class", "Card")

        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setSpacing(15)

        # Область сообщений
        self.messages_area = QScrollArea()
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        messages_container = QWidget()
        self.messages_layout = QVBoxLayout(messages_container)
        self.messages_layout.setSpacing(10)
        self.messages_layout.addStretch()

        self.messages_area.setWidget(messages_container)
        chat_layout.addWidget(self.messages_area)

        # Приветственное сообщение
        self.add_bot_message(
            "Привет! Я твой душевный помощник 🤗\n\n"
            "Я здесь, чтобы:\n"
            "• Выслушать и поддержать\n"
            "• Предложить упражнения КПТ\n"
            "• Дать мотивирующую цитату\n"
            "• Помочь разобраться в чувствах\n\n"
            "Расскажи, как ты сегодня?"
        )

        # Область ввода
        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        input_layout.setSpacing(10)

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Напишите сообщение...")
        self.message_input.setMaximumHeight(80)
        self.message_input.installEventFilter(self)
        input_layout.addWidget(self.message_input)

        send_btn = QPushButton("📤 Отправить")
        send_btn.setProperty("class", "PrimaryButton")
        send_btn.setFixedWidth(120)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        chat_layout.addWidget(input_frame)

        parent_layout.addWidget(chat_widget, 1)  # Растягиваем

    def init_bot(self):
        """Инициализация бота"""
        if self.parent.current_user:
            self.bot = MentalHealthBot(self.parent.db, self.parent.current_user['id'])
        else:
            self.bot = MentalHealthBot(self.parent.db)
            self.add_bot_message(
                "👤 Войдите в систему, чтобы я мог запоминать нашу историю и давать персонализированные советы!")

    def send_message(self):
        """Отправка сообщения"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return

        # Добавляем сообщение пользователя
        self.add_user_message(message)

        # Очищаем поле ввода
        self.message_input.clear()

        # Получаем ответ от бота
        if self.bot:
            response = self.bot.get_response(message)
            self.add_bot_message(response)

            # Проверяем персонализированную рекомендацию
            if self.bot.user_id:
                recommendation = self.bot.get_personalized_recommendation()
                if recommendation:
                    self.add_bot_message(f"💡 *Персональная заметка:* {recommendation}")
        else:
            self.add_bot_message("Извини, я временно недоступен. Попробуй позже!")

    def add_user_message(self, message):
        """Добавление сообщения пользователя с улучшенной видимостью"""
        # Анализируем эмоцию
        sentiment = self.sentiment_analyzer.analyze_sentiment(message)
        dominant = self.sentiment_analyzer.get_dominant_emotion(sentiment)

        # Определяем цвет фона и текста в зависимости от эмоции
        if dominant == 'joy':
            bg_color = "#B5E5CF"  # Мятный
            text_color = "#2C3E50"  # Темно-серый для контраста
            border_color = "#9BD1B8"
        elif dominant == 'sadness':
            bg_color = "#9AD0F5"  # Голубой
            text_color = "#2C3E50"
            border_color = "#7FB4D9"
        elif dominant == 'anger':
            bg_color = "#FFB6B9"  # Светло-красный
            text_color = "#2C3E50"
            border_color = "#E6A3A6"
        elif dominant == 'anxiety':
            bg_color = "#FFD6A5"  # Персиковый
            text_color = "#2C3E50"
            border_color = "#E6C094"
        else:
            bg_color = "#B5E5CF"  # Мятный по умолчанию
            text_color = "#2C3E50"
            border_color = "#9BD1B8"

        # Сохраняем в историю
        self.messages.append({
            'sender': 'user',
            'text': message,
            'time': datetime.now(),
            'sentiment': sentiment
        })

        # Создаем виджет сообщения
        message_widget = QFrame()
        message_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 15px 15px 5px 15px;
                border: 2px solid {border_color};
                max-width: 70%;
                margin: 5px;
            }}
        """)

        layout = QVBoxLayout(message_widget)
        layout.setSpacing(5)
        layout.setContentsMargins(12, 8, 12, 8)

        # Текст сообщения
        text = QLabel(message)
        text.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
                padding: 5px;
            }}
        """)
        text.setWordWrap(True)
        layout.addWidget(text)

        # Время и эмоция
        time_frame = QFrame()
        time_layout = QHBoxLayout(time_frame)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(10)

        # Эмодзи эмоции
        emotion_icons = {
            'joy': '😊',
            'sadness': '😔',
            'anger': '😠',
            'anxiety': '😰'
        }
        emotion_icon = emotion_icons.get(dominant, '😐')

        emotion_label = QLabel(emotion_icon)
        emotion_label.setStyleSheet("font-size: 14px; background-color: transparent;")
        time_layout.addWidget(emotion_label)

        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 11px;
                opacity: 0.7;
                background-color: transparent;
            }}
        """)
        time_layout.addWidget(time_label)

        time_layout.addStretch()
        layout.addWidget(time_frame)

        # Выравниваем справа
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 5, 0, 5)
        container_layout.addStretch()
        container_layout.addWidget(message_widget)

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
        self.scroll_to_bottom()

    def add_bot_message(self, message):
        """Добавление сообщения бота с улучшенной видимостью"""
        # Анализируем эмоцию ответа
        sentiment = self.sentiment_analyzer.analyze_sentiment(message)

        # Сохраняем в историю
        self.messages.append({
            'sender': 'bot',
            'text': message,
            'time': datetime.now(),
            'sentiment': sentiment
        })

        # Создаем виджет сообщения
        message_widget = QFrame()
        message_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;  /* Белый фон */
                border-radius: 15px 15px 15px 5px;
                border: 2px solid #9BD1B8;  /* Мятная рамка */
                max-width: 70%;
                margin: 5px;
            }
        """)

        layout = QVBoxLayout(message_widget)
        layout.setSpacing(5)
        layout.setContentsMargins(12, 8, 12, 8)

        # Обработка markdown-подобного форматирования
        message = message.replace('*', '')
        message = message.replace('**', '')

        # Текст сообщения
        text = QLabel(message)
        text.setStyleSheet("""
            QLabel {
                color: #2C3E50;  /* Темно-серый текст */
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
                padding: 5px;
            }
        """)
        text.setWordWrap(True)
        layout.addWidget(text)

        # Время и индикатор бота
        time_frame = QFrame()
        time_layout = QHBoxLayout(time_frame)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(10)

        # Иконка бота
        bot_icon = QLabel("🤖")
        bot_icon.setStyleSheet("font-size: 14px; background-color: transparent;")
        time_layout.addWidget(bot_icon)

        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setStyleSheet("""
            QLabel {
                color: #7F8C8D;  /* Серый */
                font-size: 11px;
                opacity: 0.7;
                background-color: transparent;
            }
        """)
        time_layout.addWidget(time_label)

        time_layout.addStretch()
        layout.addWidget(time_frame)

        # Выравниваем слева
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 5, 0, 5)
        container_layout.addWidget(message_widget)
        container_layout.addStretch()

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
        self.scroll_to_bottom()

        # Обновляем эмоциональный монитор
        self.update_emotion_monitor(message, is_user=False)

    def get_quote(self):
        """Получить цитату дня"""
        if self.bot:
            self.add_bot_message(self.bot.get_random_quote())

    def get_random_exercise(self):
        """Получить случайное упражнение"""
        if self.bot:
            self.add_bot_message(self.bot.suggest_exercise(""))

    def analyze_mood(self):
        """Анализ настроения"""
        if not self.parent.current_user:
            self.add_bot_message("Войдите в систему, чтобы я мог проанализировать ваше настроение!")
            return

        if self.bot and self.bot.user_id:
            recommendation = self.bot.get_personalized_recommendation()
            if recommendation:
                self.add_bot_message(recommendation)
            else:
                self.add_bot_message("Пока недостаточно данных для анализа. Продолжайте отмечать настроение! 📝")

    def clear_chat(self):
        """Очистка чата"""
        reply = QMessageBox.question(
            self, "Очистка чата",
            "Очистить историю сообщений?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Очищаем все сообщения кроме приветствия
            while self.messages_layout.count() > 1:
                item = self.messages_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self.add_bot_message(
                "Привет! Я твой душевный помощник 🤗\n\n"
                "Расскажи, как ты сегодня?"
            )

    def eventFilter(self, obj, event):
        """Фильтр событий для отправки по Enter"""
        if obj == self.message_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)


class DiaryWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_user = None
        self.init_ui()

    def set_current_user(self, user):
        """Установка текущего пользователя"""
        self.current_user = user

    def init_ui(self):
        """Инициализация окна дневника мыслей"""
        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Верхняя панель
        self.create_top_bar(main_layout)

        # Прокручиваемая область
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Контент внутри прокрутки
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(30)
        content_layout.setContentsMargins(40, 30, 40, 40)

        # Заголовок
        header_label = QLabel("📝 Дневник мыслей")
        header_label.setProperty("class", "TitleLarge")
        content_layout.addWidget(header_label)

        # Информация о методе КПТ
        info_card = self.create_info_card()
        content_layout.addWidget(info_card)

        # Форма записи
        form_card = self.create_diary_form()
        content_layout.addWidget(form_card)

        # Примеры записей
        examples_card = self.create_examples_card()
        content_layout.addWidget(examples_card)

    def create_top_bar(self, parent_layout):
        """Создание верхней панели"""
        top_bar = QFrame()
        top_bar.setFixedHeight(70)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #F8F2E9;
                border-bottom: 1px solid #E8DFD8;
            }
        """)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(30, 0, 30, 0)

        # Кнопка назад
        back_btn = QPushButton("← Назад")
        back_btn.setProperty("class", "SecondaryButton")
        back_btn.clicked.connect(
            lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(1)
        )
        top_layout.addWidget(back_btn)

        top_layout.addStretch()

        # Название
        title = QLabel("Дневник мыслей")
        title.setProperty("class", "TitleMedium")
        top_layout.addWidget(title)

        top_layout.addStretch()

        # Кнопка сохранения
        save_btn = QPushButton("💾 Сохранить")
        save_btn.setProperty("class", "PrimaryButton")
        save_btn.clicked.connect(self.save_entry)
        top_layout.addWidget(save_btn)

        parent_layout.addWidget(top_bar)

    def create_info_card(self):
        """Карточка с информацией о методе КПТ"""
        card = QFrame()
        card.setProperty("class", "WarmCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Заголовок
        title = QLabel("🤔 Что такое автоматические мысли?")
        title.setProperty("class", "TitleSmall")
        layout.addWidget(title)

        # Описание
        description = QLabel(
            "Автоматические мысли — это быстрые, мимолетные мысли, которые возникают "
            "в ответ на события. Они часто бывают искаженными и влияют на наши эмоции и поведение. "
            "В КПТ мы учимся распознавать и анализировать эти мысли."
        )
        description.setProperty("class", "TextRegular")
        description.setWordWrap(True)
        layout.addWidget(description)

        return card

    def create_diary_form(self):
        """Форма для записи мыслей"""
        card = QFrame()
        card.setProperty("class", "Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Ситуация
        situation_label = QLabel("1. Ситуация (что произошло?):")
        situation_label.setProperty("class", "TextRegular")
        situation_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(situation_label)

        self.situation_input = QTextEdit()
        self.situation_input.setPlaceholderText("Опишите ситуацию, которая вызвала эмоциональную реакцию...")
        self.situation_input.setMaximumHeight(100)
        layout.addWidget(self.situation_input)

        # Эмоции
        emotions_label = QLabel("2. Эмоции и их интенсивность (0-100%):")
        emotions_label.setProperty("class", "TextRegular")
        emotions_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(emotions_label)

        # Контейнер для эмоций
        emotions_frame = QFrame()
        emotions_layout = QVBoxLayout(emotions_frame)
        emotions_layout.setSpacing(10)

        emotions = ["Тревога", "Грусть", "Гнев", "Стыд", "Радость"]
        self.emotion_inputs = {}

        for emotion in emotions:
            emotion_frame = QFrame()
            emotion_layout = QHBoxLayout(emotion_frame)
            emotion_layout.setContentsMargins(0, 0, 0, 0)

            # Метка эмоции
            emotion_label = QLabel(f"{emotion}:")
            emotion_label.setProperty("class", "TextRegular")
            emotion_label.setFixedWidth(100)
            emotion_layout.addWidget(emotion_label)

            # Слайдер
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(0)
            slider.setFixedHeight(30)
            slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    height: 8px;
                    background: #E8DFD8;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #B5E5CF;
                    width: 20px;
                    margin: -6px 0;
                    border-radius: 10px;
                }
            """)
            emotion_layout.addWidget(slider)

            # Значение
            value_label = QLabel("0%")
            value_label.setProperty("class", "TextRegular")
            value_label.setFixedWidth(40)
            emotion_layout.addWidget(value_label)

            # Связываем слайдер и метку
            slider.valueChanged.connect(
                lambda value, lbl=value_label: lbl.setText(f"{value}%")
            )

            self.emotion_inputs[emotion] = slider
            emotions_layout.addWidget(emotion_frame)

        layout.addWidget(emotions_frame)

        # Автоматические мысли
        thoughts_label = QLabel("3. Автоматические мысли (что пришло в голову?):")
        thoughts_label.setProperty("class", "TextRegular")
        thoughts_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(thoughts_label)

        self.thoughts_input = QTextEdit()
        self.thoughts_input.setPlaceholderText("Запишите мысли, которые пришли в голову в этой ситуации...")
        self.thoughts_input.setMaximumHeight(100)
        layout.addWidget(self.thoughts_input)

        # Когнитивные искажения
        distortions_label = QLabel("4. Возможные когнитивные искажения:")
        distortions_label.setProperty("class", "TextRegular")
        distortions_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(distortions_label)

        # Чекбоксы искажений
        distortions = [
            ("Черно-белое мышление", "Видеть всё в крайностях, без полутонов"),
            ("Катастрофизация", "Представлять худший сценарий"),
            ("Долженствование", "Использовать слова 'должен', 'обязан'"),
            ("Чтение мыслей", "Думать, что знаете, что думают другие"),
            ("Персонализация", "Принимать всё на свой счёт")
        ]

        self.distortion_checks = {}
        for name, desc in distortions:
            check_frame = QFrame()
            check_layout = QHBoxLayout(check_frame)
            check_layout.setContentsMargins(5, 5, 5, 5)

            checkbox = QCheckBox(name)
            checkbox.setProperty("class", "TextRegular")
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 10px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
                QCheckBox::indicator:checked {
                    background-color: #B5E5CF;
                    border: 2px solid #9BD1B8;
                }
            """)
            check_layout.addWidget(checkbox)

            desc_label = QLabel(desc)
            desc_label.setProperty("class", "TextLight")
            desc_label.setStyleSheet("font-size: 12px;")
            check_layout.addWidget(desc_label)
            check_layout.addStretch()

            self.distortion_checks[name] = checkbox
            layout.addWidget(check_frame)

        # Альтернативная мысль
        alternative_label = QLabel("5. Альтернативная, более сбалансированная мысль:")
        alternative_label.setProperty("class", "TextRegular")
        alternative_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(alternative_label)

        self.alternative_input = QTextEdit()
        self.alternative_input.setPlaceholderText("Попробуйте найти более сбалансированный взгляд на ситуацию...")
        self.alternative_input.setMaximumHeight(100)
        layout.addWidget(self.alternative_input)

        # Переоценка эмоций
        reassessment_label = QLabel("6. Переоценка эмоций (после анализа):")
        reassessment_label.setProperty("class", "TextRegular")
        reassessment_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(reassessment_label)

        self.reassessment_input = QTextEdit()
        self.reassessment_input.setPlaceholderText("Как изменилась интенсивность эмоций после анализа?")
        self.reassessment_input.setMaximumHeight(80)
        layout.addWidget(self.reassessment_input)

        return card

    def create_examples_card(self):
        """Карточка с примерами записей"""
        card = QFrame()
        card.setProperty("class", "MintCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Заголовок
        title = QLabel("📚 Примеры записей:")
        title.setProperty("class", "TitleSmall")
        layout.addWidget(title)

        # Примеры
        examples = [
            {
                "situation": "Коллега не ответил на мое приветствие",
                "emotions": "Тревога (80%), Грусть (60%)",
                "thought": "Он меня ненавидит, я сделал что-то не так",
                "distortion": "Чтение мыслей, Катастрофизация",
                "alternative": "Возможно, он был занят или не заметил меня"
            },
            {
                "situation": "Не получилось выполнить задачу идеально",
                "emotions": "Стыд (90%), Гнев (40%)",
                "thought": "Я неудачник, у меня никогда ничего не получается",
                "distortion": "Черно-белое мышление, Персонализация",
                "alternative": "Это одна задача из многих, я учусь и совершенствуюсь"
            }
        ]

        for i, example in enumerate(examples, 1):
            example_frame = QFrame()
            example_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.5);
                    border-radius: 8px;
                    padding: 15px;
                }
            """)

            example_layout = QVBoxLayout(example_frame)
            example_layout.setSpacing(8)

            # Ситуация
            sit_label = QLabel(f"<b>Ситуация:</b> {example['situation']}")
            sit_label.setProperty("class", "TextRegular")
            sit_label.setTextFormat(Qt.RichText)
            sit_label.setWordWrap(True)
            example_layout.addWidget(sit_label)

            # Эмоции
            emo_label = QLabel(f"<b>Эмоции:</b> {example['emotions']}")
            emo_label.setProperty("class", "TextRegular")
            emo_label.setTextFormat(Qt.RichText)
            example_layout.addWidget(emo_label)

            # Мысли
            th_label = QLabel(f"<b>Мысль:</b> {example['thought']}")
            th_label.setProperty("class", "TextRegular")
            th_label.setTextFormat(Qt.RichText)
            th_label.setWordWrap(True)
            example_layout.addWidget(th_label)

            # Искажения
            dis_label = QLabel(f"<b>Искажения:</b> {example['distortion']}")
            dis_label.setProperty("class", "TextRegular")
            dis_label.setTextFormat(Qt.RichText)
            example_layout.addWidget(dis_label)

            # Альтернатива
            alt_label = QLabel(f"<b>Альтернатива:</b> {example['alternative']}")
            alt_label.setProperty("class", "TextRegular")
            alt_label.setTextFormat(Qt.RichText)
            alt_label.setWordWrap(True)
            example_layout.addWidget(alt_label)

            layout.addWidget(example_frame)

            if i < len(examples):
                # Разделитель между примерами
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setStyleSheet("background-color: rgba(155, 209, 184, 0.5);")
                separator.setFixedHeight(1)
                layout.addWidget(separator)

        return card

    def save_entry(self):
        """Сохранение записи в дневнике"""
        try:
            if not self.current_user:
                QMessageBox.warning(self, "Ошибка", "Вы не авторизованы. Войдите в систему.")
                return

            situation = self.situation_input.toPlainText().strip()
            thoughts = self.thoughts_input.toPlainText().strip()

            if not situation or not thoughts:
                QMessageBox.warning(self, "Внимание",
                                    "Пожалуйста, заполните обязательные поля: Ситуация и Автоматические мысли.")
                return

            # Собираем данные об эмоциях
            emotions_data = {}
            for emotion, slider in self.emotion_inputs.items():
                emotions_data[emotion] = slider.value()

            # Собираем когнитивные искажения
            distortions = []
            for name, checkbox in self.distortion_checks.items():
                if checkbox.isChecked():
                    distortions.append(name)

            # Получаем альтернативные мысли
            alternative = self.alternative_input.toPlainText().strip()
            reassessment = self.reassessment_input.toPlainText().strip()

            # Сохраняем в БД
            if self.parent.current_user:
                entry_id = self.parent.db.save_diary_entry(
                    user_id=self.parent.current_user['id'],
                    situation=situation,
                    emotions=emotions_data,
                    thoughts=thoughts,
                    distortions=distortions,
                    alternative_thought=alternative if alternative else None,
                    reassessment=reassessment if reassessment else None
                )
                stats = self.parent.db.get_user_stats(self.parent.current_user["id"])
                if stats:
                    new_total = stats["total_entries"] + 1
                    # Затем обновляем
                    self.parent.db.update_user_stats(self.parent.current_user['id'], {'total_entries': new_total})
                else:
                    # Если статистики нет, создаем новую запись
                    self.parent.db.update_user_stats(self.parent.current_user['id'], {'total_entries': 1})

                self.update_streak_days()

                # Проверяем достижения
                new_achievements = self.parent.db.check_achievements(self.parent.current_user['id'])

                # Показываем уведомления о новых достижениях
                if new_achievements:
                    self.show_achievement_notification(new_achievements)

                if entry_id:
                    QMessageBox.information(
                        self,
                        "Сохранено",
                        f"✅ Запись успешно сохранена!\n\n"
                        f"ID записи: #{entry_id}\n"
                        f"Выявлено искажений: {len(distortions)}\n"
                        f"Это важный шаг к осознанности!"
                    )

                    # Очищаем форму
                    self.clear_form()
                    if hasattr(self.parent, 'main_menu'):
                        self.parent.main_menu.update_display()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось сохранить запись")
            else:
                QMessageBox.warning(self, "Ошибка", "Пользователь не авторизован")
        except Exception as e:
            print(f"Ошибка сохранения записи: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения записи: {str(e)}")

    def clear_form(self):
        """Очистка формы"""
        self.situation_input.clear()
        self.thoughts_input.clear()
        self.alternative_input.clear()
        self.reassessment_input.clear()

        # Сбрасываем слайдеры
        for slider in self.emotion_inputs.values():
            slider.setValue(0)

        # Сбрасываем чекбоксы
        for checkbox in self.distortion_checks.values():
            checkbox.setChecked(False)

    def update_streak_days(self):
        """Обновление дней подряд"""
        if not self.parent.current_user:
            return

        user_id = self.parent.current_user['id']
        stats = self.parent.db.get_user_stats(user_id)

        today = datetime.now().strftime('%Y-%m-%d')
        last_date = stats.get('last_activity_date')

        if last_date:
            last_dt = datetime.strptime(last_date, '%Y-%m-%d')
            today_dt = datetime.strptime(today, '%Y-%m-%d')

            if (today_dt - last_dt).days == 1:
                # Подряд
                new_streak = stats['streak_days'] + 1
            elif (today_dt - last_dt).days == 0:
                # Сегодня уже была активность
                new_streak = stats['streak_days']
            else:
                # Разрыв
                new_streak = 1
        else:
            # Первая активность
            new_streak = 1

        # Обновляем
        self.parent.db.update_user_stats(user_id, {
            'streak_days': new_streak,
            'last_activity_date': today
        })

    # Метод для показа уведомлений о достижениях:
    def show_achievement_notification(self, achievements):
        """Показать уведомление о новых достижениях"""
        if not achievements:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("🎉 Новое достижение!")
        dialog.setFixedSize(400, 300)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #FFFBF6;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Анимация конфетти
        confetti_label = QLabel("🎊")
        confetti_label.setStyleSheet("font-size: 48px;")
        confetti_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(confetti_label)

        # Заголовок
        title = QLabel("Поздравляем!")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #5A5A5A;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Достижения
        for ach in achievements:
            ach_frame = QFrame()
            ach_layout = QHBoxLayout(ach_frame)
            ach_layout.setSpacing(15)

            # Иконка
            icon_label = QLabel(ach['icon'])
            icon_label.setStyleSheet("font-size: 24px;")
            ach_layout.addWidget(icon_label)

            # Информация
            info_widget = QWidget()
            info_layout = QVBoxLayout(info_widget)
            info_layout.setSpacing(5)

            name_label = QLabel(ach['name'])
            name_label.setStyleSheet("font-weight: bold; font-size: 16px;")
            info_layout.addWidget(name_label)

            desc_label = QLabel(ach['description'])
            desc_label.setProperty("class", "TextSecondary")
            info_layout.addWidget(desc_label)

            xp_label = QLabel(f"+{ach['xp']} XP")
            xp_label.setStyleSheet("color: #FFD166; font-weight: bold;")
            info_layout.addWidget(xp_label)

            ach_layout.addWidget(info_widget, 1)

            layout.addWidget(ach_frame)

        layout.addStretch()

        # Кнопка
        ok_btn = QPushButton("Отлично!")
        ok_btn.setProperty("class", "PrimaryButton")
        ok_btn.clicked.connect(dialog.close)
        layout.addWidget(ok_btn)

        dialog.exec_()


class ExercisesWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.exercise_library = ExerciseLibrary()
        self.current_category = 'все'
        self.init_ui()

    def init_ui(self):
        """Инициализация окна упражнений"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Верхняя панель
        self.create_top_bar(main_layout)

        # Прокручиваемая область
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #F8F2E9;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #C4B6A6;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #8B7355;
            }
        """)

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(30)
        self.content_layout.setContentsMargins(40, 30, 40, 40)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Заголовок (только один раз!)
        header_label = QLabel("🧘 Упражнения КПТ")
        header_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #2C3E50;
            margin-bottom: 10px;
        """)
        self.content_layout.addWidget(header_label)

        # Категории
        self.create_category_buttons()

        # Статистика (если пользователь авторизован)
        if self.parent.current_user:
            self.create_stats_card()

        # Все упражнения (отображаем сразу)
        self.display_all_exercises()

    def create_top_bar(self, parent_layout):
        """Создание верхней панели"""
        top_bar = QFrame()
        top_bar.setFixedHeight(70)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #F8F2E9;
                border-bottom: 2px solid #E8DFD8;
            }
        """)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(30, 0, 30, 0)

        # Кнопка назад
        back_btn = QPushButton("← Назад")
        back_btn.setProperty("class", "SecondaryButton")
        back_btn.setStyleSheet("""
            QPushButton.SecondaryButton {
                background-color: #FFFFFF;
                color: #2C3E50;
                border: 2px solid #E8DFD8;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton.SecondaryButton:hover {
                background-color: #9BD1B8;
                border-color: #7FB4D9;
            }
        """)
        back_btn.clicked.connect(lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(1))
        top_layout.addWidget(back_btn)

        top_layout.addStretch()

        # Название
        title = QLabel("Упражнения КПТ")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2C3E50;
        """)
        top_layout.addWidget(title)

        top_layout.addStretch()

        # Кнопка случайного упражнения
        random_btn = QPushButton("🎲 Случайное")
        random_btn.setStyleSheet("""
            QPushButton {
                background-color: #9BD1B8;
                color: #2C3E50;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #B5E5CF;
            }
        """)
        random_btn.clicked.connect(self.open_random_exercise)
        top_layout.addWidget(random_btn)

        parent_layout.addWidget(top_bar)

    def create_category_buttons(self):
        """Создание кнопок категорий"""
        category_frame = QFrame()
        category_layout = QHBoxLayout(category_frame)
        category_layout.setSpacing(10)
        category_layout.setContentsMargins(0, 10, 0, 20)

        categories = [
            ("🌬️ Дыхание", "дыхание"),
            ("🧠 Мышление", "мышление"),
            ("💆 Релаксация", "релаксация"),
            ("🧘 Осознанность", "осознанность"),
            ("📚 Все", "все")
        ]

        self.category_buttons = []

        for text, cat in categories:
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(45)

            if cat == "все":
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #9BD1B8;
                        color: #2C3E50;
                        border: 2px solid #7FB4D9;
                        padding: 8px 20px;
                        border-radius: 25px;
                        font-weight: bold;
                        font-size: 14px;
                        min-width: 130px;
                    }
                    QPushButton:hover {
                        background-color: #B5E5CF;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #F8F2E9;
                        color: #2C3E50;
                        border: 2px solid #E8DFD8;
                        padding: 8px 20px;
                        border-radius: 25px;
                        font-weight: bold;
                        font-size: 14px;
                        min-width: 130px;
                    }
                    QPushButton:hover {
                        background-color: #9BD1B8;
                        border-color: #7FB4D9;
                    }
                """)

            btn.clicked.connect(lambda checked, c=cat: self.filter_by_category(c))
            category_layout.addWidget(btn)
            self.category_buttons.append((btn, cat))

        category_layout.addStretch()
        self.content_layout.addWidget(category_frame)

    def create_stats_card(self):
        """Создание карточки статистики упражнений"""
        stats_card = QFrame()
        stats_card.setStyleSheet("""
            QFrame {
                background-color: #F8F2E9;
                border-radius: 16px;
                border: 2px solid #E8DFD8;
                padding: 20px;
            }
        """)

        layout = QHBoxLayout(stats_card)
        layout.setSpacing(40)

        # Получаем статистику
        exercise_stats = self.parent.db.get_exercise_stats(self.parent.current_user['id'])
        total_exercises = sum([stat['count'] for stat in exercise_stats]) if exercise_stats else 0

        # Количество выполненных упражнений
        count_frame = QFrame()
        count_layout = QHBoxLayout(count_frame)
        count_layout.setSpacing(10)

        count_icon = QLabel("✅")
        count_icon.setStyleSheet("font-size: 24px;")
        count_layout.addWidget(count_icon)

        count_value = QLabel(str(total_exercises))
        count_value.setStyleSheet("font-size: 28px; font-weight: bold; color: #2C3E50;")
        count_layout.addWidget(count_value)

        count_label = QLabel("выполнено")
        count_label.setStyleSheet("color: #7F8C8D; font-size: 14px;")
        count_layout.addWidget(count_label)

        count_layout.addStretch()
        layout.addWidget(count_frame)

        # Разные упражнения
        unique_count = len(exercise_stats) if exercise_stats else 0
        unique_frame = QFrame()
        unique_layout = QHBoxLayout(unique_frame)
        unique_layout.setSpacing(10)

        unique_icon = QLabel("🔄")
        unique_icon.setStyleSheet("font-size: 24px;")
        unique_layout.addWidget(unique_icon)

        unique_value = QLabel(str(unique_count))
        unique_value.setStyleSheet("font-size: 28px; font-weight: bold; color: #2C3E50;")
        unique_layout.addWidget(unique_value)

        unique_label = QLabel("разных")
        unique_label.setStyleSheet("color: #7F8C8D; font-size: 14px;")
        unique_layout.addWidget(unique_label)

        unique_layout.addStretch()
        layout.addWidget(unique_frame)

        layout.addStretch()
        self.content_layout.addWidget(stats_card)

    def create_exercise_card(self, exercise):
        """Создание карточки упражнения"""
        card = QFrame()
        card.setCursor(Qt.PointingHandCursor)
        card.setFixedSize(300, 280)

        # Цвета для категорий
        category_colors = {
            'дыхание': '#B5E5CF',
            'мышление': '#FFB6B9',
            'релаксация': '#9AD0F5',
            'осознанность': '#FFD6A5'
        }
        color = category_colors.get(exercise.category, '#E8DFD8')

        card.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border-radius: 16px;
                border-left: 8px solid {color};
                border: 2px solid #E8DFD8;
            }}
            QFrame:hover {{
                background-color: #F8F2E9;
                border-color: {color};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)

        # Название
        title_label = QLabel(exercise.name)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1A2634;
            line-height: 1.5;
            margin-bottom: 5px;
        """)
        layout.addWidget(title_label)

        # Длительность
        duration_label = QLabel(f"⏱️ {exercise.duration} мин")
        duration_label.setStyleSheet("color: #7F8C8D; font-size: 13px; font-weight: 500;")
        layout.addWidget(duration_label)

        # Описание
        desc_label = QLabel(exercise.description)
        desc_label.setWordWrap(True)
        desc_label.setMaximumHeight(60)
        desc_label.setStyleSheet("""
            color: #5A5A5A;
            font-size: 13px;
            line-height: 1.4;
            padding: 5px 0;
        """)
        layout.addWidget(desc_label)

        # Количество шагов
        steps_label = QLabel(f"🔹 {exercise.get_steps_count()} шагов")
        steps_label.setStyleSheet("color: #9BD1B8; font-size: 13px; font-weight: bold;")
        layout.addWidget(steps_label)

        layout.addStretch()

        # Кнопка "Начать"
        start_btn = QPushButton("▶ Начать упражнение")
        start_btn.setFixedHeight(44)
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #9BD1B8;
                color: #1A2634;
                border: 2px solid #7FB4D9;
                border-radius: 22px;
                font-weight: bold;
                font-size: 15px;
                text-align: center;
                padding: 8px 16px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #9BD1B8;
                border-color: #7FB4D9;
            }
        """)
        start_btn.clicked.connect(lambda: self.start_exercise(exercise))
        layout.addWidget(start_btn)

        return card

    def display_all_exercises(self):
        """Отображение всех упражнений по категориям"""
        # Очищаем все, кроме первых 3 элементов (заголовок, кнопки категорий, статистика)
        while self.content_layout.count() > 3:
            item = self.content_layout.takeAt(3)
            if item.widget():
                item.widget().deleteLater()

        # Показываем каждую категорию
        categories_order = ['дыхание', 'мышление', 'релаксация', 'осознанность']
        category_names = {
            'дыхание': '🌬️ Дыхательные практики',
            'мышление': '🧠 Работа с мыслями',
            'релаксация': '💆 Релаксация',
            'осознанность': '🧘 Осознанность'
        }

        for cat in categories_order:
            exercises = self.exercise_library.get_exercises_by_category(cat)
            if exercises:
                self.add_category_section(category_names[cat], exercises)

    def add_category_section(self, title, exercises):
        """Добавить секцию с упражнениями"""
        # Заголовок категории
        section_title = QLabel(title)
        section_title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2C3E50;
            margin-top: 20px;
            margin-bottom: 15px;
        """)
        self.content_layout.addWidget(section_title)

        # Контейнер для карточек
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFixedHeight(300)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:horizontal {
                height: 8px;
                background: #F8F2E9;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #9BD1B8;
                border-radius: 4px;
                min-width: 50px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #7FB4D9;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """)

        scroll_content = QWidget()
        scroll_layout = QHBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        scroll_layout.setContentsMargins(5, 5, 5, 5)

        for exercise in exercises:
            card = self.create_exercise_card(exercise)
            scroll_layout.addWidget(card)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        self.content_layout.addWidget(scroll_area)

    def filter_by_category(self, category):
        """Фильтрация упражнений по категории"""
        self.current_category = category

        # Обновляем стили кнопок
        for btn, cat in self.category_buttons:
            if cat == category:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #9BD1B8;
                        color: #2C3E50;
                        border: 2px solid #7FB4D9;
                        padding: 10px 20px;
                        border-radius: 25px;
                        font-weight: bold;
                        font-size: 14px;
                        min-width: 100px;
                    }
                    QPushButton:hover {
                        background-color: #B5E5CF;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #F8F2E9;
                        color: #2C3E50;
                        border: 2px solid #E8DFD8;
                        padding: 10px 20px;
                        border-radius: 25px;
                        font-weight: bold;
                        font-size: 14px;
                        min-width: 100px;
                    }
                    QPushButton:hover {
                        background-color: #9BD1B8;
                        border-color: #7FB4D9;
                    }
                """)

        # Очищаем все, кроме первых 3 элементов
        while self.content_layout.count() > 3:
            item = self.content_layout.takeAt(3)
            if item.widget():
                item.widget().deleteLater()

        if category == 'все':
            # Показываем все категории
            self.display_all_exercises()
        else:
            # Показываем только выбранную категорию
            category_names = {
                'дыхание': '🌬️ Дыхательные практики',
                'мышление': '🧠 Работа с мыслями',
                'релаксация': '💆 Релаксация',
                'осознанность': '🧘 Осознанность'
            }

            exercises = self.exercise_library.get_exercises_by_category(category)
            if exercises:
                self.add_category_section(category_names[category], exercises)

    def start_exercise(self, exercise):
        """Запуск упражнения"""
        if not self.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему для выполнения упражнений")
            return

        dialog = ExerciseSessionWindow(exercise, self.parent)
        dialog.exec_()

    def open_random_exercise(self):
        """Открыть случайное упражнение"""
        if not self.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему для выполнения упражнений")
            return

        exercise = self.exercise_library.get_random_exercise()
        if exercise:
            self.start_exercise(exercise)


class HistoryWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent  # MentalHealthApp
        self.current_user = None
        self.entries_layout = None
        self.stats_card = None
        self.stats_widgets = {}
        self.init_ui()

    def set_current_user(self, user):
        """Установка текущего пользователя"""
        self.current_user = user
        self.update_display()

    def update_display(self):
        """Обновление отображения истории"""
        try:
            # Используем пользователя из parent (MentalHealthApp)
            if not self.parent or not self.parent.current_user:
                print("DEBUG: Нет пользователя в parent")
                # Показываем сообщение для гостя
                self.show_guest_message()
                return

            user_id = self.parent.current_user['id']
            print(f"DEBUG: Загружаем записи для user_id={user_id}")

            # Очищаем старые записи
            if hasattr(self, 'entries_layout') and self.entries_layout:
                while self.entries_layout.count() > 2:  # Оставляем заголовок и кнопку
                    item = self.entries_layout.takeAt(2)
                    if item and item.widget():
                        item.widget().deleteLater()

            # Загружаем реальные записи
            entries = self.parent.db.get_diary_entries(user_id, limit=20)
            print(f"DEBUG: Загружено {len(entries)} записей")

            # Добавляем реальные записи
            if entries:
                for entry in entries:
                    entry_card = self.create_real_entry_card(entry)
                    if self.entries_layout:
                        # Вставляем перед кнопкой "показать больше"
                        self.entries_layout.insertWidget(self.entries_layout.count() - 1, entry_card)
            else:
                # Показываем сообщение об отсутствии записей
                no_entries = QLabel("📭 У вас пока нет записей в дневнике\n\n"
                                    "Создайте первую запись в разделе «Дневник мыслей»")
                no_entries.setProperty("class", "TextSecondary")
                no_entries.setAlignment(Qt.AlignCenter)
                no_entries.setStyleSheet("""
                    QLabel {
                        padding: 40px;
                        font-size: 16px;
                    }
                """)
                if self.entries_layout:
                    self.entries_layout.insertWidget(1, no_entries)  # После заголовка

            # Обновляем статистику
            print("DEBUG: Вызов update_stats_section()")
            self.update_stats_section()

            print(f"DEBUG: Обновление истории завершено")

        except Exception as e:
            print(f"Ошибка обновления истории: {e}")
            import traceback
            traceback.print_exc()

    def showEvent(self, event):
        """Событие при показе окна"""
        super().showEvent(event)
        self.update_display()

    def update_stats_section(self):
        """Обновление статистики"""
        try:
            print(f"DEBUG: Обновление статистики для пользователя {self.parent.current_user['id']}")

            # Получаем статистику
            user_id = self.parent.current_user['id']
            diary_stats = self.parent.db.get_diary_stats(user_id)
            print(f"DEBUG: diary_stats = {diary_stats}")

            # Получаем статистику настроения
            mood_entries = self.parent.db.get_mood_entries(user_id, days=30)
            print(f"DEBUG: mood_entries count = {len(mood_entries) if mood_entries else 0}")

            # Рассчитываем среднее настроение
            if mood_entries and len(mood_entries) > 0:
                mood_scores = [entry['mood_score'] for entry in mood_entries if entry['mood_score'] > 0]
                avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0
            else:
                avg_mood = 0

            print(f"DEBUG: avg_mood = {avg_mood}")

            # Находим stats_card и обновляем значения
            if not hasattr(self, 'stats_card'):
                print("DEBUG: stats_card не найден")
                return

            stats_layout = self.stats_card.layout()
            if not stats_layout:
                print("DEBUG: Нет layout у stats_card")
                return

            print(f"DEBUG: В stats_card {stats_layout.count()} элементов")

            # Обновляем значения - ищем все QLabel внутри stats_card
            # Это более надежный способ
            all_labels = self.stats_card.findChildren(QLabel)
            print(f"DEBUG: Найдено {len(all_labels)} QLabel в stats_card")

            # Отладочная информация
            for i, label in enumerate(all_labels):
                print(f"  Label {i}: '{label.text()}'")

            # Ищем и обновляем значения статистики
            for label in all_labels:
                text = label.text()

                # Ищем метки значений (не заголовки)
                if text.isdigit() or "/10" in text or "раз" in text or "Нет данных" in text:
                    # Это значение статистики
                    parent_widget = label.parent()
                    if parent_widget:
                        # Ищем заголовок в том же виджете
                        for sibling in parent_widget.findChildren(QLabel):
                            if sibling != label:  # Это не текущий label
                                header = sibling.text()

                                if "Всего записей" in header:
                                    label.setText(str(diary_stats.get('total_entries', 0)))
                                    print(f"DEBUG: Обновлено Всего записей: {diary_stats.get('total_entries', 0)}")

                                elif "Дней с записями" in header:
                                    label.setText(str(diary_stats.get('days_with_entries', 0)))
                                    print(
                                        f"DEBUG: Обновлено Дней с записями: {diary_stats.get('days_with_entries', 0)}")

                                elif "Среднее настроение" in header:
                                    label.setText(f"{avg_mood:.1f}/10")
                                    print(f"DEBUG: Обновлено Среднее настроение: {avg_mood:.1f}/10")

                                elif "Частое искажение" in header:
                                    if 'common_distortions' in diary_stats and diary_stats['common_distortions']:
                                        most_common = max(diary_stats['common_distortions'].items(),
                                                          key=lambda x: x[1],
                                                          default=("Нет данных", 0))
                                        label.setText(f"{most_common[0]} ({most_common[1]} раз)")
                                        print(f"DEBUG: Обновлено Частое искажение: {most_common[0]}")
                                    else:
                                        label.setText("Нет данных")

        except Exception as e:
            print(f"Ошибка обновления статистики: {e}")
            import traceback
            traceback.print_exc()

    def show_guest_message(self):
        """Показать сообщение для гостя"""
        if hasattr(self, 'entries_layout') and self.entries_layout:
            # Очищаем старые записи
            while self.entries_layout.count() > 2:
                item = self.entries_layout.takeAt(2)
                if item.widget():
                    item.widget().deleteLater()

            # Показываем сообщение
            guest_message = QLabel("👤 Войдите в систему, чтобы увидеть историю записей")
            guest_message.setProperty("class", "TextSecondary")
            guest_message.setAlignment(Qt.AlignCenter)
            guest_message.setStyleSheet("""
                QLabel {
                    padding: 40px;
                    font-size: 16px;
                }
            """)
            self.entries_layout.insertWidget(1, guest_message)

    def create_real_entry_card(self, entry):
        """Создание карточки реальной записи"""
        card = QFrame()
        card.setProperty("class", "Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Дата и время
        created_at = datetime.strptime(entry['created_at'], '%Y-%m-%d %H:%M:%S')
        date_str = created_at.strftime("%d.%m.%Y %H:%M")

        date_label = QLabel(f"📅 {date_str}")
        date_label.setProperty("class", "TextLight")
        layout.addWidget(date_label)

        # Ситуация (урезанная)
        situation_short = entry['situation'][:100] + "..." if len(entry['situation']) > 100 else entry['situation']
        situation_label = QLabel(f"<b>Ситуация:</b> {situation_short}")
        situation_label.setProperty("class", "TextRegular")
        situation_label.setTextFormat(Qt.RichText)
        situation_label.setWordWrap(True)
        layout.addWidget(situation_label)

        # Эмоции (первые 3 самые сильные)
        emotions = entry['emotions']
        top_emotions = sorted([(k, v) for k, v in emotions.items() if v > 0],
                              key=lambda x: x[1], reverse=True)[:3]
        if top_emotions:
            emotions_text = ", ".join([f"{e[0]}: {e[1]}%" for e in top_emotions])
            emotions_label = QLabel(f"<b>Эмоции:</b> {emotions_text}")
            emotions_label.setProperty("class", "TextSecondary")
            emotions_label.setTextFormat(Qt.RichText)
            layout.addWidget(emotions_label)

        # Когнитивные искажения
        if entry['distortions']:
            distortions_text = ", ".join(entry['distortions'])
            distortions_label = QLabel(f"<b>Искажения:</b> {distortions_text}")
            distortions_label.setProperty("class", "TextSecondary")
            distortions_label.setTextFormat(Qt.RichText)
            layout.addWidget(distortions_label)

        # Кнопка детального просмотра
        view_btn = QPushButton("👁️ Подробнее")
        view_btn.setProperty("class", "SecondaryButton")
        view_btn.setFixedHeight(35)
        view_btn.clicked.connect(lambda checked, e=entry: self.show_entry_details(e))
        layout.addWidget(view_btn)

        return card

    def show_entry_details(self, entry):
        """Показать детали записи"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Запись от {entry['created_at'][:10]}")
        dialog.setFixedSize(600, 500)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # Прокручиваемая область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)

        # Все поля записи
        fields = [
            ("📅 Дата", entry['created_at']),
            ("🎭 Ситуация", entry['situation']),
            ("💭 Автоматические мысли", entry['thoughts']),
            ("🧠 Альтернативная мысль", entry['alternative_thought'] or "Не указано"),
            ("📊 Переоценка", entry['reassessment'] or "Не указано"),
        ]

        for title, value in fields:
            frame = QFrame()
            frame_layout = QVBoxLayout(frame)
            frame_layout.setSpacing(5)

            title_label = QLabel(f"<b>{title}:</b>")
            title_label.setProperty("class", "TextRegular")
            title_label.setTextFormat(Qt.RichText)
            frame_layout.addWidget(title_label)

            value_label = QLabel(value)
            value_label.setProperty("class", "TextRegular")
            value_label.setWordWrap(True)
            value_label.setTextFormat(Qt.PlainText)
            frame_layout.addWidget(value_label)

            content_layout.addWidget(frame)

        # Эмоции в виде таблицы
        if entry['emotions']:
            emotions_frame = QFrame()
            emotions_layout = QVBoxLayout(emotions_frame)
            emotions_layout.setSpacing(5)

            title = QLabel("<b>📈 Эмоции и интенсивность:</b>")
            title.setProperty("class", "TextRegular")
            title.setTextFormat(Qt.RichText)
            emotions_layout.addWidget(title)

            for emotion, value in entry['emotions'].items():
                if value > 0:
                    emotion_row = QFrame()
                    row_layout = QHBoxLayout(emotion_row)

                    label = QLabel(emotion)
                    label.setProperty("class", "TextRegular")
                    row_layout.addWidget(label)

                    row_layout.addStretch()

                    value_label = QLabel(f"{value}%")
                    value_label.setProperty("class", "TextRegular")
                    row_layout.addWidget(value_label)

                    emotions_layout.addWidget(emotion_row)

            content_layout.addWidget(emotions_frame)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setProperty("class", "PrimaryButton")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec_()

    def init_ui(self):
        """Инициализация окна истории"""
        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Верхняя панель
        self.create_top_bar(main_layout)

        # Прокручиваемая область
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Контент внутри прокрутки
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(25)
        content_layout.setContentsMargins(40, 30, 40, 40)

        # Заголовок
        header_label = QLabel("📊 История записей")
        header_label.setProperty("class", "TitleLarge")
        content_layout.addWidget(header_label)

        # Фильтры
        filters_frame = self.create_filters()
        content_layout.addWidget(filters_frame)

        # Статистика (теперь она будет доступна как атрибут)
        stats_frame = self.create_stats()  # Этот метод создает self.stats_card
        content_layout.addWidget(stats_frame)

        # Записи
        entries_frame = self.create_entries()
        content_layout.addWidget(entries_frame)

    def create_top_bar(self, parent_layout):
        """Создание верхней панели"""
        top_bar = QFrame()
        top_bar.setFixedHeight(70)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #F8F2E9;
                border-bottom: 1px solid #E8DFD8;
            }
        """)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(30, 0, 30, 0)

        # Кнопка назад
        back_btn = QPushButton("← Назад")
        back_btn.setProperty("class", "SecondaryButton")
        back_btn.clicked.connect(lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(1))
        top_layout.addWidget(back_btn)

        top_layout.addStretch()

        # Название
        title = QLabel("История записей")
        title.setProperty("class", "TitleMedium")
        top_layout.addWidget(title)

        top_layout.addStretch()

        # Заглушка для выравнивания
        dummy_btn = QPushButton()
        dummy_btn.setFixedSize(back_btn.sizeHint())
        dummy_btn.setVisible(False)
        top_layout.addWidget(dummy_btn)

        parent_layout.addWidget(top_bar)

    def create_filters(self):
        """Создание фильтров"""
        frame = QFrame()
        frame.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout(frame)
        layout.setSpacing(15)

        # Период
        period_label = QLabel("Период:")
        period_label.setProperty("class", "TextRegular")
        layout.addWidget(period_label)

        period_combo = QComboBox()
        period_combo.addItems(["За всё время", "За месяц", "За неделю", "За сегодня"])
        period_combo.setFixedWidth(150)
        layout.addWidget(period_combo)

        layout.addStretch()

        # Кнопка экспорта
        export_btn = QPushButton("📤 Экспорт")
        export_btn.setProperty("class", "SecondaryButton")
        layout.addWidget(export_btn)

        return frame

    def create_stats(self):
        """Создание статистики"""
        self.stats_card = QFrame()
        self.stats_card.setProperty("class", "WarmCard")

        layout = QVBoxLayout(self.stats_card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("📈 Ваша статистика")
        title.setProperty("class", "TitleSmall")
        layout.addWidget(title)

        # Инициализируем словарь для хранения виджетов статистики
        self.stats_widgets = {}

        # Создаем виджеты статистики (3 значения вместо 4)
        stats_data = [
            ("Всего записей", "total_entries", "0"),  # Только 3 значения!
            ("Дней с записями", "days_with_entries", "0"),
            ("Среднее настроение", "avg_mood", "0/10"),
            ("Частое искажение", "common_distortion", "Нет данных"),
        ]

        for label_text, key, default_value in stats_data:  # Распаковываем 3 значения
            stat_frame = QFrame()
            stat_layout = QHBoxLayout(stat_frame)
            stat_layout.setContentsMargins(0, 0, 0, 0)

            # Заголовок
            label_widget = QLabel(label_text)
            label_widget.setProperty("class", "TextRegular")
            label_widget.setFixedWidth(150)
            stat_layout.addWidget(label_widget)

            # Значение
            value_widget = QLabel(default_value)
            value_widget.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #5A5A5A;
            """)
            stat_layout.addWidget(value_widget)

            stat_layout.addStretch()

            # Сохраняем виджет значения
            self.stats_widgets[key] = value_widget
            layout.addWidget(stat_frame)

        return self.stats_card

    def create_entries(self):
        """Создание списка записей"""
        frame = QFrame()
        frame.setStyleSheet("background-color: transparent;")

        self.entries_layout = QVBoxLayout(frame)
        self.entries_layout.setSpacing(15)

        # Заголовок
        title = QLabel("Последние записи")
        title.setProperty("class", "TitleSmall")
        self.entries_layout.addWidget(title)

        # Кнопка показать больше
        more_btn = QPushButton("Показать больше записей")
        more_btn.setProperty("class", "SecondaryButton")
        more_btn.clicked.connect(
            lambda: QMessageBox.information(self, "Информация", "В полной версии здесь будут все ваши записи 📚"))
        self.entries_layout.addWidget(more_btn)

        return frame


class SentimentAnalyzer:
    """Анализатор тональности и эмоций текста"""

    def __init__(self):
        # Словари эмоциональной лексики
        self.positive_words = {
            'хорошо', 'отлично', 'прекрасно', 'замечательно', 'радостно', 'счастлив',
            'круто', 'супер', 'классно', 'великолепно', 'восхитительно', 'превосходно',
            'спокойно', 'уютно', 'комфортно', 'приятно', 'доволен', 'рад', 'счастье',
            'улыбка', 'смех', 'позитив', 'энергия', 'бодрость', 'вдохновение'
        }

        self.negative_words = {
            'плохо', 'ужасно', 'грустно', 'тоскливо', 'одиноко', 'страшно', 'тревожно',
            'больно', 'тяжело', 'невыносимо', 'отчаяние', 'безнадежно', 'беспомощно',
            'злость', 'гнев', 'раздражение', 'обида', 'вина', 'стыд', 'кошмар',
            'депрессия', 'апатия', 'усталость', 'бессилие', 'пустота', 'тоска'
        }

        self.anxiety_words = {
            'тревога', 'страх', 'боюсь', 'паника', 'паническая', 'беспокойство',
            'переживаю', 'волнуюсь', 'напряжение', 'стресс', 'нервы', 'нервничаю',
            'кошмар', 'ужас', 'опасность', 'угроза', 'катастрофа', 'беда'
        }

        self.anger_words = {
            'злость', 'гнев', 'ярость', 'бешенство', 'раздражение', 'ненависть',
            'презираю', 'отвращение', 'возмущение', 'негодование', 'обида', 'злюсь'
        }

        self.sadness_words = {
            'грусть', 'печаль', 'тоска', 'уныние', 'скорбь', 'горе', 'плакать',
            'слезы', 'одиночество', 'безысходность', 'отчаяние', 'депрессия'
        }

        self.joy_words = {
            'радость', 'счастье', 'восторг', 'ликование', 'блаженство', 'эйфория',
            'удовольствие', 'наслаждение', 'веселье', 'смех', 'улыбка'
        }

        # Эмодзи и их эмоциональная окраска
        self.emoji_map = {
            '😊': 'positive', '😄': 'positive', '😁': 'positive', '😂': 'positive',
            '🥰': 'positive', '😍': 'positive', '🤗': 'positive', '😌': 'positive',
            '😔': 'negative', '😢': 'negative', '😭': 'negative', '😞': 'negative',
            '😟': 'negative', '😰': 'negative', '😨': 'negative', '😱': 'negative',
            '😠': 'anger', '😡': 'anger', '🤬': 'anger',
            '😐': 'neutral', '😶': 'neutral', '🤔': 'neutral'
        }

    def analyze_sentiment(self, text):
        """
        Анализ тональности текста
        Возвращает: {'sentiment': 'positive/negative/neutral/mixed',
                     'score': float от -1 до 1,
                     'emotions': {'joy': 0.0, 'sadness': 0.0, 'anger': 0.0, 'anxiety': 0.0},
                     'intensity': float 0-1}
        """
        text_lower = text.lower()

        # Подсчет слов по категориям
        word_count = len(text_lower.split())
        if word_count == 0:
            return {'sentiment': 'neutral', 'score': 0.0, 'emotions': {}, 'intensity': 0.0}

        # Счетчики эмоций
        emotions = {
            'joy': 0,
            'sadness': 0,
            'anger': 0,
            'anxiety': 0
        }

        # Общий счет тональности
        positive_score = 0
        negative_score = 0

        # Анализ слов
        words = text_lower.split()
        for word in words:
            # Удаляем знаки препинания
            word = word.strip('.,!?;:"\'()[]{}')

            if word in self.positive_words:
                positive_score += 1
                if word in self.joy_words:
                    emotions['joy'] += 1
            elif word in self.negative_words:
                negative_score += 1
                if word in self.sadness_words:
                    emotions['sadness'] += 1
                elif word in self.anger_words:
                    emotions['anger'] += 1
                elif word in self.anxiety_words:
                    emotions['anxiety'] += 1

        # Анализ эмодзи
        for char in text:
            if char in self.emoji_map:
                emoji_type = self.emoji_map[char]
                if emoji_type == 'positive':
                    positive_score += 2
                    emotions['joy'] += 1
                elif emoji_type == 'negative':
                    negative_score += 2
                    emotions['sadness'] += 1
                elif emoji_type == 'anger':
                    negative_score += 3
                    emotions['anger'] += 1

        # Учет восклицательных знаков (усиливают эмоциональность)
        exclamation_count = text.count('!')
        question_count = text.count('?')

        if exclamation_count > 0:
            if positive_score > negative_score:
                positive_score += exclamation_count * 0.5
            else:
                negative_score += exclamation_count * 0.5

        # Расчет общего балла (-1 до 1)
        total = positive_score + negative_score
        if total > 0:
            sentiment_score = (positive_score - negative_score) / total
        else:
            sentiment_score = 0.0

        # Определение тональности
        if sentiment_score > 0.3:
            sentiment = 'positive'
        elif sentiment_score < -0.3:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        # Нормализация эмоций
        max_emotion = max(emotions.values()) if emotions.values() else 1
        normalized_emotions = {
            emotion: count / max_emotion if max_emotion > 0 else 0.0
            for emotion, count in emotions.items()
        }

        # Интенсивность (0-1)
        intensity = min(1.0, (positive_score + negative_score) / (word_count + 1) * 2)

        return {
            'sentiment': sentiment,
            'score': round(sentiment_score, 2),
            'emotions': normalized_emotions,
            'intensity': round(intensity, 2)
        }

    def get_dominant_emotion(self, sentiment_data):
        """Получить доминирующую эмоцию"""
        emotions = sentiment_data['emotions']
        if not emotions:
            return None

        dominant = max(emotions.items(), key=lambda x: x[1])
        if dominant[1] > 0.3:  # Порог значимости
            return dominant[0]
        return None


class EmotionalMemory:
    """Эмоциональная память бота - запоминает контекст разговора"""

    def __init__(self, max_history=20):
        self.conversation_history = []
        self.max_history = max_history
        self.user_mood_trend = []
        self.last_emotion = None
        self.emotional_intensity = 0.0

    def add_message(self, message, sentiment_data, is_user=True):
        """Добавить сообщение в историю"""
        self.conversation_history.append({
            'text': message,
            'sentiment': sentiment_data,
            'is_user': is_user,
            'timestamp': datetime.now()
        })

        # Ограничиваем историю
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)

        # Обновляем тренд настроения пользователя
        if is_user:
            self.user_mood_trend.append(sentiment_data['score'])
            if len(self.user_mood_trend) > 10:
                self.user_mood_trend.pop(0)

            self.last_emotion = sentiment_data['sentiment']
            self.emotional_intensity = sentiment_data['intensity']

    def get_mood_trend(self):
        """Получить тренд настроения пользователя"""
        if len(self.user_mood_trend) < 2:
            return 'stable'

        recent = sum(self.user_mood_trend[-3:]) / 3 if len(self.user_mood_trend) >= 3 else self.user_mood_trend[-1]
        previous = sum(self.user_mood_trend[:-3]) / 3 if len(self.user_mood_trend) >= 6 else self.user_mood_trend[0]

        if recent - previous > 0.2:
            return 'improving'
        elif recent - previous < -0.2:
            return 'worsening'
        else:
            return 'stable'

    def get_conversation_context(self):
        """Получить контекст разговора для лучших ответов"""
        if not self.conversation_history:
            return {}

        user_messages = [msg for msg in self.conversation_history if msg['is_user']]
        bot_messages = [msg for msg in self.conversation_history if not msg['is_user']]

        return {
            'user_message_count': len(user_messages),
            'bot_message_count': len(bot_messages),
            'last_user_sentiment': user_messages[-1]['sentiment'] if user_messages else None,
            'mood_trend': self.get_mood_trend(),
            'conversation_length': len(self.conversation_history)
        }


class EnhancedMentalHealthBot(MentalHealthBot):
    """Улучшенный чат-бот с эмоциональным интеллектом"""

    def __init__(self, db, user_id=None):
        super().__init__(db, user_id)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.emotional_memory = EmotionalMemory()
        self.personality = self._initialize_personality()

    def _initialize_personality(self):
        """Инициализация личности бота"""
        return {
            'name': 'Душевный помощник',
            'style': 'эмпатичный',
            'warmth': 0.9,
            'professionalism': 0.7,
            'humor': 0.3
        }

    def get_response(self, message):
        """Получить ответ с учетом эмоционального анализа"""

        # Анализируем тональность сообщения
        sentiment = self.sentiment_analyzer.analyze_sentiment(message)
        dominant_emotion = self.sentiment_analyzer.get_dominant_emotion(sentiment)

        # Сохраняем в память
        self.emotional_memory.add_message(message, sentiment, is_user=True)

        # Проверка на экстренную ситуацию (усиленная)
        if self.is_emergency(message) or sentiment['score'] < -0.7:
            return self.get_emergency_response_with_emotion(sentiment)

        # Получаем контекст
        context = self.emotional_memory.get_conversation_context()

        # Выбираем стратегию ответа в зависимости от эмоции
        response = self._generate_empathetic_response(message, sentiment, dominant_emotion, context)

        # Сохраняем ответ в память
        response_sentiment = self.sentiment_analyzer.analyze_sentiment(response)
        self.emotional_memory.add_message(response, response_sentiment, is_user=False)

        return response

    def _generate_empathetic_response(self, message, sentiment, emotion, context):
        """Генерация эмпатичного ответа с учетом эмоций"""

        message_lower = message.lower()

        # Проверка на приветствие
        if any(word in message_lower for word in ['привет', 'здравствуй', 'хай', 'здарова']):
            return self._get_personalized_greeting(context)

        # Ответ в зависимости от эмоции
        if emotion == 'joy' or sentiment['sentiment'] == 'positive':
            return self._respond_to_joy(message, sentiment, context)
        elif emotion == 'sadness':
            return self._respond_to_sadness(message, sentiment, context)
        elif emotion == 'anger':
            return self._respond_to_anger(message, sentiment, context)
        elif emotion == 'anxiety':
            return self._respond_to_anxiety(message, sentiment, context)
        elif sentiment['sentiment'] == 'negative':
            return self._respond_to_negative(message, sentiment, context)

        # Если эмоция не определена, используем стандартные ответы
        return self._get_general_response_with_context(message, context)

    def _respond_to_joy(self, message, sentiment, context):
        """Ответ на радость"""
        joy_responses = [
            "Как здорово, что ты испытываешь радость! 😊 Расскажи, что тебя так порадовало?",
            "Рад твоему хорошему настроению! Это прекрасно, когда есть повод для радости ✨",
            "Замечательно! Твоя радость заразительна. Что случилось хорошего? 🌟",
            "Улыбка на лице - лучшее украшение! Делись своим счастьем, я слушаю 💫"
        ]

        # Если интенсивность высокая, добавляем эмодзи
        if sentiment['intensity'] > 0.7:
            return random.choice(joy_responses) + " 🎉"

        return random.choice(joy_responses)

    def _respond_to_sadness(self, message, sentiment, context):
        """Ответ на грусть"""

        # Проверяем тренд
        if context['mood_trend'] == 'worsening':
            sadness_responses = [
                "Мне очень жаль, что тебе грустно. Помни, что я рядом и готов поддержать. Что случилось? 💙",
                "Грусть - это нормально. Ты не один. Хочешь поговорить об этом? 🌧️",
                "Я слышу твою грусть. Иногда просто выговориться помогает. Расскажи, что происходит? 🤗"
            ]
        else:
            sadness_responses = [
                "Грустно тебе... Это чувство приходит и уходит. Что могло бы сейчас поднять настроение? 🌈",
                "Обнимаю тебя мысленно. Хочешь, предложу упражнение, которое помогает при грусти? 🫂",
                "Я здесь, чтобы выслушать. Расскажи, что тебя тревожит. 💝"
            ]

        return random.choice(sadness_responses)

    def _respond_to_anger(self, message, sentiment, context):
        """Ответ на гнев"""

        if sentiment['intensity'] > 0.7:
            anger_responses = [
                "Я чувствую твой гнев. Это очень сильная эмоция. Давай сначала сделаем глубокий вдох вместе? 🌬️",
                "Когда злость зашкаливает, важно выпустить пар безопасно. Может, покричать в подушку? 🔥",
                "Твой гнев имеет право быть. За ним часто скрываются другие чувства. Хочешь разобраться? 💢"
            ]
        else:
            anger_responses = [
                "Злость - сигнал, что что-то не так. Что именно вызвало такую реакцию? 🤔",
                "Понимаю твое раздражение. Хочешь поговорить об этом или сделать дыхательное упражнение?",
                "Иногда гнев помогает нам понять свои границы. Что случилось? 🎯"
            ]

        return random.choice(anger_responses)

    def _respond_to_anxiety(self, message, sentiment, context):
        """Ответ на тревогу"""

        anxiety_responses = [
            "Тревога - это очень тяжело. Давай попробуем технику заземления 5-4-3-2-1 прямо сейчас? 🌱",
            "Я слышу твою тревогу. Помни, что это временное состояние. Хочешь подышать вместе? 🌬️",
            "Когда тревога накрывает, важно вернуться в тело. Назови 5 вещей, которые видишь вокруг 👀"
        ]

        return random.choice(anxiety_responses)

    def _respond_to_negative(self, message, sentiment, context):
        """Ответ на негативное сообщение (без конкретной эмоции)"""

        negative_responses = [
            "Мне жаль, что тебе сейчас непросто. Что бы тебе помогло почувствовать себя лучше? 💫",
            "Я здесь, чтобы поддержать. Расскажи, что происходит в твоем мире? 🤗",
            "Твои чувства важны. Спасибо, что делишься. Как я могу помочь тебе сейчас? 🌿"
        ]

        return random.choice(negative_responses)

    def _get_personalized_greeting(self, context):
        """Персонализированное приветствие"""

        if context.get('last_user_sentiment'):
            last_sentiment = context['last_user_sentiment']['sentiment']
            if last_sentiment == 'positive':
                return random.choice([
                    "С возвращением! Рад снова видеть тебя в хорошем настроении! 🌟",
                    "Привет! Как твои дела сегодня? Надеюсь, все отлично! 😊"
                ])
            elif last_sentiment == 'negative':
                return random.choice([
                    "Привет! Как ты сегодня? Я здесь, если захочешь поговорить. 💙",
                    "Здравствуй! Рад тебя видеть. Как твое самочувствие сейчас? 🌷"
                ])

        return random.choice(self.greetings)

    def _get_general_response_with_context(self, message, context):
        """Общий ответ с учетом контекста"""

        # Если разговор длинный, предлагаем сменить тему
        if context['conversation_length'] > 10:
            return "Мы уже немного поговорили. Хочешь, предложу новую тему или упражнение? 🧘"

        # Если настроение падает, предлагаем помощь
        if context['mood_trend'] == 'worsening':
            return "Заметил, что твое настроение ухудшается. Хочешь что-то обсудить или сделать упражнение? 💫"

        return super().get_general_response(message)

    def get_emergency_response_with_emotion(self, sentiment):
        """Экстренный ответ с учетом эмоционального состояния"""

        base_response = """🚨 **Если тебе прямо сейчас очень плохо:**

1. **Позвони на горячую линию**: 8-800-2000-122 (круглосуточно, бесплатно)
2. **Напиши в чат помощи**: https://psyhelp.ru/chat
3. **Сделай заземление**: Назови 5 вещей, которые видишь вокруг
4. **Дыши глубоко**: Вдох на 4, задержка на 4, выдох на 6

Ты не один. Пожалуйста, обратись за помощью. 💝"""

        # Добавляем эмпатичное начало в зависимости от эмоции
        if sentiment['emotions'].get('anger', 0) > 0.5:
            empathy = "Я слышу твой гнев и отчаяние. Это очень тяжело. "
        elif sentiment['emotions'].get('sadness', 0) > 0.5:
            empathy = "Мне так жаль, что тебе так больно и грустно. "
        elif sentiment['emotions'].get('anxiety', 0) > 0.5:
            empathy = "Понимаю, как тебе сейчас страшно и тревожно. "
        else:
            empathy = "Я чувствую, как тебе сейчас тяжело. "

        return empathy + base_response


class EnhancedChatBotWindow(QWidget):
    """Улучшенное окно чата с отображением эмоций"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.bot = None
        self.sentiment_analyzer = SentimentAnalyzer()
        self.messages = []
        self.initialized = False  # Флаг для предотвращения рекурсии
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Устанавливаем общий стиль для окна чата
        self.setStyleSheet("""
            EnhancedChatBotWindow {
                background-color: #FFFBF6;
            }

            QScrollArea {
                border: none;
                background-color: transparent;
            }

            QScrollBar:vertical {
                border: none;
                background-color: #F8F2E9;
                width: 10px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background-color: #C4B6A6;
                border-radius: 5px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #8B7355;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        # Верхняя панель с индикатором настроения
        self.create_top_bar(layout)

        # Основная область
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Левая панель - эмоциональный монитор
        self.create_emotion_panel(main_layout)

        # Правая панель - чат
        self.create_chat_panel(main_layout)

        layout.addWidget(main_widget)

        # Инициализируем бота ПОСЛЕ создания интерфейса
        QTimer.singleShot(100, self.init_bot)

    def create_top_bar(self, parent_layout):
        """Создание верхней панели с улучшенным индикатором настроения"""
        top_bar = QFrame()
        top_bar.setFixedHeight(80)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #F8F2E9;
                border-bottom: 2px solid #E8DFD8;
            }
        """)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(30, 0, 30, 0)

        # Кнопка назад
        back_btn = QPushButton("← Назад")
        back_btn.setProperty("class", "SecondaryButton")
        back_btn.setStyleSheet("""
            QPushButton.SecondaryButton {
                background-color: #FFFFFF;
                color: #2C3E50;
                border: 2px solid #E8DFD8;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton.SecondaryButton:hover {
                background-color: #F0F0F0;
            }
        """)
        back_btn.clicked.connect(
            lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(1)
        )
        top_layout.addWidget(back_btn)

        top_layout.addStretch()

        # Название и аватар
        title_frame = QFrame()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(15)

        avatar = QLabel("🤗")
        avatar.setStyleSheet("font-size: 36px;")
        title_layout.addWidget(avatar)

        title = QLabel("Душевный помощник")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2C3E50;
        """)
        title_layout.addWidget(title)

        top_layout.addWidget(title_frame)

        top_layout.addStretch()

        # Индикатор эмоционального состояния
        mood_frame = QFrame()
        mood_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 30px;
                padding: 8px 15px;
                border: 2px solid #9BD1B8;
            }
        """)
        mood_layout = QHBoxLayout(mood_frame)
        mood_layout.setSpacing(10)
        mood_layout.setContentsMargins(10, 5, 15, 5)

        self.mood_indicator = QLabel("😊")
        self.mood_indicator.setStyleSheet("font-size: 24px;")
        mood_layout.addWidget(self.mood_indicator)

        self.mood_label = QLabel("Хорошее")
        self.mood_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2C3E50;
        """)
        mood_layout.addWidget(self.mood_label)

        top_layout.addWidget(mood_frame)

        parent_layout.addWidget(top_bar)

    def create_emotion_panel(self, parent_layout):
        """Создание панели эмоционального монитора с улучшенной читаемостью"""
        emotion_widget = QFrame()
        emotion_widget.setFixedWidth(280)
        emotion_widget.setProperty("class", "WarmCard")

        emotion_widget.setStyleSheet("""
            QFrame.WarmCard {
                background-color: #FFFFFF;
                border-radius: 15px;
                border: 2px solid #E8DFD8;
                padding: 10px;
            }

            QLabel {
                color: #2C3E50;
                font-size: 13px;
            }

            QLabel.TitleSmall {
                font-size: 16px;
                font-weight: bold;
                color: #2C3E50;
                padding-bottom: 10px;
            }

            QProgressBar {
                border: 1px solid #E8DFD8;
                border-radius: 5px;
                background-color: #F8F2E9;
                height: 12px;
                margin: 2px 0;
            }

            QProgressBar::chunk {
                border-radius: 4px;
            }
        """)

        emotion_layout = QVBoxLayout(emotion_widget)
        emotion_layout.setSpacing(15)
        emotion_layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок с иконкой
        title_frame = QFrame()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title_icon = QLabel("📊")
        title_icon.setStyleSheet("font-size: 20px;")
        title_layout.addWidget(title_icon)

        title = QLabel("Эмоциональный монитор")
        title.setProperty("class", "TitleSmall")
        title_layout.addWidget(title)
        title_layout.addStretch()

        emotion_layout.addWidget(title_frame)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #E8DFD8; max-height: 1px;")
        emotion_layout.addWidget(separator)

        # Текущая эмоция
        current_frame = QFrame()
        current_layout = QHBoxLayout(current_frame)
        current_layout.setContentsMargins(0, 5, 0, 5)

        current_label = QLabel("🎭 Текущая эмоция:")
        current_label.setStyleSheet("font-weight: bold; color: #2C3E50; font-size: 13px;")
        current_layout.addWidget(current_label)

        current_layout.addStretch()

        self.current_emotion_value = QLabel("—")
        self.current_emotion_value.setStyleSheet("""
            font-weight: bold;
            color: #9BD1B8;
            font-size: 14px;
            background-color: #F8F2E9;
            padding: 5px 12px;
            border-radius: 15px;
        """)
        current_layout.addWidget(self.current_emotion_value)

        emotion_layout.addWidget(current_frame)

        # Эмоциональная шкала
        intensity_frame = QFrame()
        intensity_layout = QVBoxLayout(intensity_frame)
        intensity_layout.setSpacing(5)

        intensity_title = QLabel("Интенсивность:")
        intensity_title.setStyleSheet("color: #2C3E50; font-size: 12px; font-weight: 600;")
        intensity_layout.addWidget(intensity_title)

        self.emotion_bar = QProgressBar()
        self.emotion_bar.setRange(0, 100)
        self.emotion_bar.setValue(0)
        self.emotion_bar.setTextVisible(False)
        intensity_layout.addWidget(self.emotion_bar)

        emotion_layout.addWidget(intensity_frame)

        # Радар эмоций
        radar_title = QLabel("Эмоциональный профиль:")
        radar_title.setStyleSheet("color: #2C3E50; font-size: 12px; font-weight: 600; margin-top: 5px;")
        emotion_layout.addWidget(radar_title)

        self.emotion_radar = QFrame()
        radar_layout = QVBoxLayout(self.emotion_radar)
        radar_layout.setSpacing(8)

        emotions = [
            ('😊 Радость', '#06D6A0'),
            ('😔 Грусть', '#118AB2'),
            ('😠 Гнев', '#EF476F'),
            ('😰 Тревога', '#FFB703')
        ]

        self.emotion_bars = {}

        for emotion, color in emotions:
            frame = QFrame()
            frame_layout = QVBoxLayout(frame)
            frame_layout.setSpacing(3)

            # Название эмоции и значение
            header_layout = QHBoxLayout()

            label = QLabel(emotion)
            label.setStyleSheet("color: #2C3E50; font-size: 12px;")
            header_layout.addWidget(label)

            header_layout.addStretch()

            value_label = QLabel("0%")
            value_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
            header_layout.addWidget(value_label)

            frame_layout.addLayout(header_layout)

            # Прогресс-бар
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #E8DFD8;
                    border-radius: 4px;
                    background-color: #F8F2E9;
                    height: 8px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
            frame_layout.addWidget(bar)

            self.emotion_bars[emotion] = (bar, value_label)
            radar_layout.addWidget(frame)

        emotion_layout.addWidget(self.emotion_radar)

        # Разделитель
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setStyleSheet("background-color: #E8DFD8; max-height: 1px; margin: 10px 0;")
        emotion_layout.addWidget(separator2)

        # Статистика диалога
        stats_title = QLabel("📈 Статистика диалога")
        stats_title.setStyleSheet("font-weight: bold; color: #2C3E50; font-size: 13px;")
        emotion_layout.addWidget(stats_title)

        stats_frame = QFrame()
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setSpacing(8)

        # Сообщений
        msg_frame = QHBoxLayout()
        msg_label = QLabel("Сообщений:")
        msg_label.setStyleSheet("color: #2C3E50; font-size: 12px;")
        msg_frame.addWidget(msg_label)
        msg_frame.addStretch()

        self.message_count_label = QLabel("0")
        self.message_count_label.setStyleSheet("font-weight: bold; color: #2C3E50; font-size: 12px;")
        msg_frame.addWidget(self.message_count_label)

        stats_layout.addLayout(msg_frame)

        # Тренд
        trend_frame = QHBoxLayout()
        trend_label = QLabel("Тренд:")
        trend_label.setStyleSheet("color: #2C3E50; font-size: 12px;")
        trend_frame.addWidget(trend_label)
        trend_frame.addStretch()

        self.trend_label = QLabel("—")
        self.trend_label.setStyleSheet("font-weight: bold; color: #2C3E50; font-size: 12px;")
        trend_frame.addWidget(self.trend_label)

        stats_layout.addLayout(trend_frame)

        emotion_layout.addWidget(stats_frame)
        emotion_layout.addStretch()

        parent_layout.addWidget(emotion_widget)

    def create_chat_panel(self, parent_layout):
        """Создание панели чата"""
        chat_widget = QFrame()
        chat_widget.setProperty("class", "Card")

        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setSpacing(15)

        # Область сообщений
        self.messages_area = QScrollArea()
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        messages_container = QWidget()
        self.messages_layout = QVBoxLayout(messages_container)
        self.messages_layout.setSpacing(10)
        self.messages_layout.addStretch()

        self.messages_area.setWidget(messages_container)
        chat_layout.addWidget(self.messages_area)

        # Область ввода
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 25px;
                border: 2px solid #E8DFD8;
                padding: 5px;
            }
            QFrame:focus-within {
                border-color: #9BD1B8;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setSpacing(10)
        input_layout.setContentsMargins(15, 5, 5, 5)

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Напишите сообщение...")
        self.message_input.setMaximumHeight(80)
        self.message_input.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: transparent;
                font-size: 14px;
                color: #2C3E50;
                padding: 8px;
            }
            QTextEdit:focus {
                outline: none;
            }
        """)
        self.message_input.installEventFilter(self)
        input_layout.addWidget(self.message_input)

        send_btn = QPushButton("📤")
        send_btn.setFixedSize(50, 50)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #9BD1B8;
                border: none;
                border-radius: 25px;
                font-size: 20px;
                color: #2C3E50;
            }
            QPushButton:hover {
                background-color: #B5E5CF;
            }
            QPushButton:pressed {
                background-color: #7FB4D9;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        chat_layout.addWidget(input_frame)

        parent_layout.addWidget(chat_widget, 1)

    def init_bot(self):
        """Инициализация улучшенного бота"""
        if self.parent.current_user:
            self.bot = EnhancedMentalHealthBot(self.parent.db, self.parent.current_user['id'])
        else:
            self.bot = EnhancedMentalHealthBot(self.parent.db)

        # Добавляем приветственное сообщение
        welcome_msg = "Привет! Я твой эмоционально-интеллектуальный помощник 🤗\n\nЯ умею:\n• Распознавать твои эмоции\n• Адаптироваться под твое настроение\n• Предлагать упражнения под ситуацию\n• Отслеживать эмоциональный тренд\n\nРасскажи, как ты сегодня?"

        if not self.parent.current_user:
            welcome_msg += "\n\n👤 Войдите в систему, чтобы я мог запоминать нашу историю и давать персонализированные советы!"

        # Добавляем сообщение напрямую, без обновления монитора
        self._add_bot_message_direct(welcome_msg)
        self.initialized = True

    def _add_bot_message_direct(self, message):
        """Добавление сообщения бота без обновления монитора (для инициализации)"""
        # Сохраняем в историю
        self.messages.append({
            'sender': 'bot',
            'text': message,
            'time': datetime.now(),
            'sentiment': {'sentiment': 'neutral', 'score': 0, 'emotions': {}, 'intensity': 0}
        })

        # Создаем контейнер для сообщения
        container = QWidget()
        container.setMaximumWidth(800)  # Ограничиваем максимальную ширину
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(10, 5, 10, 5)

        # Создаем виджет сообщения
        message_widget = QFrame()
        message_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        message_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 18px 18px 18px 5px;
                border: 2px solid #9BD1B8;
            }
        """)

        # Основной layout сообщения
        layout = QVBoxLayout(message_widget)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # Текст сообщения с правильным переносом
        text = QLabel(message)
        text.setWordWrap(True)
        text.setMinimumWidth(200)
        text.setMaximumWidth(500)
        text.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                font-size: 14px;
                font-weight: 500;
                line-height: 1.5;
                background-color: transparent;
            }
        """)
        layout.addWidget(text)

        # Нижняя панель с иконкой и временем
        bottom_frame = QFrame()
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        bot_icon = QLabel("🤖")
        bot_icon.setStyleSheet("font-size: 14px;")
        bottom_layout.addWidget(bot_icon)

        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setStyleSheet("""
            QLabel {
                color: #95A5A6;
                font-size: 11px;
            }
        """)
        bottom_layout.addWidget(time_label)

        bottom_layout.addStretch()
        layout.addWidget(bottom_frame)

        # Добавляем сообщение в контейнер (слева)
        container_layout.addWidget(message_widget)
        container_layout.addStretch()

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
        self.scroll_to_bottom()

    def add_bot_message(self, message):
        """Добавление сообщения бота"""
        if not self.initialized:
            self._add_bot_message_direct(message)
            return

        # Анализируем эмоцию ответа
        sentiment = self.sentiment_analyzer.analyze_sentiment(message)

        # Сохраняем в историю
        self.messages.append({
            'sender': 'bot',
            'text': message,
            'time': datetime.now(),
            'sentiment': sentiment
        })

        # Создаем контейнер для сообщения
        container = QWidget()
        container.setMaximumWidth(800)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(10, 5, 10, 5)

        # Создаем виджет сообщения
        message_widget = QFrame()
        message_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        message_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 18px 18px 18px 5px;
                border: 2px solid #9BD1B8;
            }
        """)

        # Основной layout сообщения
        layout = QVBoxLayout(message_widget)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # Текст сообщения
        text = QLabel(message)
        text.setWordWrap(True)
        text.setMinimumWidth(200)
        text.setMaximumWidth(500)
        text.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                font-size: 14px;
                font-weight: 500;
                line-height: 1.5;
                background-color: transparent;
            }
        """)
        layout.addWidget(text)

        # Нижняя панель
        bottom_frame = QFrame()
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        bot_icon = QLabel("🤖")
        bot_icon.setStyleSheet("font-size: 14px;")
        bottom_layout.addWidget(bot_icon)

        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setStyleSheet("""
            QLabel {
                color: #95A5A6;
                font-size: 11px;
            }
        """)
        bottom_layout.addWidget(time_label)

        bottom_layout.addStretch()
        layout.addWidget(bottom_frame)

        # Добавляем сообщение в контейнер (слева)
        container_layout.addWidget(message_widget)
        container_layout.addStretch()

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
        self.scroll_to_bottom()

    def add_user_message(self, message):
        """Добавление сообщения пользователя"""
        if not self.initialized:
            return

        # Анализируем эмоцию
        sentiment = self.sentiment_analyzer.analyze_sentiment(message)
        dominant = self.sentiment_analyzer.get_dominant_emotion(sentiment)

        # Определяем цвет фона
        if dominant == 'joy':
            bg_color = "#B5E5CF"
            border_color = "#9BD1B8"
        elif dominant == 'sadness':
            bg_color = "#9AD0F5"
            border_color = "#7FB4D9"
        elif dominant == 'anger':
            bg_color = "#FFB6B9"
            border_color = "#E6A3A6"
        elif dominant == 'anxiety':
            bg_color = "#FFD6A5"
            border_color = "#E6C094"
        else:
            bg_color = "#B5E5CF"
            border_color = "#9BD1B8"

        # Сохраняем в историю
        self.messages.append({
            'sender': 'user',
            'text': message,
            'time': datetime.now(),
            'sentiment': sentiment
        })

        # Создаем контейнер для сообщения
        container = QWidget()
        container.setMaximumWidth(800)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(10, 5, 10, 5)

        # Добавляем stretch слева для выравнивания справа
        container_layout.addStretch()

        # Создаем виджет сообщения
        message_widget = QFrame()
        message_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        message_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 18px 18px 5px 18px;
                border: 2px solid {border_color};
            }}
        """)

        # Основной layout сообщения
        layout = QVBoxLayout(message_widget)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # Текст сообщения
        text = QLabel(message)
        text.setWordWrap(True)
        text.setMinimumWidth(200)
        text.setMaximumWidth(500)
        text.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                font-size: 14px;
                font-weight: 500;
                line-height: 1.5;
                background-color: transparent;
            }
        """)
        layout.addWidget(text)

        # Нижняя панель
        bottom_frame = QFrame()
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        # Эмодзи эмоции
        emotion_icons = {
            'joy': '😊',
            'sadness': '😔',
            'anger': '😠',
            'anxiety': '😰'
        }
        emotion_icon = emotion_icons.get(dominant, '😐')

        emotion_label = QLabel(emotion_icon)
        emotion_label.setStyleSheet("font-size: 14px;")
        bottom_layout.addWidget(emotion_label)

        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setStyleSheet("""
            QLabel {
                color: #7F8C8D;
                font-size: 11px;
            }
        """)
        bottom_layout.addWidget(time_label)

        bottom_layout.addStretch()
        layout.addWidget(bottom_frame)

        # Добавляем сообщение в контейнер
        container_layout.addWidget(message_widget)

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
        self.scroll_to_bottom()

        # Обновляем эмоциональный монитор
        self.update_emotion_monitor()

    def send_message(self):
        """Отправка сообщения"""
        if not self.initialized:
            return

        message = self.message_input.toPlainText().strip()
        if not message:
            return

        # Добавляем сообщение пользователя
        self.add_user_message(message)

        # Очищаем поле ввода
        self.message_input.clear()

        # Получаем ответ от бота
        if self.bot:
            # Показываем индикатор печати
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(10, 5, 10, 5)

            typing_label = QLabel("🤖 печатает...")
            typing_label.setStyleSheet("""
                QLabel {
                    color: #95A5A6;
                    font-style: italic;
                    padding: 8px 16px;
                    background-color: #F8F9FA;
                    border-radius: 18px;
                    border: 1px solid #E8DFD8;
                }
            """)

            container_layout.addWidget(typing_label)
            container_layout.addStretch()

            self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
            QApplication.processEvents()

            # Получаем ответ
            response = self.bot.get_response(message)

            # Удаляем индикатор
            typing_label.parent().deleteLater()

            self.add_bot_message(response)

    def update_emotion_monitor(self):
        """Обновление эмоционального монитора"""
        if not self.initialized:
            return

        # Получаем последние сообщения пользователя
        user_messages = [msg for msg in self.messages if msg['sender'] == 'user']
        if not user_messages:
            return

        # Берем последнее сообщение
        last_message = user_messages[-1]
        sentiment = last_message['sentiment']

        # Обновляем текущую эмоцию
        emotions_map = {
            'joy': '😊 Радость',
            'sadness': '😔 Грусть',
            'anger': '😠 Гнев',
            'anxiety': '😰 Тревога'
        }

        dominant = self.sentiment_analyzer.get_dominant_emotion(sentiment)
        if dominant:
            self.current_emotion_value.setText(emotions_map.get(dominant, '—'))
        else:
            self.current_emotion_value.setText(sentiment['sentiment'].capitalize())

        # Обновляем интенсивность
        intensity = int(sentiment['intensity'] * 100)
        self.emotion_bar.setValue(intensity)

        # Обновляем радар эмоций
        emotions = sentiment['emotions']
        for emotion_name, (bar, value_label) in self.emotion_bars.items():
            if 'Радость' in emotion_name:
                value = emotions.get('joy', 0) * 100
            elif 'Грусть' in emotion_name:
                value = emotions.get('sadness', 0) * 100
            elif 'Гнев' in emotion_name:
                value = emotions.get('anger', 0) * 100
            elif 'Тревога' in emotion_name:
                value = emotions.get('anxiety', 0) * 100
            else:
                value = 0

            bar.setValue(int(value))
            value_label.setText(f"{int(value)}%")

        # Обновляем статистику
        user_msg_count = len([msg for msg in self.messages if msg['sender'] == 'user'])
        self.message_count_label.setText(str(user_msg_count))

        # Обновляем тренд
        if len(user_messages) >= 3:
            recent_scores = [msg['sentiment']['score'] for msg in user_messages[-3:]]
            avg_recent = sum(recent_scores) / 3

            if avg_recent > 0.3:
                trend = "↗️ Улучшается"
                self.mood_indicator.setText("😊")
                self.mood_label.setText("Хорошее")
            elif avg_recent < -0.3:
                trend = "↘️ Ухудшается"
                self.mood_indicator.setText("😔")
                self.mood_label.setText("Нужна поддержка")
            else:
                trend = "➡️ Стабильно"
                self.mood_indicator.setText("😐")
                self.mood_label.setText("Нейтральное")

            self.trend_label.setText(trend)

    def scroll_to_bottom(self):
        """Прокрутка вниз"""
        QTimer.singleShot(100, lambda: self.messages_area.verticalScrollBar().setValue(
            self.messages_area.verticalScrollBar().maximum()
        ))

    def eventFilter(self, obj, event):
        """Фильтр событий для отправки по Enter"""
        if obj == self.message_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)


class CBTExercise:
    """Базовый класс для упражнений КПТ"""

    def __init__(self, name, description, category, duration):
        self.name = name
        self.description = description
        self.category = category  # 'дыхание', 'мышление', 'релаксация', 'осознанность'
        self.duration = duration  # в минутах
        self.steps = []
        self.tips = []
        self.completed_count = 0

    def add_step(self, step):
        self.steps.append(step)

    def add_tip(self, tip):
        self.tips.append(tip)

    def get_steps_count(self):
        return len(self.steps)

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'duration': self.duration,
            'steps': self.steps,
            'tips': self.tips
        }


class BreathingExercise(CBTExercise):
    """Упражнения на дыхание"""

    def __init__(self, name, description, duration):
        super().__init__(name, description, 'дыхание', duration)
        self.technique = None
        self.cycles = 5

    def set_technique(self, technique, inhale, hold, exhale):
        self.technique = {
            'name': technique,
            'inhale': inhale,
            'hold': hold,
            'exhale': exhale
        }


class CognitiveExercise(CBTExercise):
    """Когнитивные упражнения"""

    def __init__(self, name, description, duration):
        super().__init__(name, description, 'мышление', duration)
        self.prompts = []

    def add_prompt(self, prompt):
        self.prompts.append(prompt)


class RelaxationExercise(CBTExercise):
    """Упражнения на релаксацию"""

    def __init__(self, name, description, duration):
        super().__init__(name, description, 'релаксация', duration)
        self.background_music = None
        self.visualization = None


class ExerciseLibrary:
    """Библиотека всех упражнений КПТ"""

    def __init__(self):
        self.exercises = []
        self.categories = ['дыхание', 'мышление', 'релаксация', 'осознанность']
        self.init_exercises()

    def init_exercises(self):
        """Инициализация всех упражнений"""

        # 1. ДЫХАТЕЛЬНЫЕ УПРАЖНЕНИЯ
        ex1 = BreathingExercise(
            "🌬 Дыхание 4-7-8",
            "Техника для быстрого успокоения и снижения тревожности",
            5
        )
        ex1.set_technique("4-7-8", 4, 7, 8)
        ex1.add_step("Сядьте удобно, выпрямите спину")
        ex1.add_step("Положите кончик языка за верхние передние зубы")
        ex1.add_step("Выдохните полностью через рот со звуком")
        ex1.add_step("Закройте рот, вдохните через нос на 4 счета")
        ex1.add_step("Задержите дыхание на 7 счетов")
        ex1.add_step("Выдохните через рот на 8 счетов со звуком")
        ex1.add_step("Повторите цикл 4-5 раз")
        ex1.add_tip("Выполняйте упражнение 2 раза в день для лучшего эффекта")
        ex1.add_tip("Не перенапрягайтесь, со временем будет легче")
        self.exercises.append(ex1)

        ex2 = BreathingExercise(
            "🌊 Квадратное дыхание",
            "Техника для фокусировки и снятия стресса",
            5
        )
        ex2.set_technique("Квадрат", 4, 4, 4)
        ex2.add_step("Сядьте прямо, расслабьте плечи")
        ex2.add_step("Медленно вдохните через нос на 4 счета")
        ex2.add_step("Задержите дыхание на 4 счета")
        ex2.add_step("Медленно выдохните через рот на 4 счета")
        ex2.add_step("Задержите дыхание на 4 счета")
        ex2.add_step("Представляйте, как воздух движется по сторонам квадрата")
        ex2.add_step("Повторите 5-10 циклов")
        ex2.add_tip("Можно представлять, как рисуете квадрат в воздухе")
        self.exercises.append(ex2)

        ex3 = BreathingExercise(
            "🫁 Диафрагмальное дыхание",
            "Глубокое дыхание животом для полного расслабления",
            7
        )
        ex3.set_technique("Диафрагма", 5, 0, 5)
        ex3.add_step("Лягте на спину или сядьте удобно")
        ex3.add_step("Положите одну руку на грудь, другую на живот")
        ex3.add_step("Медленно вдохните через нос, направляя воздух в живот")
        ex3.add_step("Почувствуйте, как поднимается рука на животе")
        ex3.add_step("Медленно выдохните через рот, втягивая живот")
        ex3.add_step("Повторите 10 раз, концентрируясь на движении живота")
        ex3.add_tip("Грудь должна оставаться почти неподвижной")
        ex3.add_tip("Делайте выдох длиннее вдоха для большего расслабления")
        self.exercises.append(ex3)

        # 2. КОГНИТИВНЫЕ УПРАЖНЕНИЯ
        ex4 = CognitiveExercise(
            "🧠 Анализ автоматических мыслей",
            "Выявление и оспаривание негативных мыслей",
            15
        )
        ex4.add_step("Запишите ситуацию, которая вызвала дискомфорт")
        ex4.add_step("Определите автоматическую мысль, которая возникла")
        ex4.add_step("Оцените свою уверенность в этой мысли (0-100%)")
        ex4.add_step("Какие эмоции возникли? Оцените их интенсивность")
        ex4.add_step("Найдите доказательства ЗА эту мысль")
        ex4.add_step("Найдите доказательства ПРОТИВ этой мысли")
        ex4.add_step("Сформулируйте более сбалансированную мысль")
        ex4.add_step("Переоцените уверенность в исходной мысли")
        ex4.add_step("Оцените новые эмоции")
        ex4.add_prompt("Ситуация:")
        ex4.add_prompt("Автоматическая мысль:")
        ex4.add_prompt("Эмоции:")
        ex4.add_prompt("Доказательства ЗА:")
        ex4.add_prompt("Доказательства ПРОТИВ:")
        ex4.add_prompt("Альтернативная мысль:")
        ex4.add_tip("Ищите когнитивные искажения: катастрофизация, чтение мыслей, долженствование")
        ex4.add_tip("Спросите себя: 'Что бы я сказал другу в такой ситуации?'")
        self.exercises.append(ex4)

        ex5 = CognitiveExercise(
            "🎯 Техника заземления 5-4-3-2-1",
            "Быстрое возвращение в реальность при тревоге",
            5
        )
        ex5.add_step("Найдите 5 вещей, которые вы видите вокруг")
        ex5.add_step("Назовите их вслух или про себя")
        ex5.add_step("Найдите 4 вещи, которых вы можете коснуться")
        ex5.add_step("Почувствуйте их текстуру, температуру")
        ex5.add_step("Прислушайтесь к 3 звукам вокруг вас")
        ex5.add_step("Определите 2 запаха, которые чувствуете")
        ex5.add_step("Найдите 1 вкус, который ощущаете сейчас")
        ex5.add_step("Сделайте глубокий вдох")
        ex5.add_tip("Это упражнение особенно эффективно при панических атаках")
        ex5.add_tip("Можно выполнять с закрытыми глазами")
        self.exercises.append(ex5)

        ex6 = CognitiveExercise(
            "📝 Дневник благодарности",
            "Развитие позитивного мышления через благодарность",
            10
        )
        ex6.add_step("Запишите 3 вещи, за которые вы благодарны сегодня")
        ex6.add_step("Они могут быть очень простыми (вкусный чай, солнце, улыбка)")
        ex6.add_step("Для каждой вещи запишите, почему она важна")
        ex6.add_step("Почувствуйте благодарность в теле")
        ex6.add_step("Подумайте о человеке, которому вы благодарны")
        ex6.add_step("Если есть возможность, скажите им спасибо")
        ex6.add_tip("Ведите дневник ежедневно, это меняет мышление")
        ex6.add_tip("В трудные дни ищите даже маленькие поводы для благодарности")
        self.exercises.append(ex6)

        # 3. РЕЛАКСАЦИЯ
        ex7 = RelaxationExercise(
            "💆 Прогрессивная мышечная релаксация",
            "Постепенное напряжение и расслабление всех групп мышц",
            15
        )
        ex7.add_step("Сядьте или лягте удобно, закройте глаза")
        ex7.add_step("Сделайте несколько глубоких вдохов")
        ex7.add_step("Напрягите мышцы лица на 5 секунд... расслабьте")
        ex7.add_step("Поднимите плечи к ушам на 5 секунд... расслабьте")
        ex7.add_step("Сожмите кулаки на 5 секунд... расслабьте")
        ex7.add_step("Напрягите мышцы рук на 5 секунд... расслабьте")
        ex7.add_step("Напрягите мышцы спины на 5 секунд... расслабьте")
        ex7.add_step("Втяните живот на 5 секунд... расслабьте")
        ex7.add_step("Напрягите ягодицы на 5 секунд... расслабьте")
        ex7.add_step("Напрягите ноги на 5 секунд... расслабьте")
        ex7.add_step("Почувствуйте полное расслабление во всем теле")
        ex7.add_tip("Концентрируйтесь на разнице между напряжением и расслаблением")
        ex7.add_tip("Дышите глубоко во время упражнения")
        self.exercises.append(ex7)

        ex8 = RelaxationExercise(
            "🌈 Визуализация безопасного места",
            "Создание ментального убежища для отдыха",
            10
        )
        ex8.add_step("Сядьте удобно, закройте глаза")
        ex8.add_step("Сделайте несколько глубоких вдохов")
        ex8.add_step("Представьте место, где вы чувствуете себя в полной безопасности")
        ex8.add_step("Это может быть реальное или воображаемое место")
        ex8.add_step("Рассмотрите детали: цвета, формы, освещение")
        ex8.add_step("Какие звуки вы слышите в этом месте?")
        ex8.add_step("Какие запахи вы чувствуете?")
        ex8.add_step("Почувствуйте температуру воздуха")
        ex8.add_step("Прикоснитесь к предметам вокруг")
        ex8.add_step("Побудьте в этом месте несколько минут")
        ex8.add_step("Медленно вернитесь в реальность")
        ex8.add_tip("Это место всегда с вами, вы можете вернуться в любой момент")
        ex8.add_tip("С каждым разом визуализация будет становиться ярче")
        self.exercises.append(ex8)

        ex9 = RelaxationExercise(
            "☯️ Сканирование тела",
            "Осознанное внимание к каждой части тела",
            10
        )
        ex9.add_step("Лягте на спину, закройте глаза")
        ex9.add_step("Сделайте несколько глубоких вдохов")
        ex9.add_step("Направьте внимание на пальцы ног")
        ex9.add_step("Почувствуйте их, расслабьте")
        ex9.add_step("Медленно поднимайтесь вверх: стопы, голени, колени")
        ex9.add_step("Бедра, таз, живот, грудь")
        ex9.add_step("Пальцы рук, кисти, предплечья, плечи")
        ex9.add_step("Шея, лицо, голова")
        ex9.add_step("Почувствуйте расслабление во всем теле")
        ex9.add_step("Оставайтесь в этом состоянии несколько минут")
        ex9.add_tip("Не пытайтесь ничего изменить, просто наблюдайте")
        ex9.add_tip("Если отвлеклись, мягко верните внимание")
        self.exercises.append(ex9)

        # 4. ОСОЗНАННОСТЬ
        ex10 = CognitiveExercise(
            "🍵 Осознанное чаепитие",
            "Практика присутствия в моменте через обычное действие",
            7
        )
        ex10.add_step("Приготовьте чашку чая")
        ex10.add_step("Рассмотрите чашку: цвет, форму, текстуру")
        ex10.add_step("Почувствуйте тепло чашки в руках")
        ex10.add_step("Вдохните аромат чая, отметьте ноты")
        ex10.add_step("Сделайте маленький глоток")
        ex10.add_step("Почувствуйте вкус, температуру, текстуру")
        ex10.add_step("Проследите, как тепло распространяется по телу")
        ex10.add_step("Повторите, полностью присутствуя в моменте")
        ex10.add_tip("Можно делать с любой едой или напитком")
        ex10.add_tip("Замечайте, когда мысли уходят в прошлое или будущее")
        self.exercises.append(ex10)

        ex11 = CognitiveExercise(
            "🚶 Осознанная ходьба",
            "Медитация в движении",
            10
        )
        ex11.add_step("Встаньте, почувствуйте стопы на полу")
        ex11.add_step("Начните медленно идти")
        ex11.add_step("Почувствуйте, как стопа касается пола")
        ex11.add_step("Ощутите движение в ногах")
        ex11.add_step("Заметьте, как движутся руки")
        ex11.add_step("Почувствуйте дыхание во время ходьбы")
        ex11.add_step("Обратите внимание на окружающее: свет, цвета, звуки")
        ex11.add_step("Продолжайте 5-10 минут")
        ex11.add_tip("Можно ходить по комнате или на улице")
        ex11.add_tip("Не пытайтесь никуда успеть, просто идите")
        self.exercises.append(ex11)

    def get_exercises_by_category(self, category):
        """Получить упражнения по категории"""
        return [ex for ex in self.exercises if ex.category == category]

    def get_exercise_by_name(self, name):
        """Получить упражнение по названию"""
        for ex in self.exercises:
            if ex.name == name:
                return ex
        return None

    def get_random_exercise(self, category=None):
        """Получить случайное упражнение"""
        if category:
            exercises = self.get_exercises_by_category(category)
        else:
            exercises = self.exercises

        if exercises:
            return random.choice(exercises)
        return None



class DeepLearningAnalyzer:
    """Нейросетевой анализ эмоций и предсказание кризисов"""

    def __init__(self, db):
        self.db = db
        self.model = None
        self.tokenizer = Tokenizer(num_words=5000, oov_token='<OOV>')
        self.max_length = 100
        self.model_path = "emotion_model.h5"
        self.tokenizer_path = "tokenizer.pickle"

        # Категории эмоций для классификации
        self.emotion_categories = ['тревога', 'грусть', 'гнев', 'радость', 'спокойствие', 'кризис']

        # Загружаем или создаем модель
        self.load_or_create_model()

    def load_or_create_model(self):
        """Загрузка существующей модели или создание новой"""
        if os.path.exists(self.model_path) and os.path.exists(self.tokenizer_path):
            try:
                self.model = tf.keras.models.load_model(self.model_path)
                with open(self.tokenizer_path, 'rb') as handle:
                    self.tokenizer = pickle.load(handle)
                print("✅ Модель загружена")
            except Exception as e:
                print(f"❌ Ошибка загрузки модели: {e}")
                self.create_model()
        else:
            self.create_model()

    def create_model(self):
        """Создание архитектуры нейросети"""
        self.model = Sequential([
            Embedding(5000, 128, input_length=self.max_length),
            Bidirectional(LSTM(64, return_sequences=True)),
            Dropout(0.3),
            Bidirectional(LSTM(32)),
            Dropout(0.3),
            Dense(16, activation='relu'),
            Dense(len(self.emotion_categories), activation='softmax')
        ])

        self.model.compile(
            loss='categorical_crossentropy',
            optimizer='adam',
            metrics=['accuracy']
        )

        print("✅ Новая модель создана")

    def prepare_texts(self, texts):
        """Подготовка текстов для нейросети"""
        sequences = self.tokenizer.texts_to_sequences(texts)
        padded = pad_sequences(sequences, maxlen=self.max_length, padding='post', truncating='post')
        return padded

    def train_on_user_data(self, user_id):
        """Обучение модели на данных пользователя"""
        try:
            # Получаем записи пользователя
            entries = self.db.get_diary_entries(user_id, limit=200)

            if len(entries) < 20:
                return False, "Недостаточно данных для обучения нейросети (нужно минимум 20 записей)"

            # Подготовка данных
            texts = []
            labels = []

            for entry in entries:
                text = entry['situation'] + ' ' + entry['thoughts']
                texts.append(text)

                # Определяем метку на основе эмоций
                emotions = entry['emotions']
                if emotions:
                    # Находим доминирующую эмоцию
                    main_emotion = max(emotions.items(), key=lambda x: x[1])[0].lower()

                    # Проверяем на кризисные признаки
                    if self._is_crisis_entry(entry):
                        labels.append('кризис')
                    elif main_emotion in ['тревога', 'страх']:
                        labels.append('тревога')
                    elif main_emotion in ['грусть', 'печаль']:
                        labels.append('грусть')
                    elif main_emotion in ['гнев', 'злость']:
                        labels.append('гнев')
                    elif main_emotion in ['радость', 'счастье']:
                        labels.append('радость')
                    else:
                        labels.append('спокойствие')
                else:
                    labels.append('спокойствие')

            # Токенизация
            self.tokenizer.fit_on_texts(texts)

            # Подготовка данных
            X = self.prepare_texts(texts)
            y = tf.keras.utils.to_categorical([self.emotion_categories.index(l) for l in labels],
                                              num_classes=len(self.emotion_categories))

            # Обучение
            history = self.model.fit(
                X, y,
                epochs=10,
                batch_size=8,
                validation_split=0.2,
                verbose=0
            )

            # Сохраняем модель
            self.model.save(self.model_path)
            with open(self.tokenizer_path, 'wb') as handle:
                pickle.dump(self.tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

            accuracy = history.history['accuracy'][-1]
            return True, f"Нейросеть обучена на {len(entries)} записях. Точность: {accuracy:.2f}"

        except Exception as e:
            return False, f"Ошибка обучения нейросети: {str(e)}"

    def _is_crisis_entry(self, entry):
        """Проверка на кризисные признаки"""
        crisis_keywords = ['безнадежно', 'беспомощно', 'невыносимо', 'больше не могу',
                           'не хочу жить', 'плохая мысль', 'самоубийство']

        text = (entry['situation'] + ' ' + entry['thoughts']).lower()

        for keyword in crisis_keywords:
            if keyword in text:
                return True

        # Проверяем интенсивность эмоций
        if entry['emotions']:
            for emotion, intensity in entry['emotions'].items():
                if emotion in ['грусть', 'тревога'] and intensity > 85:
                    return True

        return False

    def analyze_text(self, text):
        """Анализ текста нейросетью"""
        try:
            if self.model is None:
                return {'error': 'Модель не обучена'}

            prepared = self.prepare_texts([text])
            predictions = self.model.predict(prepared, verbose=0)[0]

            # Получаем результаты
            results = {}
            for i, emotion in enumerate(self.emotion_categories):
                results[emotion] = float(predictions[i])

            # Определяем основную эмоцию
            main_emotion_index = np.argmax(predictions)
            main_emotion = self.emotion_categories[main_emotion_index]
            confidence = predictions[main_emotion_index]

            return {
                'main_emotion': main_emotion,
                'confidence': float(confidence),
                'all_emotions': results,
                'is_crisis': main_emotion == 'кризис' and confidence > 0.6
            }

        except Exception as e:
            return {'error': str(e)}

    def predict_crisis_risk(self, user_id, days=7):
        """Предсказание риска кризиса на ближайшие дни"""
        try:
            # Получаем последние записи
            entries = self.db.get_diary_entries(user_id, limit=50)

            if len(entries) < 10:
                return {'risk': 'low', 'message': 'Недостаточно данных для прогноза'}

            # Анализируем последние записи
            recent_analyses = []
            for entry in entries[-10:]:
                text = entry['situation'] + ' ' + entry['thoughts']
                analysis = self.analyze_text(text)
                if 'main_emotion' in analysis:
                    recent_analyses.append(analysis)

            # Считаем кризисные и негативные
            crisis_count = sum(1 for a in recent_analyses if a.get('is_crisis', False))
            negative_count = sum(1 for a in recent_analyses
                                 if a.get('main_emotion') in ['грусть', 'тревога', 'гнев'])

            # Определяем риск
            if crisis_count >= 2:
                risk = 'high'
                message = '🔴 Высокий риск кризиса. Рекомендуется обратиться к специалисту.'
            elif negative_count >= 5:
                risk = 'medium'
                message = '🟡 Средний риск. Уделите больше времени заботе о себе.'
            else:
                risk = 'low'
                message = '🟢 Низкий риск. Продолжайте практики самопомощи.'

            # Прогноз на неделю
            trend = 'stable'
            if len(recent_analyses) >= 3:
                last_three = recent_analyses[-3:]
                if all(a.get('main_emotion') in ['радость', 'спокойствие'] for a in last_three):
                    trend = 'improving'
                elif all(a.get('main_emotion') in ['грусть', 'тревога'] for a in last_three):
                    trend = 'worsening'

            return {
                'risk': risk,
                'message': message,
                'trend': trend,
                'crisis_count': crisis_count,
                'negative_count': negative_count,
                'analyzed_entries': len(recent_analyses)
            }

        except Exception as e:
            return {'error': str(e)}



class ExerciseSessionWindow(QDialog):
    """Окно для выполнения упражнения с интерактивным таймером"""

    def __init__(self, exercise, parent=None):
        super().__init__(parent)
        self.exercise = exercise
        self.parent_app = parent
        self.current_step = 0
        self.timer_running = False
        self.seconds_remaining = 0
        self.total_seconds = 0
        self.responses = {}

        self.setWindowTitle(exercise.name)
        self.setFixedSize(600, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFBF6;
                border-radius: 20px;
            }
            QLabel {
                color: #2C3E50;
            }
            QPushButton {
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QTextEdit, QLineEdit {
                border: 2px solid #E8DFD8;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                background-color: white;
            }
            QTextEdit:focus, QLineEdit:focus {
                border-color: #9BD1B8;
            }
        """)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title_frame = QFrame()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)

        # Иконка категории
        category_icons = {
            'дыхание': '🌬️',
            'мышление': '🧠',
            'релаксация': '💆',
            'осознанность': '🧘'
        }
        icon = category_icons.get(self.exercise.category, '🧘')

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 40px;")
        title_layout.addWidget(icon_label)

        title = QLabel(self.exercise.name)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2C3E50;
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()

        layout.addWidget(title_frame)

        # Длительность
        duration_label = QLabel(f"⏱️ Длительность: {self.exercise.duration} минут")
        duration_label.setStyleSheet("color: #7F8C8D; font-size: 14px;")
        layout.addWidget(duration_label)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #E8DFD8; max-height: 1px;")
        layout.addWidget(separator)

        # Карточка прогресса
        self.progress_card = QFrame()
        self.progress_card.setStyleSheet("""
            QFrame {
                background-color: #F8F2E9;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        progress_layout = QHBoxLayout(self.progress_card)

        self.step_counter = QLabel(f"Шаг 1 из {self.exercise.get_steps_count()}")
        self.step_counter.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50;")
        progress_layout.addWidget(self.step_counter)

        progress_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.exercise.get_steps_count())
        self.progress_bar.setValue(1)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 10px;
                border-radius: 5px;
                background-color: #E8DFD8;
            }
            QProgressBar::chunk {
                background-color: #9BD1B8;
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        layout.addWidget(self.progress_card)

        # Основная область для контента
        self.content_area = QScrollArea()
        self.content_area.setWidgetResizable(True)
        self.content_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_area.setStyleSheet("border: none; background-color: transparent;")

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)

        self.content_area.setWidget(self.content_widget)
        layout.addWidget(self.content_area, 1)

        # Панель с кнопками
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(15)

        self.prev_btn = QPushButton("◀ Назад")
        self.prev_btn.setProperty("class", "SecondaryButton")
        self.prev_btn.clicked.connect(self.prev_step)
        self.prev_btn.setEnabled(False)
        button_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Далее ▶")
        self.next_btn.setProperty("class", "PrimaryButton")
        self.next_btn.clicked.connect(self.next_step)
        button_layout.addWidget(self.next_btn)

        self.finish_btn = QPushButton("✅ Завершить")
        self.finish_btn.setProperty("class", "PrimaryButton")
        self.finish_btn.clicked.connect(self.finish_exercise)
        self.finish_btn.setVisible(False)
        button_layout.addWidget(self.finish_btn)

        button_layout.addStretch()

        self.cancel_btn = QPushButton("✕ Закрыть")
        self.cancel_btn.setProperty("class", "SecondaryButton")
        self.cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_btn)

        layout.addWidget(button_frame)

        # Показываем первый шаг
        self.show_step(0)

    def show_step(self, index):
        """Показать шаг упражнения"""
        self.current_step = index

        # Очищаем контент
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Обновляем счетчик
        self.step_counter.setText(f"Шаг {index + 1} из {self.exercise.get_steps_count()}")
        self.progress_bar.setValue(index + 1)

        # Проверяем, последний ли это шаг
        if index == self.exercise.get_steps_count() - 1:
            self.next_btn.setVisible(False)
            self.finish_btn.setVisible(True)
        else:
            self.next_btn.setVisible(True)
            self.finish_btn.setVisible(False)

        # Обновляем кнопку назад
        self.prev_btn.setEnabled(index > 0)

        # Показываем соответствующий контент
        step_text = self.exercise.steps[index]

        # Заголовок шага
        step_title = QLabel(f"Шаг {index + 1}")
        step_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2C3E50;
            padding: 10px 0;
        """)
        self.content_layout.addWidget(step_title)

        # Текст шага
        text_label = QLabel(step_text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("""
            font-size: 16px;
            line-height: 1.6;
            color: #2C3E50;
            padding: 10px;
            background-color: #FFFFFF;
            border-radius: 10px;
            border: 1px solid #E8DFD8;
        """)
        self.content_layout.addWidget(text_label)

        # Для дыхательных упражнений добавляем таймер
        if isinstance(self.exercise, BreathingExercise) and self.exercise.technique:
            self.add_breathing_timer()

        # Для когнитивных упражнений добавляем поля ввода
        if isinstance(self.exercise, CognitiveExercise) and hasattr(self.exercise, 'prompts') and index < len(
                self.exercise.prompts):
            self.add_input_field(self.exercise.prompts[index])

        self.content_layout.addStretch()

    def add_breathing_timer(self):
        """Добавить таймер для дыхательного упражнения"""
        technique = self.exercise.technique

        timer_frame = QFrame()
        timer_frame.setStyleSheet("""
            QFrame {
                background-color: #B5E5CF;
                border-radius: 15px;
                padding: 20px;
                margin-top: 20px;
            }
        """)
        timer_layout = QVBoxLayout(timer_frame)
        timer_layout.setSpacing(15)

        # Название техники
        tech_label = QLabel(f"Техника: {technique['name']}")
        tech_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50;")
        tech_label.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(tech_label)

        # Индикатор фазы дыхания
        self.phase_label = QLabel("Вдох")
        self.phase_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #2C3E50;")
        self.phase_label.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(self.phase_label)

        # Таймер
        self.timer_display = QLabel("0")
        self.timer_display.setStyleSheet("font-size: 48px; font-weight: bold; color: #2C3E50;")
        self.timer_display.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(self.timer_display)

        # Кнопки управления
        control_layout = QHBoxLayout()

        self.start_timer_btn = QPushButton("▶ Начать")
        self.start_timer_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #2C3E50;
                border: 2px solid #2C3E50;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2C3E50;
                color: #FFFFFF;
            }
        """)
        self.start_timer_btn.clicked.connect(self.start_breathing_timer)
        control_layout.addWidget(self.start_timer_btn)

        self.stop_timer_btn = QPushButton("⏸ Пауза")
        self.stop_timer_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB6B9;
                color: #2C3E50;
                border: 2px solid #2C3E50;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6B6B;
                color: #FFFFFF;
            }
        """)
        self.stop_timer_btn.clicked.connect(self.stop_breathing_timer)
        self.stop_timer_btn.setEnabled(False)
        control_layout.addWidget(self.stop_timer_btn)

        timer_layout.addLayout(control_layout)

        # Инструкция
        instr_label = QLabel(
            f"• Вдох: {technique['inhale']} сек\n"
            f"• Задержка: {technique['hold']} сек\n"
            f"• Выдох: {technique['exhale']} сек\n"
            f"• Повторить: {self.exercise.cycles} раз"
        )
        instr_label.setStyleSheet("color: #2C3E50; font-size: 14px;")
        instr_label.setAlignment(Qt.AlignLeft)
        timer_layout.addWidget(instr_label)

        self.content_layout.addWidget(timer_frame)

        # Таймер для дыхания
        self.breath_timer = QTimer()
        self.breath_timer.timeout.connect(self.update_breathing_timer)

        self.current_phase = 'inhale'
        self.phase_seconds = technique['inhale']
        self.cycle_count = 0

    def add_input_field(self, prompt):
        """Добавить поле ввода для когнитивного упражнения"""
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E8DFD8;
                padding: 15px;
                margin-top: 10px;
            }
        """)
        input_layout = QVBoxLayout(input_frame)

        prompt_label = QLabel(prompt)
        prompt_label.setStyleSheet("font-weight: bold; color: #2C3E50; font-size: 14px;")
        input_layout.addWidget(prompt_label)

        # Создаем поле ввода
        if 'оценка' in prompt.lower() or 'процент' in prompt.lower():
            # Слайдер для оценок
            slider_frame = QFrame()
            slider_layout = QHBoxLayout(slider_frame)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(50)
            slider_layout.addWidget(slider)

            value_label = QLabel("50%")
            value_label.setFixedWidth(50)
            slider_layout.addWidget(value_label)

            slider.valueChanged.connect(lambda v, lbl=value_label: lbl.setText(f"{v}%"))
            self.responses[f"step_{self.current_step}"] = slider

            input_layout.addWidget(slider_frame)
        else:
            # Текстовое поле
            text_edit = QTextEdit()
            text_edit.setMaximumHeight(100)
            text_edit.setPlaceholderText("Введите ответ...")
            self.responses[f"step_{self.current_step}"] = text_edit
            input_layout.addWidget(text_edit)

        self.content_layout.addWidget(input_frame)

    def start_breathing_timer(self):
        """Запустить таймер дыхания"""
        self.timer_running = True
        self.start_timer_btn.setEnabled(False)
        self.stop_timer_btn.setEnabled(True)

        self.current_phase = 'inhale'
        self.phase_seconds = self.exercise.technique['inhale']
        self.timer_display.setText(str(self.phase_seconds))
        self.phase_label.setText("Вдох 🌬️")
        self.breath_timer.start(1000)  # Каждую секунду

    def stop_breathing_timer(self):
        """Остановить таймер дыхания"""
        self.timer_running = False
        self.breath_timer.stop()
        self.start_timer_btn.setEnabled(True)
        self.stop_timer_btn.setEnabled(False)
        self.phase_label.setText("Пауза ⏸️")

    def update_breathing_timer(self):
        """Обновление таймера дыхания"""
        self.phase_seconds -= 1
        self.timer_display.setText(str(self.phase_seconds))

        if self.phase_seconds <= 0:
            # Переходим к следующей фазе
            technique = self.exercise.technique

            if self.current_phase == 'inhale':
                self.current_phase = 'hold'
                self.phase_seconds = technique['hold']
                self.phase_label.setText("Задержка 🤐")
            elif self.current_phase == 'hold':
                self.current_phase = 'exhale'
                self.phase_seconds = technique['exhale']
                self.phase_label.setText("Выдох 🌪️")
            elif self.current_phase == 'exhale':
                self.cycle_count += 1
                if self.cycle_count < self.exercise.cycles:
                    self.current_phase = 'inhale'
                    self.phase_seconds = technique['inhale']
                    self.phase_label.setText("Вдох 🌬️")
                else:
                    # Завершаем упражнение
                    self.stop_breathing_timer()
                    self.phase_label.setText("✅ Упражнение завершено!")
                    QMessageBox.information(self, "Отлично!",
                                            f"Вы завершили {self.exercise.cycles} циклов дыхания!")

    def prev_step(self):
        """Переход к предыдущему шагу"""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

    def next_step(self):
        """Переход к следующему шагу"""
        if self.current_step < self.exercise.get_steps_count() - 1:
            self.show_step(self.current_step + 1)

    def finish_exercise(self):
        """Завершение упражнения"""
        # Сохраняем ответы (для когнитивных упражнений)
        if isinstance(self.exercise, CognitiveExercise) and self.responses:
            self.save_responses()

        # Сохраняем в БД
        if self.parent_app and self.parent_app.current_user:
            self.parent_app.db.save_exercise_log(
                user_id=self.parent_app.current_user['id'],
                exercise_name=self.exercise.name,
                duration_minutes=self.exercise.duration,
                notes=f"Выполнено упражнение: {self.exercise.name}"
            )

            # Начисляем XP
            stats = self.parent_app.db.get_user_stats(self.parent_app.current_user['id'])
            if stats:
                xp_reward = self.exercise.duration * 2  # 2 XP за минуту
                new_xp = stats['xp'] + xp_reward
                self.parent_app.db.update_user_stats(
                    self.parent_app.current_user['id'],
                    {'xp': new_xp}
                )

        QMessageBox.information(self, "Поздравляю!",
                                f"✅ Вы успешно выполнили упражнение!\n\n"
                                f"Продолжайте практиковаться для лучших результатов.")

        self.accept()

    def save_responses(self):
        """Сохранить ответы пользователя"""
        responses_text = ""
        for key, widget in self.responses.items():
            if isinstance(widget, QSlider):
                responses_text += f"{key}: {widget.value()}%\n"
            elif isinstance(widget, QTextEdit):
                responses_text += f"{key}: {widget.toPlainText()[:100]}\n"

        # Здесь можно сохранить в отдельную таблицу БД
        print(f"Сохранены ответы: {responses_text}")


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
            # Определяем время суток по дате создания
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

        # Анализ времени суток
        time_of_day = time_patterns.get('time_of_day', {})
        if time_of_day:
            # Находим наиболее активное время
            max_time = max(time_of_day.items(), key=lambda x: x[1])
            if max_time[1] > 0:
                insights.append(f"Чаще всего вы делаете записи {max_time[0]} ({max_time[1]} записей)")

        # Анализ дней недели
        weekday_pattern = time_patterns.get('weekday_pattern', {})
        if weekday_pattern:
            # Находим наиболее активный день
            max_day = max(weekday_pattern.items(), key=lambda x: x[1])
            if max_day[1] > 3:  # Если достаточно записей
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

            # Ищем ключевые слова
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

                        # Анализируем эмоции
                        for emotion, intensity in emotions.items():
                            if intensity > 0:
                                triggers[category]['avg_emotional_intensity'].append(intensity)

                                if emotion not in triggers[category]['common_emotions']:
                                    triggers[category]['common_emotions'][emotion] = 0
                                triggers[category]['common_emotions'][emotion] += 1

        # Рассчитываем среднюю интенсивность
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

        # Находим наиболее частый триггер
        most_common = max(context_triggers.items(), key=lambda x: x[1]['count'])
        if most_common[1]['count'] > 3:
            insights.append(f"Самый частый триггер: {most_common[0]} ({most_common[1]['count']} раз)")

        # Находим самый эмоционально интенсивный триггер
        high_intensity_triggers = [(cat, data) for cat, data in context_triggers.items()
                                   if data.get('avg_intensity', 0) > 50]
        if high_intensity_triggers:
            high_intensity = max(high_intensity_triggers, key=lambda x: x[1]['avg_intensity'])
            insights.append(
                f"Самый эмоциональный триггер: {high_intensity[0]} (интенсивность: {high_intensity[1]['avg_intensity']:.0f}%)")

        # Анализируем основные эмоции для триггеров
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
                # Считаем частоту
                distortions_count[distortion] = distortions_count.get(distortion, 0) + 1

                # Связываем с эмоциями
                if distortion not in distortion_emotions:
                    distortion_emotions[distortion] = {}

                for emotion, intensity in emotions.items():
                    if intensity > 0:
                        if emotion not in distortion_emotions[distortion]:
                            distortion_emotions[distortion][emotion] = []
                        distortion_emotions[distortion][emotion].append(intensity)

        # Подготавливаем результат
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

        # Находим наиболее частое искажение
        most_common = max(distortion_patterns.items(), key=lambda x: x[1]['frequency'])
        if most_common[1]['frequency'] > 2:
            insights.append(
                f"Наиболее частое когнитивное искажение: '{most_common[0]}' ({most_common[1]['frequency']} раз)")

        # Анализируем связанные эмоции
        for distortion, data in list(distortion_patterns.items())[:3]:
            emotions = data.get('associated_emotions', {})
            if emotions:
                # Находим наиболее частую эмоцию для этого искажения
                emotion_counts = {emotion: len(intensities) for emotion, intensities in emotions.items()}
                main_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else None

                if main_emotion:
                    insights.append(f"Искажение '{distortion}' часто связано с эмоцией '{main_emotion}'")

        # Рекомендации
        total_distortions = sum([data['frequency'] for data in distortion_patterns.values()])
        if total_distortions > 10:
            insights.append("Вы хорошо работаете с выявлением когнитивных искажений!")

        return insights

    def _detect_warning_signs(self, mood_entries, diary_entries):
        """Обнаружение предупреждающих знаков"""
        warnings = []

        if len(mood_entries) >= 7:
            # Проверяем снижение настроения
            recent_moods = [entry['mood_score'] for entry in mood_entries[-7:]]
            if np.mean(recent_moods) < 4:
                warnings.append({
                    'type': 'low_mood',
                    'severity': 'medium',
                    'message': 'Среднее настроение за неделю ниже 4/10'
                })

            # Проверяем резкое падение
            if len(mood_entries) >= 2:
                last_mood = mood_entries[-1]['mood_score']
                prev_mood = mood_entries[-2]['mood_score']
                if last_mood - prev_mood < -3:
                    warnings.append({
                        'type': 'sharp_drop',
                        'severity': 'high',
                        'message': 'Резкое падение настроения'
                    })

        # Анализируем негативные записи
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

        # Проверяем частоту записей
        if len(diary_entries) >= 5:
            # Проверяем, были ли записи в последние 7 дней
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


class IntelligenceDashboard(QWidget):
    """Расширенный дашборд интеллектуального анализа"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.predictor = MoodPredictor(parent.db)
        self.trigger_intel = TriggerIntelligence(parent.db)
        self.recommender = IntelligentRecommender(parent.db)
        self.progress_analyzer = ProgressAnalyzer(parent.db)
        self.emotion_classifier = EmotionClassifier()
        self.visualization = EnhancedVisualizationWidget()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Верхняя панель
        self.create_top_bar(layout)

        # Табы для разных видов анализа
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: #F8F2E9;
                padding: 10px 20px;
                margin-right: 5px;
                border-radius: 8px;
                color: #8B7355;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #B5E5CF;
                color: #5A5A5A;
            }
            QTabBar::tab:hover {
                background-color: #E8DFD8;
            }
        """)

        # Создаем ВСЕ 4 вкладки
        self.create_overview_tab()
        self.create_progress_tab()
        self.create_insights_tab()
        self.create_visualization_tab()

        # Подключаем событие смены вкладки
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        layout.addWidget(self.tab_widget)

        # Загружаем данные для первой вкладки
        self.load_intelligence_data()

    def on_tab_changed(self, index):
        """Обработчик смены вкладки"""
        tab_name = self.tab_widget.tabText(index)

        if "Графики" in tab_name:
            # Обновляем вкладку графиков при переключении на нее
            self.update_visualization_tab()
        elif "Обзор" in tab_name and hasattr(self, 'overview_layout'):
            self.update_overview_tab(self.parent.current_user['id'] if self.parent.current_user else None)
        elif "Прогресс" in tab_name and hasattr(self, 'progress_layout'):
            self.update_progress_tab(self.parent.current_user['id'] if self.parent.current_user else None)
        elif "Инсайты" in tab_name and hasattr(self, 'insights_layout'):
            self.update_insights_tab(self.parent.current_user['id'] if self.parent.current_user else None)

    def create_top_bar(self, parent_layout):
        """Создание верхней панели"""
        top_bar = QFrame()
        top_bar.setFixedHeight(70)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #F8F2E9;
                border-bottom: 1px solid #E8DFD8;
            }
        """)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(30, 0, 30, 0)

        # Кнопка назад
        back_btn = QPushButton("← Назад")
        back_btn.setProperty("class", "SecondaryButton")
        back_btn.clicked.connect(
            lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(1)
        )
        top_layout.addWidget(back_btn)

        top_layout.addStretch()

        # Название
        title = QLabel("🤖 Интеллектуальный анализ")
        title.setProperty("class", "TitleMedium")
        top_layout.addWidget(title)

        top_layout.addStretch()

        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.setProperty("class", "SecondaryButton")
        refresh_btn.clicked.connect(self.load_intelligence_data)
        top_layout.addWidget(refresh_btn)

        parent_layout.addWidget(top_bar)

    def create_overview_tab(self):
        """Вкладка с общим обзором"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)
        layout.setContentsMargins(40, 30, 40, 40)

        # Сохраняем layout для обновления
        self.overview_layout = layout

        # Добавим заглушку
        loading_label = QLabel("Загрузка данных...")
        loading_label.setProperty("class", "TextSecondary")
        loading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(loading_label)

        self.tab_widget.addTab(tab, "📊 Обзор")

    def create_progress_tab(self):
        """Вкладка с анализом прогресса"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)
        layout.setContentsMargins(40, 30, 40, 40)

        self.progress_layout = layout

        loading_label = QLabel("Загрузка прогресса...")
        loading_label.setProperty("class", "TextSecondary")
        loading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(loading_label)

        self.tab_widget.addTab(tab, "📈 Прогресс")

    def create_insights_tab(self):
        """Вкладка с инсайтами и рекомендациями"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)
        layout.setContentsMargins(40, 30, 40, 40)

        self.insights_layout = layout

        loading_label = QLabel("Генерация инсайтов...")
        loading_label.setProperty("class", "TextSecondary")
        loading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(loading_label)

        self.tab_widget.addTab(tab, "💡 Инсайты")

    def create_visualization_tab(self):
        """Создание вкладки с визуализацией данных"""
        # Создаем вкладку
        self.visualization_tab = QWidget()
        self.visualization_layout = QVBoxLayout(self.visualization_tab)  # Сохраняем layout
        self.visualization_layout.setSpacing(25)
        self.visualization_layout.setContentsMargins(40, 30, 40, 40)

        # Добавляем вкладку в табвиджет
        self.tab_widget.addTab(self.visualization_tab, "📈 Графики")

    def show_emotion_timeline(self):
        """Показать временную линию эмоций"""
        try:
            if not self.parent.current_user:
                QMessageBox.information(self, "Информация", "Войдите в систему")
                return

            user_id = self.parent.current_user['id']
            entries = self.parent.db.get_diary_entries(user_id, limit=30)

            if entries and len(entries) >= 5:
                # Очищаем предыдущий график
                self.visualization.figure.clear()
                self.visualization.plot_emotion_timeline(entries)
            else:
                QMessageBox.information(self, "Информация",
                                        f"Недостаточно данных для построения графика (нужно минимум 5 записей, у вас {len(entries) if entries else 0})")

                # Показываем заглушку
                self.visualization.figure.clear()
                ax = self.visualization.figure.add_subplot(111)
                ax.text(0.5, 0.5, f'Недостаточно данных\n(записей: {len(entries) if entries else 0}/5)',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=14, color='#8B7355')
                ax.set_axis_off()
                self.visualization.canvas.draw()

        except Exception as e:
            print(f"Ошибка при построении графика эмоций: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось построить график: {str(e)}")

            # Показываем сообщение об ошибке
            self.visualization.figure.clear()
            ax = self.visualization.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Ошибка загрузки графика',
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=14, color='#FF6B6B')
            ax.set_axis_off()
            self.visualization.canvas.draw()

    def show_mood_chart(self):
        """Показать график настроения"""
        try:
            if not self.parent.current_user:
                return

            user_id = self.parent.current_user['id']
            mood_entries = self.parent.db.get_mood_entries(user_id, days=30)

            if not mood_entries or len(mood_entries) < 2:
                # Показываем сообщение о недостатке данных
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'Недостаточно данных о настроении\n(нужно минимум 2 отметки)',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=14, color='#8B7355')
                ax.set_axis_off()
                self.canvas.draw()
                return

            # Очищаем предыдущий график
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            # Подготавливаем данные
            dates = []
            moods = []

            for entry in mood_entries:
                dates.append(entry['date'])
                moods.append(entry['mood_score'])

            # Создаем простой график
            x = range(len(dates))
            ax.plot(x, moods, 'o-', color='#9BD1B8', linewidth=2, markersize=8)

            # Настройки графика
            ax.set_title('Динамика настроения', fontsize=14, pad=15)
            ax.set_xlabel('Дни', fontsize=11)
            ax.set_ylabel('Настроение (1-10)', fontsize=11)
            ax.set_ylim(0, 11)
            ax.grid(True, alpha=0.3)

            # Подписи дат
            if len(dates) <= 10:
                ax.set_xticks(x)
                ax.set_xticklabels(dates, rotation=45, ha='right')
            else:
                # Показываем каждую 3-ю дату
                tick_indices = range(0, len(dates), max(1, len(dates) // 5))
                ax.set_xticks([x[i] for i in tick_indices])
                ax.set_xticklabels([dates[i] for i in tick_indices], rotation=45, ha='right')

            # Расчет среднего
            avg_mood = sum(moods) / len(moods)
            ax.axhline(y=avg_mood, color='#FFB38E', linestyle='--', alpha=0.7,
                       label=f'Среднее: {avg_mood:.1f}')
            ax.legend()

            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            print(f"Ошибка построения графика настроения: {e}")
            self.show_chart_error(f"Ошибка: {str(e)[:50]}")

    def show_entries_chart(self):
        """Показать график активности записей"""
        try:
            if not self.parent.current_user:
                return

            user_id = self.parent.current_user['id']
            diary_entries = self.parent.db.get_diary_entries(user_id, limit=50)

            if not diary_entries:
                self.show_chart_error("Нет данных о записях")
                return

            # Очищаем предыдущий график
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            # Группируем записи по датам
            entries_by_date = {}
            for entry in diary_entries:
                date_str = entry['created_at'].split()[0]  # Берем только дату

                if date_str not in entries_by_date:
                    entries_by_date[date_str] = 0
                entries_by_date[date_str] += 1

            # Сортируем даты
            dates = sorted(entries_by_date.keys())
            counts = [entries_by_date[date] for date in dates]

            # Создаем столбчатую диаграмму
            x = range(len(dates))
            bars = ax.bar(x, counts, color='#B5E5CF', alpha=0.7)

            # Настройки
            ax.set_title('Активность ведения дневника', fontsize=14, pad=15)
            ax.set_xlabel('Дата', fontsize=11)
            ax.set_ylabel('Количество записей', fontsize=11)

            # Подписи дат (упрощенные)
            if len(dates) <= 10:
                ax.set_xticks(x)
                ax.set_xticklabels(dates, rotation=45, ha='right')
            else:
                # Показываем только некоторые даты
                tick_indices = range(0, len(dates), max(1, len(dates) // 5))
                ax.set_xticks([x[i] for i in tick_indices])
                ax.set_xticklabels([dates[i] for i in tick_indices], rotation=45, ha='right')

            # Добавляем значения над столбцами
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                        f'{count}', ha='center', va='bottom', fontsize=9)

            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            print(f"Ошибка построения графика записей: {e}")
            self.show_chart_error(f"Ошибка: {str(e)[:50]}")

    def show_chart_error(self, message):
        """Показать сообщение об ошибке на графике"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, message,
                ha='center', va='center', transform=ax.transAxes,
                fontsize=12, color='#FF6B6B')
        ax.set_axis_off()
        self.canvas.draw()

    def load_intelligence_data(self):
        """Загрузка и отображение интеллектуального анализа"""
        if not self.parent.current_user:
            self.show_no_data_message("Войдите в систему для доступа к анализу")
            return

        user_id = self.parent.current_user['id']

        # Обновляем все вкладки
        self.update_overview_tab(user_id)
        self.update_progress_tab(user_id)
        self.update_insights_tab(user_id)

    def update_visualization_tab(self):
        """Обновление вкладки с визуализацией (вызывается при переключении на вкладку)"""
        # Очищаем старый контент
        while self.visualization_layout.count():
            item = self.visualization_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Заголовок
        title = QLabel("📊 Визуализация данных")
        title.setProperty("class", "TitleMedium")
        self.visualization_layout.addWidget(title)

        # Проверяем авторизацию сейчас
        if not self.parent or not self.parent.current_user:
            auth_label = QLabel("👤 Войдите в систему для просмотра графиков")
            auth_label.setProperty("class", "TextSecondary")
            auth_label.setAlignment(Qt.AlignCenter)
            auth_label.setStyleSheet("padding: 40px;")
            self.visualization_layout.addWidget(auth_label)
            self.visualization_layout.addStretch()
            return

        # Пользователь авторизован
        user_id = self.parent.current_user['id']
        diary_stats = self.parent.db.get_diary_stats(user_id)
        entries_count = diary_stats.get('total_entries', 0) if diary_stats else 0

        # Информация о данных
        info_label = QLabel(f"📝 У вас {entries_count} записей в дневнике")
        info_label.setProperty("class", "TextRegular")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        self.visualization_layout.addWidget(info_label)

        # Если достаточно данных, создаем виджет визуализации
        if entries_count >= 5:
            try:
                # Создаем виджет визуализации
                from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
                from matplotlib.figure import Figure

                # Создаем фигуру
                self.figure = Figure(figsize=(10, 6), dpi=100, facecolor='#FFFBF6')
                self.canvas = FigureCanvas(self.figure)

                # Начальное сообщение
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'Выберите тип графика для отображения',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=14, color='#8B7355')
                ax.set_axis_off()

                self.visualization_layout.addWidget(self.canvas)

                # Кнопки для выбора графика
                buttons_frame = QFrame()
                buttons_layout = QHBoxLayout(buttons_frame)
                buttons_layout.setSpacing(10)

                # Кнопка графика настроения
                mood_btn = QPushButton("📈 График настроения")
                mood_btn.setProperty("class", "SecondaryButton")
                mood_btn.clicked.connect(self.show_mood_chart)
                buttons_layout.addWidget(mood_btn)

                # Кнопка графика записей
                entries_btn = QPushButton("📊 График активности")
                entries_btn.setProperty("class", "SecondaryButton")
                entries_btn.clicked.connect(self.show_entries_chart)
                buttons_layout.addWidget(entries_btn)

                buttons_layout.addStretch()
                self.visualization_layout.addWidget(buttons_frame)

            except Exception as e:
                print(f"Ошибка создания графиков: {e}")
                error_label = QLabel(f"Не удалось создать графики: {str(e)[:100]}")
                error_label.setStyleSheet("color: #FF6B6B; padding: 20px;")
                error_label.setAlignment(Qt.AlignCenter)
                self.visualization_layout.addWidget(error_label)
        else:
            # Недостаточно данных
            warning_label = QLabel(
                f"⚠️ Недостаточно данных для построения графиков\n(нужно минимум 5 записей, у вас {entries_count})")
            warning_label.setProperty("class", "TextSecondary")
            warning_label.setAlignment(Qt.AlignCenter)
            warning_label.setStyleSheet("padding: 40px;")
            self.visualization_layout.addWidget(warning_label)

            # Кнопка для перехода в дневник
            diary_btn = QPushButton("📝 Перейти в дневник")
            diary_btn.setProperty("class", "PrimaryButton")
            diary_btn.clicked.connect(lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(2))
            diary_btn.setFixedWidth(200)
            self.visualization_layout.addWidget(diary_btn, 0, Qt.AlignCenter)

        self.visualization_layout.addStretch()

    def update_overview_tab(self, user_id):
        """Обновление вкладки обзора"""
        # Очищаем старый контент
        while self.overview_layout.count():
            item = self.overview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Заголовок
        title = QLabel("📊 Общий обзор")
        title.setProperty("class", "TitleMedium")
        self.overview_layout.addWidget(title)

        # Карточка с ключевыми показателями
        key_metrics_card = QFrame()
        key_metrics_card.setProperty("class", "MintCard")

        key_layout = QVBoxLayout(key_metrics_card)
        key_layout.setContentsMargins(25, 25, 25, 25)
        key_layout.setSpacing(15)

        # Заголовок карточки
        card_title = QLabel("🔑 Ключевые показатели")
        card_title.setProperty("class", "TitleSmall")
        key_layout.addWidget(card_title)

        try:
            # Получаем данные
            diary_stats = self.parent.db.get_diary_stats(user_id)
            mood_entries = self.parent.db.get_mood_entries(user_id, days=30)
            user_stats = self.parent.db.get_user_stats(user_id)

            if diary_stats:
                # Показатель 1: Всего записей
                total_entries_frame = QFrame()
                total_layout = QHBoxLayout(total_entries_frame)

                total_label = QLabel("📝 Всего записей:")
                total_label.setProperty("class", "TextRegular")
                total_layout.addWidget(total_label)

                total_layout.addStretch()

                total_value = QLabel(str(diary_stats.get('total_entries', 0)))
                total_value.setStyleSheet("font-weight: bold; font-size: 16px;")
                total_layout.addWidget(total_value)

                key_layout.addWidget(total_entries_frame)

                # Показатель 2: Дней подряд
                if user_stats:
                    streak_frame = QFrame()
                    streak_layout = QHBoxLayout(streak_frame)

                    streak_label = QLabel("🔥 Дней подряд:")
                    streak_label.setProperty("class", "TextRegular")
                    streak_layout.addWidget(streak_label)

                    streak_layout.addStretch()

                    streak_value = QLabel(str(user_stats.get('streak_days', 0)))
                    streak_value.setStyleSheet("font-weight: bold; font-size: 16px;")
                    streak_layout.addWidget(streak_value)

                    key_layout.addWidget(streak_frame)

                # Показатель 3: Среднее настроение
                if mood_entries:
                    mood_scores = [entry['mood_score'] for entry in mood_entries if entry['mood_score'] > 0]
                    avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0

                    mood_frame = QFrame()
                    mood_layout = QHBoxLayout(mood_frame)

                    mood_label = QLabel("😊 Среднее настроение:")
                    mood_label.setProperty("class", "TextRegular")
                    mood_layout.addWidget(mood_label)

                    mood_layout.addStretch()

                    mood_value = QLabel(f"{avg_mood:.1f}/10")
                    mood_value.setStyleSheet("font-weight: bold; font-size: 16px;")
                    mood_layout.addWidget(mood_value)

                    key_layout.addWidget(mood_frame)

                # Показатель 4: Частое искажение
                common_distortions = diary_stats.get('common_distortions', {})
                if common_distortions:
                    most_common = max(common_distortions.items(), key=lambda x: x[1], default=("Нет данных", 0))

                    distortion_frame = QFrame()
                    distortion_layout = QHBoxLayout(distortion_frame)

                    distortion_label = QLabel("🧠 Частое искажение:")
                    distortion_label.setProperty("class", "TextRegular")
                    distortion_layout.addWidget(distortion_label)

                    distortion_layout.addStretch()

                    distortion_value = QLabel(f"{most_common[0]} ({most_common[1]} раз)")
                    distortion_value.setStyleSheet("font-weight: bold; font-size: 16px;")
                    distortion_layout.addWidget(distortion_value)

                    key_layout.addWidget(distortion_frame)

            else:
                no_data = QLabel("Недостаточно данных для анализа")
                no_data.setProperty("class", "TextSecondary")
                no_data.setAlignment(Qt.AlignCenter)
                key_layout.addWidget(no_data)

        except Exception as e:
            print(f"Ошибка обновления обзора: {e}")
            error_label = QLabel("Ошибка загрузки данных")
            error_label.setProperty("class", "TextSecondary")
            error_label.setAlignment(Qt.AlignCenter)
            key_layout.addWidget(error_label)

        self.overview_layout.addWidget(key_metrics_card)
        self.overview_layout.addStretch()

    def show_no_data_message(self, message):
        """Показать сообщение об отсутствии данных"""
        # Создаем простой лейбл с сообщением
        label = QLabel(message)
        label.setProperty("class", "TextSecondary")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                padding: 40px;
                font-size: 16px;
            }
        """)

        # Добавляем на все вкладки
        self.overview_layout.addWidget(label)
        self.progress_layout.addWidget(label)
        self.insights_layout.addWidget(label)

    def update_progress_tab(self, user_id):
        """Обновление вкладки прогресса"""
        # Очищаем старый контент
        while self.progress_layout.count():
            item = self.progress_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Заголовок
        title = QLabel("📈 Анализ прогресса")
        title.setProperty("class", "TitleMedium")
        self.progress_layout.addWidget(title)

        try:
            # Получаем анализ прогресса
            progress_data = self.progress_analyzer.analyze_progress_trends(user_id)

            if not progress_data.get('has_data'):
                no_data = QLabel("Недостаточно данных для анализа прогресса")
                no_data.setProperty("class", "TextSecondary")
                no_data.setAlignment(Qt.AlignCenter)
                self.progress_layout.addWidget(no_data)
                self.progress_layout.addStretch()
                return

            # Карточка с общим баллом прогресса
            score_card = QFrame()
            score_card.setProperty("class", "WarmCard")

            score_layout = QVBoxLayout(score_card)
            score_layout.setContentsMargins(25, 25, 25, 25)
            score_layout.setSpacing(15)

            score_title = QLabel("🎯 Общий балл прогресса")
            score_title.setProperty("class", "TitleSmall")
            score_layout.addWidget(score_title)

            # Круговой прогресс (имитация)
            progress_frame = QFrame()
            progress_layout = QVBoxLayout(progress_frame)
            progress_layout.setAlignment(Qt.AlignCenter)

            progress_value = progress_data.get('progress_score', 0)
            progress_level = progress_data.get('progress_level', 'Новичок')

            score_label = QLabel(f"{progress_value}/100")
            score_label.setStyleSheet("""
                font-size: 48px;
                font-weight: bold;
                color: #5A5A5A;
            """)
            score_label.setAlignment(Qt.AlignCenter)
            progress_layout.addWidget(score_label)

            level_label = QLabel(f"Уровень: {progress_level}")
            level_label.setProperty("class", "TextRegular")
            level_label.setAlignment(Qt.AlignCenter)
            progress_layout.addWidget(level_label)

            score_layout.addWidget(progress_frame)
            self.progress_layout.addWidget(score_card)

            # Достигнутые цели
            if progress_data.get('goals_achieved'):
                goals_card = QFrame()
                goals_card.setProperty("class", "SoftPinkCard")

                goals_layout = QVBoxLayout(goals_card)
                goals_layout.setContentsMargins(25, 25, 25, 25)
                goals_layout.setSpacing(15)

                goals_title = QLabel("✅ Достигнутые цели")
                goals_title.setProperty("class", "TitleSmall")
                goals_layout.addWidget(goals_title)

                for goal in progress_data['goals_achieved'][:5]:  # Ограничиваем 5 целями
                    goal_label = QLabel(f"• {goal}")
                    goal_label.setProperty("class", "TextRegular")
                    goal_label.setWordWrap(True)
                    goals_layout.addWidget(goal_label)

                self.progress_layout.addWidget(goals_card)

            # Области для улучшения
            if progress_data.get('areas_for_improvement'):
                improvement_card = QFrame()
                improvement_card.setProperty("class", "MintCard")

                improvement_layout = QVBoxLayout(improvement_card)
                improvement_layout.setContentsMargins(25, 25, 25, 25)
                improvement_layout.setSpacing(15)

                improvement_title = QLabel("💡 Области для улучшения")
                improvement_title.setProperty("class", "TitleSmall")
                improvement_layout.addWidget(improvement_title)

                for area in progress_data['areas_for_improvement'][:3]:  # Ограничиваем 3 областями
                    area_label = QLabel(f"• {area}")
                    area_label.setProperty("class", "TextRegular")
                    area_label.setWordWrap(True)
                    improvement_layout.addWidget(area_label)

                self.progress_layout.addWidget(improvement_card)

        except Exception as e:
            print(f"Ошибка обновления прогресса: {e}")
            error_label = QLabel("Ошибка загрузки данных прогресса")
            error_label.setProperty("class", "TextSecondary")
            error_label.setAlignment(Qt.AlignCenter)
            self.progress_layout.addWidget(error_label)

        self.progress_layout.addStretch()

    def update_insights_tab(self, user_id):
        """Обновление вкладки инсайтов"""
        # Очищаем старый контент
        while self.insights_layout.count():
            item = self.insights_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Заголовок
        title = QLabel("💡 Персонализированные инсайты")
        title.setProperty("class", "TitleMedium")
        self.insights_layout.addWidget(title)

        try:
            # Получаем рекомендации
            recommendations = self.recommender.generate_personalized_recommendations(user_id)

            if not recommendations:
                no_data = QLabel("Недостаточно данных для генерации инсайтов")
                no_data.setProperty("class", "TextSecondary")
                no_data.setAlignment(Qt.AlignCenter)
                self.insights_layout.addWidget(no_data)
                self.insights_layout.addStretch()
                return

            # Сортируем рекомендации по приоритету
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            recommendations.sort(key=lambda x: priority_order[x.get('priority', 'medium')])

            # Отображаем рекомендации
            for i, rec in enumerate(recommendations[:5], 1):  # Ограничиваем 5 рекомендациями
                rec_card = QFrame()

                # Определяем цвет рамки по приоритету
                priority_color = "#FF6B6B" if rec.get('priority') == 'high' else "#FFD166" if rec.get(
                    'priority') == 'medium' else "#06D6A0"

                rec_card.setStyleSheet(f"""
                    QFrame {{
                        background-color: #FFFFFF;
                        border-radius: 12px;
                        border-left: 6px solid {priority_color};
                        border: 1px solid #E8DFD8;
                        margin: 5px;
                    }}
                    QFrame:hover {{
                        background-color: #F8F2E9;
                    }}
                """)

                rec_layout = QVBoxLayout(rec_card)
                rec_layout.setContentsMargins(20, 20, 20, 20)
                rec_layout.setSpacing(10)

                # Заголовок с номером
                header_frame = QFrame()
                header_layout = QHBoxLayout(header_frame)
                header_layout.setContentsMargins(0, 0, 0, 0)

                rec_title = QLabel(f"{i}. {rec.get('title', 'Рекомендация')}")
                rec_title.setStyleSheet("font-weight: bold; font-size: 16px;")
                header_layout.addWidget(rec_title)

                header_layout.addStretch()

                # Иконка приоритета
                priority_icon = "🔴" if rec.get('priority') == 'high' else "🟡" if rec.get(
                    'priority') == 'medium' else "🟢"
                priority_label = QLabel(priority_icon)
                header_layout.addWidget(priority_label)

                rec_layout.addWidget(header_frame)

                # Описание
                rec_desc = QLabel(rec.get('description', ''))
                rec_desc.setProperty("class", "TextRegular")
                rec_desc.setWordWrap(True)
                rec_layout.addWidget(rec_desc)

                # Категория
                if rec.get('category'):
                    category_frame = QFrame()
                    category_layout = QHBoxLayout(category_frame)
                    category_layout.setContentsMargins(0, 0, 0, 0)

                    category_label = QLabel(f"🏷️ {rec.get('category')}")
                    category_label.setProperty("class", "TextLight")
                    category_layout.addWidget(category_label)

                    category_layout.addStretch()
                    rec_layout.addWidget(category_frame)

                # Упражнения (если есть)
                if rec.get('exercises'):
                    exercises_label = QLabel(f"💪 Упражнения: {', '.join(rec['exercises'][:2])}")
                    exercises_label.setProperty("class", "TextSecondary")
                    exercises_label.setWordWrap(True)
                    rec_layout.addWidget(exercises_label)

                self.insights_layout.addWidget(rec_card)

            # Добавляем прогноз настроения
            self.add_mood_forecast(user_id)

        except Exception as e:
            print(f"Ошибка обновления инсайтов: {e}")
            error_label = QLabel("Ошибка загрузки инсайтов")
            error_label.setProperty("class", "TextSecondary")
            error_label.setAlignment(Qt.AlignCenter)
            self.insights_layout.addWidget(error_label)

        self.insights_layout.addStretch()

    def add_mood_forecast(self, user_id):
        """Добавление прогноза настроения"""
        try:
            prediction = self.predictor.predict_mood_trend(user_id, days_ahead=3)

            if prediction.get('can_predict'):
                forecast_card = QFrame()
                forecast_card.setProperty("class", "WarmCard")

                forecast_layout = QVBoxLayout(forecast_card)
                forecast_layout.setContentsMargins(25, 25, 25, 25)
                forecast_layout.setSpacing(15)

                forecast_title = QLabel("🔮 Прогноз настроения")
                forecast_title.setProperty("class", "TitleSmall")
                forecast_layout.addWidget(forecast_title)

                # Информация о тренде
                trend_icon = "📈" if prediction['trend'] == 'повышательный' else "📉" if prediction[
                                                                                           'trend'] == 'понижательный' else "➡️"
                trend_label = QLabel(f"Тренд: {trend_icon} {prediction['trend']}")
                trend_label.setProperty("class", "TextRegular")
                forecast_layout.addWidget(trend_label)

                # Прогноз на ближайшие дни
                if prediction.get('predictions'):
                    days = ['Сегодня', 'Завтра', 'Послезавтра']

                    for i, (day, pred) in enumerate(zip(days[:3], prediction['predictions'][:3])):
                        day_frame = QFrame()
                        day_layout = QHBoxLayout(day_frame)
                        day_layout.setContentsMargins(0, 0, 0, 0)

                        day_label = QLabel(day)
                        day_label.setFixedWidth(100)
                        day_layout.addWidget(day_label)

                        # Индикатор настроения
                        mood_icon = "😊" if pred >= 7 else "😐" if pred >= 5 else "😔"
                        mood_label = QLabel(f"{mood_icon} {pred:.1f}/10")
                        mood_label.setStyleSheet("font-weight: bold;")
                        day_layout.addWidget(mood_label)

                        forecast_layout.addWidget(day_frame)

                # Рекомендация
                if prediction.get('recommendation'):
                    rec_label = QLabel(f"💡 {prediction['recommendation']}")
                    rec_label.setProperty("class", "TextSecondary")
                    rec_label.setWordWrap(True)
                    forecast_layout.addWidget(rec_label)

                self.insights_layout.addWidget(forecast_card)

        except Exception as e:
            print(f"Ошибка прогноза настроения: {e}")
            # Не показываем карточку, если ошибка

    def show_progress_radar(self):
        """Показать радар прогресса"""
        try:
            if not self.parent.current_user:
                QMessageBox.information(self, "Информация", "Войдите в систему")
                return

            user_id = self.parent.current_user['id']

            # Создаем простой анализ прогресса
            diary_stats = self.parent.db.get_diary_stats(user_id)

            if not diary_stats or diary_stats.get('total_entries', 0) < 5:
                QMessageBox.information(self, "Информация",
                                        f"Недостаточно данных для анализа прогресса (нужно минимум 5 записей)")

                # Показываем заглушку
                self.visualization.figure.clear()
                ax = self.visualization.figure.add_subplot(111)
                ax.text(0.5, 0.5,
                        f'Недостаточно данных\n(записей: {diary_stats.get("total_entries", 0) if diary_stats else 0}/5)',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=14, color='#8B7355')
                ax.set_axis_off()
                self.visualization.canvas.draw()
                return

            # Создаем простые данные для радара
            progress_data = {
                'has_data': True,
                'progress_score': min(100, diary_stats.get('total_entries', 0) * 5),
                'progress_metrics': {
                    'avg_entry_interval': 1.0,  # Примерное значение
                    'distortion_reduction': 30,  # Примерное значение
                    'exercises_completed': 0
                },
                'goals_achieved': ['5+ записей в дневнике'] if diary_stats.get('total_entries', 0) >= 5 else []
            }

            # Очищаем предыдущий график
            self.visualization.figure.clear()
            self.visualization.plot_progress_radar(progress_data)

        except Exception as e:
            print(f"Ошибка при построении радара прогресса: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось построить радар: {str(e)}")

            # Показываем сообщение об ошибке
            self.visualization.figure.clear()
            ax = self.visualization.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Ошибка загрузки радара',
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=14, color='#FF6B6B')
            ax.set_axis_off()
            self.visualization.canvas.draw()


class MoodCalendar(QWidget):
    """Календарь настроения"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_date = QDate.currentDate()
        self.mood_data = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("📅 Календарь настроения")
        title.setProperty("class", "TitleMedium")
        layout.addWidget(title)

        # Навигация по месяцам
        nav_frame = QFrame()
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)

        prev_btn = QPushButton("◀")
        prev_btn.setProperty("class", "SecondaryButton")
        prev_btn.setFixedSize(40, 40)
        prev_btn.clicked.connect(self.prev_month)
        nav_layout.addWidget(prev_btn)

        self.month_label = QLabel()
        self.month_label.setProperty("class", "TitleSmall")
        self.month_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.month_label, 1)

        next_btn = QPushButton("▶")
        next_btn.setProperty("class", "SecondaryButton")
        next_btn.setFixedSize(40, 40)
        next_btn.clicked.connect(self.next_month)
        nav_layout.addWidget(next_btn)

        layout.addWidget(nav_frame)

        # Дни недели
        week_frame = QFrame()
        week_layout = QHBoxLayout(week_frame)
        week_layout.setSpacing(5)

        for day in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']:
            label = QLabel(day)
            label.setProperty("class", "TextRegular")
            label.setAlignment(Qt.AlignCenter)
            week_layout.addWidget(label)

        layout.addWidget(week_frame)

        # Сетка календаря
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(5)
        layout.addLayout(self.calendar_grid)

        # Легенда
        legend_frame = QFrame()
        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setSpacing(20)

        moods = [
            ("😊 Отлично", "#06D6A0"),
            ("😐 Нормально", "#FFD166"),
            ("😔 Плохо", "#FF6B6B"),
            ("📝 Есть запись", "#B5E5CF")
        ]

        for text, color in moods:
            legend_item = QFrame()
            item_layout = QHBoxLayout(legend_item)
            item_layout.setContentsMargins(0, 0, 0, 0)

            color_box = QFrame()
            color_box.setFixedSize(16, 16)
            color_box.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            item_layout.addWidget(color_box)

            label = QLabel(text)
            label.setProperty("class", "TextLight")
            item_layout.addWidget(label)

            legend_layout.addWidget(legend_item)

        legend_layout.addStretch()
        layout.addWidget(legend_frame)

        layout.addStretch()

        self.update_month()

    def update_month(self):
        """Обновление отображения месяца"""
        # Загружаем данные
        if self.parent.current_user:
            self.load_mood_data()

        # Обновляем заголовок
        self.month_label.setText(self.current_date.toString("MMMM yyyy"))

        # Очищаем сетку
        for i in reversed(range(self.calendar_grid.count())):
            widget = self.calendar_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Получаем первый день месяца
        first_day = QDate(self.current_date.year(), self.current_date.month(), 1)
        start_day = first_day.dayOfWeek() - 1  # 1 = понедельник, 7 = воскресенье

        # Получаем количество дней в месяце
        days_in_month = self.current_date.daysInMonth()

        # Заполняем календарь
        row = 0
        col = start_day

        for day in range(1, days_in_month + 1):
            date = QDate(self.current_date.year(), self.current_date.month(), day)
            date_str = date.toString("yyyy-MM-dd")

            # Создаем ячейку дня
            day_cell = self.create_day_cell(day, date_str)
            self.calendar_grid.addWidget(day_cell, row, col)

            col += 1
            if col > 6:
                col = 0
                row += 1

    def create_day_cell(self, day, date_str):
        """Создание ячейки для дня"""
        cell = QFrame()
        cell.setProperty("class", "Card")
        cell.setFixedSize(100, 80)
        cell.setCursor(Qt.PointingHandCursor)

        # Определяем стиль на основе данных
        mood = self.mood_data.get(date_str, {})

        layout = QVBoxLayout(cell)
        layout.setSpacing(5)

        # Число
        day_label = QLabel(str(day))
        day_label.setStyleSheet("font-weight: bold; font-size: 18px;")
        layout.addWidget(day_label)

        # Эмодзи настроения
        if mood.get('mood'):
            mood_icons = {1: '😔', 2: '😕', 3: '😐', 4: '🙂', 5: '😊',
                          6: '😄', 7: '😁', 8: '😎', 9: '🤗', 10: '🥳'}
            emoji = mood_icons.get(mood['mood'], '😐')
        else:
            emoji = ''

        # Индикатор записи
        if mood.get('has_entry'):
            emoji += ' 📝'

        mood_label = QLabel(emoji)
        mood_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(mood_label)

        return cell

    def load_mood_data(self):
        """Загрузка данных о настроении"""
        user_id = self.parent.current_user['id']

        # Получаем записи настроения
        start_date = QDate(self.current_date.year(), self.current_date.month(), 1)
        end_date = QDate(self.current_date.year(), self.current_date.month(),
                         self.current_date.daysInMonth())

        # В реальном приложении - запрос к БД за этот месяц
        mood_entries = self.parent.db.get_mood_entries(user_id, days=31)

        # Получаем записи дневника
        diary_entries = self.parent.db.get_diary_entries(user_id, limit=50)
        diary_dates = [e['created_at'][:10] for e in diary_entries]

        # Формируем словарь
        self.mood_data = {}
        for entry in mood_entries:
            date = entry['date']
            if date not in self.mood_data:
                self.mood_data[date] = {}
            self.mood_data[date]['mood'] = entry['mood_score']

        for date in diary_dates:
            if date not in self.mood_data:
                self.mood_data[date] = {}
            self.mood_data[date]['has_entry'] = True

    def prev_month(self):
        """Предыдущий месяц"""
        self.current_date = self.current_date.addMonths(-1)
        self.update_month()

    def next_month(self):
        """Следующий месяц"""
        self.current_date = self.current_date.addMonths(1)
        self.update_month()


class GroupSupportWidget(QWidget):
    """Виджет групповой поддержки"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("👥 Групповая поддержка")
        title.setProperty("class", "TitleMedium")
        layout.addWidget(title)

        # Описание
        desc = QLabel("Присоединяйтесь к группам поддержки, делитесь опытом и получайте поддержку")
        desc.setProperty("class", "TextSecondary")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Список групп
        groups = [
            ("🌿 Управление тревожностью", "15 участников", "Активно сейчас"),
            ("😊 Позитивное мышление", "23 участника", "Новые сообщения"),
            ("🧘 Медитация и осознанность", "12 участников", "Тихий час"),
            ("💪 Мотивация и цели", "8 участников", "Активно сейчас"),
        ]

        for name, members, status in groups:
            group_card = self.create_group_card(name, members, status)
            layout.addWidget(group_card)

        # Кнопка создания группы
        create_btn = QPushButton("➕ Создать свою группу")
        create_btn.setProperty("class", "PrimaryButton")
        create_btn.clicked.connect(self.create_group)
        layout.addWidget(create_btn)

        layout.addStretch()

    def create_group_card(self, name, members, status):
        """Создание карточки группы"""
        card = QFrame()
        card.setProperty("class", "Card")
        card.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        # Название
        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(name_label)

        # Информация
        info_frame = QFrame()
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)

        members_label = QLabel(f"👥 {members}")
        members_label.setProperty("class", "TextSecondary")
        info_layout.addWidget(members_label)

        info_layout.addStretch()

        # Статус
        status_color = "#06D6A0" if "Активно" in status else "#FFD166"
        status_label = QLabel(f"● {status}")
        status_label.setStyleSheet(f"color: {status_color};")
        info_layout.addWidget(status_label)

        layout.addWidget(info_frame)

        # Кнопка входа
        join_btn = QPushButton("Войти в группу")
        join_btn.setProperty("class", "SecondaryButton")
        join_btn.clicked.connect(lambda: self.join_group(name))
        layout.addWidget(join_btn)

        return card

    def join_group(self, group_name):
        """Присоединение к группе"""
        QMessageBox.information(self, "Группа",
                                f"Вы присоединились к группе '{group_name}'\n\n"
                                "Функционал групп будет доступен в следующем обновлении!")

    def create_group(self):
        """Создание группы"""
        name, ok = QInputDialog.getText(self, "Создание группы", "Название группы:")
        if ok and name:
            QMessageBox.information(self, "Группа создана",
                                    f"Группа '{name}' успешно создана!")


class DataExporter(QWidget):
    """Виджет для экспорта данных в различные форматы"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("📤 Экспорт данных")
        title.setProperty("class", "TitleMedium")
        layout.addWidget(title)

        # Описание
        desc = QLabel("Вы можете экспортировать свои данные для анализа или печати")
        desc.setProperty("class", "TextSecondary")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Выбор периода
        period_frame = QFrame()
        period_layout = QHBoxLayout(period_frame)
        period_layout.setContentsMargins(0, 0, 0, 0)

        period_label = QLabel("Период:")
        period_label.setProperty("class", "TextRegular")
        period_layout.addWidget(period_label)

        self.period_combo = QComboBox()
        self.period_combo.addItems(["Всё время", "Последний месяц", "Последняя неделя"])
        self.period_combo.setFixedWidth(150)
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()

        layout.addWidget(period_frame)

        # Форматы экспорта
        formats_frame = QFrame()
        formats_layout = QHBoxLayout(formats_frame)
        formats_layout.setSpacing(20)

        # PDF
        pdf_card = self.create_format_card(
            "📄 PDF",
            "Красивый отчет с графиками",
            "#FFB38E",
            lambda: self.export_pdf()
        )
        formats_layout.addWidget(pdf_card)

        # CSV
        csv_card = self.create_format_card(
            "📊 CSV",
            "Для анализа в Excel",
            "#B5E5CF",
            lambda: self.export_csv()
        )
        formats_layout.addWidget(csv_card)

        # JSON
        json_card = self.create_format_card(
            "🔧 JSON",
            "Для разработчиков",
            "#FFD6DC",
            lambda: self.export_json()
        )
        formats_layout.addWidget(json_card)

        layout.addWidget(formats_frame)

        # Что экспортировать
        what_frame = QFrame()
        what_layout = QVBoxLayout(what_frame)
        what_layout.setSpacing(10)

        what_title = QLabel("Что экспортировать:")
        what_title.setProperty("class", "TextRegular")
        what_title.setStyleSheet("font-weight: bold;")
        what_layout.addWidget(what_title)

        self.export_diary = QCheckBox("📝 Записи дневника")
        self.export_diary.setChecked(True)
        what_layout.addWidget(self.export_diary)

        self.export_mood = QCheckBox("😊 Отметки настроения")
        self.export_mood.setChecked(True)
        what_layout.addWidget(self.export_mood)

        self.export_stats = QCheckBox("📊 Статистику и прогресс")
        self.export_stats.setChecked(True)
        what_layout.addWidget(self.export_stats)

        self.export_achievements = QCheckBox("🏆 Достижения")
        self.export_achievements.setChecked(True)
        what_layout.addWidget(self.export_achievements)

        layout.addWidget(what_frame)

        # Кнопка экспорта
        export_btn = QPushButton("📥 Сформировать отчет")
        export_btn.setProperty("class", "PrimaryButton")
        export_btn.setFixedHeight(50)
        export_btn.clicked.connect(self.generate_report)
        layout.addWidget(export_btn)

        # Прогресс
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

    def create_format_card(self, title, desc, color, callback):
        """Создание карточки формата"""
        card = QPushButton()
        card.setFixedSize(150, 120)
        card.clicked.connect(callback)

        card.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                border-radius: 12px;
                border-left: 6px solid {color};
                border: 1px solid #E8DFD8;
                padding: 15px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: #F8F2E9;
                border-left: 6px solid {self.darken_color(color)};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)

        desc_label = QLabel(desc)
        desc_label.setProperty("class", "TextLight")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        return card

    def export_pdf(self):
        """Экспорт в PDF"""
        if not self.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему")
            return

        # Сохраняем файл
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчет", "", "PDF Files (*.pdf)"
        )

        if filename:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)

            # Имитация процесса
            for i in range(101):
                QApplication.processEvents()
                self.progress_bar.setValue(i)

            self.progress_bar.setVisible(False)
            QMessageBox.information(self, "Готово", f"Отчет сохранен:\n{filename}")

    def export_csv(self):
        """Экспорт в CSV"""
        if not self.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить данные", "", "CSV Files (*.csv)"
        )

        if filename:
            try:
                import csv

                user_id = self.parent.current_user['id']

                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)

                    # Заголовки
                    writer.writerow(['Дата', 'Тип', 'Значение', 'Заметки'])

                    # Записи настроения
                    mood_entries = self.parent.db.get_mood_entries(user_id, days=365)
                    for entry in mood_entries:
                        writer.writerow([
                            entry['date'],
                            'Настроение',
                            entry['mood_score'],
                            entry.get('notes', '')
                        ])

                    # Записи дневника
                    diary_entries = self.parent.db.get_diary_entries(user_id, limit=100)
                    for entry in diary_entries:
                        writer.writerow([
                            entry['created_at'][:10],
                            'Запись',
                            '',
                            entry['situation'][:50]
                        ])

                QMessageBox.information(self, "Готово", f"Данные сохранены в CSV")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {str(e)}")

    def export_json(self):
        """Экспорт в JSON"""
        if not self.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить данные", "", "JSON Files (*.json)"
        )

        if filename:
            try:
                user_id = self.parent.current_user['id']

                data = {
                    'user': self.parent.current_user['name'],
                    'export_date': datetime.now().isoformat(),
                    'stats': dict(self.parent.db.get_user_stats(user_id)),
                    'mood_entries': [dict(e) for e in self.parent.db.get_mood_entries(user_id, days=365)],
                    'diary_entries': self.parent.db.get_diary_entries(user_id, limit=100)
                }

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)

                QMessageBox.information(self, "Готово", f"Данные сохранены в JSON")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {str(e)}")

    def generate_report(self):
        """Создание отчета"""
        QMessageBox.information(self, "Отчет", "Функция в разработке!")

    def darken_color(self, color):
        """Затемнить цвет"""
        colors = {
            "#FFB38E": "#FF9E70",
            "#B5E5CF": "#9BD1B8",
            "#FFD6DC": "#FFC8D6"
        }
        return colors.get(color, color)


class ThemeManager:
    """Менеджер тем приложения"""

    LIGHT_THEME = """
        /* Светлая тема (текущая) */
        QMainWindow { background-color: #FFFBF6; }
        QWidget { color: #5A5A5A; }
        .Card { background-color: #FFFFFF; border: 1px solid #E8DFD8; }
        .WarmCard { background-color: #F8F2E9; border: 1px solid #E8DFD8; }
        .MintCard { background-color: #B5E5CF; }
        .SoftPinkCard { background-color: #FFD6DC; }
        QPushButton { border: none; padding: 12px 24px; border-radius: 8px; }
        .PrimaryButton { background-color: #B5E5CF; color: #5A5A5A; }
        .SecondaryButton { background-color: #F8F2E9; color: #8B7355; }
    """

    DARK_THEME = """
        /* Темная тема */
        QMainWindow { background-color: #2C3E50; }
        QWidget { color: #ECF0F1; }
        .Card { background-color: #34495E; border: 1px solid #4A5A6A; }
        .WarmCard { background-color: #3A4A5A; border: 1px solid #4A5A6A; }
        .MintCard { background-color: #27AE60; }
        .SoftPinkCard { background-color: #E74C3C; }
        QPushButton { border: none; padding: 12px 24px; border-radius: 8px; }
        .PrimaryButton { background-color: #27AE60; color: #ECF0F1; }
        .SecondaryButton { background-color: #3A4A5A; color: #BDC3C7; border: 1px solid #4A5A6A; }
        QLineEdit { background-color: #34495E; border: 1px solid #4A5A6A; color: #ECF0F1; }
        QTextEdit { background-color: #34495E; border: 1px solid #4A5A6A; color: #ECF0F1; }
        QComboBox { background-color: #34495E; border: 1px solid #4A5A6A; color: #ECF0F1; }
        QTabBar::tab { background-color: #3A4A5A; color: #BDC3C7; }
        QTabBar::tab:selected { background-color: #27AE60; color: #ECF0F1; }
        QProgressBar { background-color: #34495E; }
        QProgressBar::chunk { background-color: #27AE60; }
        QScrollBar:vertical { background-color: #34495E; }
        QScrollBar::handle:vertical { background-color: #4A5A6A; }
    """

    def __init__(self, app):
        self.app = app
        self.current_theme = 'light'

    def toggle_theme(self):
        """Переключение темы"""
        if self.current_theme == 'light':
            self.app.setStyleSheet(self.DARK_THEME)
            self.current_theme = 'dark'
        else:
            self.app.setStyleSheet(self.LIGHT_THEME)
            self.current_theme = 'light'

    def get_theme_button(self):
        """Получить кнопку переключения темы"""
        btn = QPushButton("🌙 Темная тема" if self.current_theme == 'light' else "☀️ Светлая тема")
        btn.setProperty("class", "SecondaryButton")
        btn.clicked.connect(self.toggle_theme)
        return btn


class EmotionClassifier:
    """Классификатор эмоций на основе текста с машинным обучением"""

    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.label_encoder = LabelEncoder()
        self.is_trained = False

    def train_model(self, db, user_id):
        """Обучение модели на данных пользователя"""
        try:
            # Получаем записи пользователя
            entries = db.get_diary_entries(user_id, limit=100)

            if len(entries) < 10:
                return False, "Недостаточно данных для обучения (нужно минимум 10 записей)"

            # Подготовка данных
            texts = []
            emotions = []

            for entry in entries:
                # Объединяем ситуацию и мысли
                text = entry['situation'] + ' ' + entry['thoughts']
                texts.append(self._preprocess_text(text))

                # Определяем основную эмоцию
                emotions_entry = entry['emotions']
                if emotions_entry:
                    # Берем эмоцию с максимальной интенсивностью
                    main_emotion = max(emotions_entry.items(), key=lambda x: x[1])[0]
                    emotions.append(main_emotion)
                else:
                    emotions.append('нейтральная')

            # Кодируем метки
            emotion_labels = self.label_encoder.fit_transform(emotions)

            # Создаем и обучаем модель
            self.vectorizer = CountVectorizer(
                max_features=1000,
                stop_words=['и', 'в', 'на', 'с', 'по', 'для', 'что', 'это', 'как', 'но']
            )

            self.model = make_pipeline(
                self.vectorizer,
                MultinomialNB()
            )

            self.model.fit(texts, emotion_labels)
            self.is_trained = True

            # Оцениваем точность
            accuracy = self.model.score(texts, emotion_labels)

            return True, f"Модель обучена на {len(entries)} записях. Точность: {accuracy:.2f}"

        except Exception as e:
            return False, f"Ошибка обучения: {str(e)}"

    def predict_emotion(self, text):
        """Предсказание эмоции по тексту"""
        if not self.is_trained or self.model is None:
            return None, "Модель не обучена"

        try:
            processed_text = self._preprocess_text(text)
            prediction = self.model.predict([processed_text])[0]
            emotion = self.label_encoder.inverse_transform([prediction])[0]

            return emotion, None
        except Exception as e:
            return None, f"Ошибка предсказания: {str(e)}"

    def _preprocess_text(self, text):
        """Предобработка текста"""
        # Приводим к нижнему регистру
        text = text.lower()
        # Удаляем специальные символы
        text = re.sub(r'[^\w\s]', ' ', text)
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def get_emotion_statistics(self, predictions):
        """Статистика по предсказанным эмоциям"""
        if not predictions:
            return {}

        counter = Counter(predictions)
        total = len(predictions)

        statistics = {
            'total_predictions': total,
            'emotion_counts': dict(counter),
            'emotion_percentages': {emotion: (count / total) * 100 for emotion, count in counter.items()},
            'most_common': counter.most_common(1)[0] if counter else None
        }

        return statistics


class IntelligentRecommender:
    """Интеллектуальная система рекомендаций"""

    def __init__(self, db):
        self.db = db

    def generate_personalized_recommendations(self, user_id):
        """Генерация персонализированных рекомендаций на основе анализа данных"""
        try:
            recommendations = []

            # Анализируем данные пользователя
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

                # Анализ стабильности настроения
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

            return recommendations[:5]  # Ограничиваем 5 рекомендациями

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


class ProgressAnalyzer:
    """Анализатор прогресса и достижения целей"""

    def __init__(self, db):
        self.db = db

    def analyze_progress_trends(self, user_id):
        """Анализ трендов прогресса"""
        try:
            # Получаем исторические данные
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
                # Рассчитываем средний интервал между записями
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

            # Анализ роста самосознания (по уменьшению искажений)
            if len(diary_entries) >= 10:
                # Разделяем на ранние и поздние записи
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

            # Баллы за количество записей
            total_entries = len(diary_entries)
            if total_entries >= 20:
                progress_score += 30
            elif total_entries >= 10:
                progress_score += 20
            elif total_entries >= 5:
                progress_score += 10

            # Баллы за достижения
            completed_achievements = [a for a in achievements if a['completed']]
            progress_score += len(completed_achievements) * 5

            # Баллы за упражнения
            if 'exercises_completed' in analysis['progress_metrics']:
                if analysis['progress_metrics']['exercises_completed'] >= 10:
                    progress_score += 20
                elif analysis['progress_metrics']['exercises_completed'] >= 5:
                    progress_score += 10

            analysis['progress_score'] = min(100, progress_score)

            # Определение уровня прогресса
            if progress_score >= 80:
                analysis['progress_level'] = 'Продвинутый'
            elif progress_score >= 50:
                analysis['progress_level'] = 'Средний'
            elif progress_score >= 20:
                analysis['progress_level'] = 'Начинающий'
            else:
                analysis['progress_level'] = 'Новичок'

            # Рекомендации по улучшению
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

            # Получаем текущую статистику
            diary_stats = self.db.get_diary_stats(user_id)
            user_stats = self.db.get_user_stats(user_id)

            if not diary_stats or not user_stats:
                return goals

            current_entries = diary_stats['total_entries']
            current_streak = user_stats['streak_days']

            # Цели по записям
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

            # Цели по серии дней
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

            # Цели по упражнениям
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

            # Цели по эмоциональному благополучию
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


class EnhancedVisualizationWidget(QWidget):
    """Улучшенный виджет визуализации данных с графиками"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = None
        self.canvas = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        try:
            # Импорты matplotlib
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure

            # Создаем matplotlib figure
            self.figure = Figure(figsize=(10, 6), dpi=100, facecolor='#FFFBF6')
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setStyleSheet("background-color: transparent;")

            # Показываем начальное сообщение
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Выберите тип графика для отображения',
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=14, color='#8B7355')
            ax.set_axis_off()

            layout.addWidget(self.canvas)

        except Exception as e:
            print(f"Ошибка инициализации виджета визуализации: {e}")
            # Если не удалось создать график, показываем сообщение
            error_label = QLabel(f"Ошибка инициализации графиков: {str(e)[:100]}...")
            error_label.setStyleSheet("color: #FF6B6B; padding: 20px;")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)

    def plot_emotion_timeline(self, entries):
        """Построение графика временной линии эмоций"""
        try:
            self.figure.clear()

            if not entries or len(entries) < 5:
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'Недостаточно данных\n(минимум 5 записей)',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=14, color='#8B7355')
                ax.set_axis_off()
                self.canvas.draw()
                return

            ax = self.figure.add_subplot(111)

            # Упрощенный график (без сложной обработки)
            dates = []
            mood_scores = []

            for entry in entries:
                # Используем дату создания
                date_str = entry['created_at'].split()[0]  # Берем только дату
                dates.append(date_str)

                # Простая оценка настроения по эмоциям
                emotions = entry.get('emotions', {})
                if emotions:
                    # Средняя интенсивность эмоций как индикатор настроения
                    intensities = list(emotions.values())
                    avg_intensity = sum(intensities) / len(intensities) if intensities else 50
                    # Конвертируем в 1-10 шкалу
                    mood_score = max(1, min(10, avg_intensity / 10))
                else:
                    mood_score = 5  # Нейтральное значение

                mood_scores.append(mood_score)

            # Простой линейный график
            x = range(len(dates))
            ax.plot(x, mood_scores, 'o-', color='#9BD1B8', linewidth=2, markersize=8)

            # Настройки
            ax.set_title('Динамика эмоционального состояния', fontsize=14, pad=15)
            ax.set_xlabel('Записи', fontsize=11)
            ax.set_ylabel('Настроение (1-10)', fontsize=11)
            ax.set_ylim(0, 11)
            ax.grid(True, alpha=0.3)

            # Упрощенные подписи дат (каждая 3-я)
            if len(dates) > 10:
                tick_indices = range(0, len(dates), max(1, len(dates) // 5))
                ax.set_xticks([x[i] for i in tick_indices])
                ax.set_xticklabels([dates[i] for i in tick_indices], rotation=45, ha='right')
            else:
                ax.set_xticks(x)
                ax.set_xticklabels(dates, rotation=45, ha='right')

            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            print(f"Ошибка построения графика эмоций: {e}")
            self.show_error_message(f"Ошибка: {str(e)[:50]}...")

    def plot_progress_radar(self, progress_data):
        """Упрощенный радар прогресса"""
        try:
            self.figure.clear()

            if not progress_data.get('has_data'):
                self.show_error_message("Нет данных для радара")
                return

            ax = self.figure.add_subplot(111, polar=True)

            # Простые категории
            categories = ['Записи', 'Регулярность', 'Настроение', 'Анализ']

            # Простые значения (0-1)
            values = [0.7, 0.5, 0.8, 0.6]

            # Замыкаем круг
            values += values[:1]
            angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))]
            angles += angles[:1]

            # Построение
            ax.plot(angles, values, 'o-', linewidth=2, color='#FFB38E')
            ax.fill(angles, values, alpha=0.25, color='#FFB38E')

            # Настройки
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, fontsize=11)
            ax.set_ylim(0, 1)
            ax.set_yticks([0.25, 0.5, 0.75, 1])
            ax.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=9)

            ax.set_title('Профиль прогресса', fontsize=14, pad=20)

            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            print(f"Ошибка построения радара: {e}")
            self.show_error_message(f"Ошибка радара: {str(e)[:50]}...")

    def show_error_message(self, message):
        """Показать сообщение об ошибке"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, message,
                ha='center', va='center', transform=ax.transAxes,
                fontsize=12, color='#FF6B6B')
        ax.set_axis_off()
        self.canvas.draw()


def main():
    """Главная функция приложения"""
    app = QApplication(sys.argv)

    # Устанавливаем современный стиль
    app.setStyle('Fusion')

    # Создаем и показываем главное окно
    try:
        window = MentalHealthApp()
        window.show()
        window.center_on_screen()

        # Запускаем приложение
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")
        QMessageBox.critical(None, "Ошибка запуска", f"Приложение не может быть запущено:\n{str(e)}")
        sys.exit(1)


class SimpleMusicPlayer(QWidget):
    """Простой музыкальный плеер"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎵 Музыка")
        self.setFixedSize(350, 250)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFBF6;
                border: 2px solid #E8DFD8;
                border-radius: 10px;
            }
        """)

        self.is_playing = False
        self.volume = 50
        self.current_track_index = 0
        self.pygame = None
        self.audio_available = False

        # Треки с полными путями
        self.tracks = [
            {"name": "🌊 Звуки океана", "file": "ocean.mp3"},
            {"name": "🌧️ Шум дождя", "file": "rain.mp3"},
            {"name": "🔥 Потрескивание костра", "file": "fire.mp3"},
            {"name": "🎹 Фортепиано", "file": "piano.mp3"},
            {"name": "🧘 Медитация", "file": "meditation.mp3"}
        ]

        # Получаем полный путь к папке music
        import os
        self.music_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets/music")
        print(f"📁 Музыкальная папка: {self.music_dir}")

        # Добавляем полные пути к файлам
        for track in self.tracks:
            track["full_path"] = os.path.join(self.music_dir, track["file"])
            print(f"  • {track['name']}: {track['full_path']}")

        self.init_ui()
        self.init_audio()
        self.check_music_files()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок
        title = QLabel("🎵 Расслабляющая музыка")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #5A5A5A;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Статус файлов
        self.files_status = QLabel("")
        self.files_status.setStyleSheet("color: #8B7355; font-size: 10px;")
        self.files_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.files_status)

        # Выбор трека
        track_frame = QFrame()
        track_layout = QHBoxLayout(track_frame)
        track_layout.setContentsMargins(0, 0, 0, 0)

        track_label = QLabel("Трек:")
        track_label.setStyleSheet("color: #8B7355;")
        track_layout.addWidget(track_label)

        self.track_combo = QComboBox()
        self.track_combo.addItems([t["name"] for t in self.tracks])
        self.track_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #E8DFD8;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
                min-width: 180px;
            }
            QComboBox:hover {
                border-color: #B5E5CF;
            }
        """)
        self.track_combo.currentIndexChanged.connect(self.change_track)
        track_layout.addWidget(self.track_combo)

        layout.addWidget(track_frame)

        # Кнопки управления
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(15)

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(60, 40)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #B5E5CF;
                border: none;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9BD1B8;
            }
            QPushButton:disabled {
                background-color: #E8DFD8;
                color: #C4B6A6;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.play_btn)

        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setFixedSize(60, 40)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFD6DC;
                border: none;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFC8D6;
            }
            QPushButton:disabled {
                background-color: #E8DFD8;
                color: #C4B6A6;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_music)
        controls_layout.addWidget(self.stop_btn)

        layout.addWidget(controls_frame)

        # Громкость
        volume_frame = QFrame()
        volume_layout = QHBoxLayout(volume_frame)
        volume_layout.setContentsMargins(0, 0, 0, 0)

        volume_label = QLabel("🔊")
        volume_label.setStyleSheet("color: #8B7355; font-size: 16px;")
        volume_layout.addWidget(volume_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.volume)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #E8DFD8;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #B5E5CF;
                width: 15px;
                margin: -4px 0;
                border-radius: 7px;
            }
        """)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)

        self.volume_value = QLabel(f"{self.volume}%")
        self.volume_value.setStyleSheet("color: #5A5A5A; min-width: 35px;")
        volume_layout.addWidget(self.volume_value)

        layout.addWidget(volume_frame)

        # Статус
        self.status_label = QLabel("⏸ Готов")
        self.status_label.setStyleSheet("color: #C4B6A6; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch()

    def init_audio(self):
        """Инициализация аудио"""
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            self.pygame = pygame
            self.audio_available = True
            print("✅ Аудио система инициализирована")
        except ImportError:
            print("⚠️ Pygame не установлен. Установите: pip install pygame")
            self.audio_available = False
        except Exception as e:
            print(f"⚠️ Ошибка инициализации аудио: {e}")
            self.audio_available = False

    def check_music_files(self):
        """Проверка наличия музыкальных файлов"""
        import os

        found_files = []
        missing_files = []

        for track in self.tracks:
            if os.path.exists(track["full_path"]):
                found_files.append(track["name"])
                print(f"✅ Найден: {track['file']}")
            else:
                missing_files.append(track["file"])
                print(f"❌ Не найден: {track['file']}")

        if found_files:
            self.files_status.setText(f"✅ Найдено файлов: {len(found_files)}/{len(self.tracks)}")
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
        else:
            self.files_status.setText("❌ Музыкальные файлы не найдены")
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)

    def toggle_play(self):
        """Воспроизведение/пауза"""
        if not self.audio_available or not self.pygame:
            self.show_install_instructions()
            return

        current_track = self.tracks[self.track_combo.currentIndex()]

        import os
        if not os.path.exists(current_track["full_path"]):
            self.status_label.setText(f"❌ Файл не найден: {current_track['file']}")
            return

        try:
            if self.is_playing:
                self.pygame.mixer.music.pause()
                self.play_btn.setText("▶")
                self.status_label.setText(f"⏸ Пауза")
                self.is_playing = False
                print("⏸ Музыка на паузе")
            else:
                # Останавливаем предыдущее воспроизведение
                self.pygame.mixer.music.stop()

                # Загружаем и играем
                print(f"🎵 Загружаем: {current_track['full_path']}")
                self.pygame.mixer.music.load(current_track["full_path"])
                self.pygame.mixer.music.play(-1)  # -1 для зацикливания
                self.pygame.mixer.music.set_volume(self.volume / 100)
                self.play_btn.setText("⏸")
                self.status_label.setText(f"▶ Играет: {current_track['name']}")
                self.is_playing = True
                print(f"✅ Музыка играет: {current_track['name']}")

        except pygame.error as e:
            print(f"❌ Ошибка pygame: {e}")
            self.status_label.setText(f"❌ Ошибка воспроизведения")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.status_label.setText(f"❌ Ошибка")

    def stop_music(self):
        """Остановка музыки"""
        if not self.audio_available or not self.pygame:
            return

        try:
            self.pygame.mixer.music.stop()
            self.is_playing = False
            self.play_btn.setText("▶")
            self.status_label.setText("⏸ Остановлено")
            print("⏹ Музыка остановлена")
        except Exception as e:
            print(f"Ошибка остановки: {e}")

    def change_track(self, index):
        """Смена трека"""
        self.current_track_index = index
        if self.is_playing:
            self.stop_music()

        track = self.tracks[index]
        import os
        if os.path.exists(track["full_path"]):
            self.status_label.setText(f"Выбран: {track['name']}")
        else:
            self.status_label.setText(f"❌ Файл {track['file']} не найден")

    def change_volume(self, value):
        """Изменение громкости"""
        self.volume = value
        self.volume_value.setText(f"{value}%")
        if self.audio_available and self.pygame and self.is_playing:
            try:
                self.pygame.mixer.music.set_volume(value / 100)
            except:
                pass

    def show_install_instructions(self):
        """Показать инструкции по установке"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Настройка музыки")
        msg.setText("🎵 Настройка музыкального плеера")
        msg.setInformativeText(
            "Установите pygame:\n\n"
            "pip install pygame\n\n"
            "После установки перезапустите приложение."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def closeEvent(self, event):
        """При закрытии останавливаем музыку"""
        self.stop_music()
        event.accept()

class SimpleBreathingExercise(QWidget):
    """Простое дыхательное упражнение"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("🌬 Дыхательное упражнение")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFBF6;
            }
            QLabel {
                color: #5A5A5A;
            }
            QPushButton {
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton#startBtn {
                background-color: #B5E5CF;
                color: #5A5A5A;
            }
            QPushButton#startBtn:hover {
                background-color: #9BD1B8;
            }
            QPushButton#stopBtn {
                background-color: #FFD6DC;
                color: #5A5A5A;
            }
            QPushButton#stopBtn:hover {
                background-color: #FFC8D6;
            }
            QPushButton#closeBtn {
                background-color: #F8F2E9;
                color: #8B7355;
                border: 1px solid #E8DFD8;
            }
            QPushButton#closeBtn:hover {
                background-color: #E8DFD8;
            }
        """)

        self.current_phase = "inhale"
        self.cycle_count = 0
        self.max_cycles = 5
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_phase)
        self.time_left = 0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title = QLabel("🌬 Дыхательное упражнение 4-7-8")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2C3E50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Инструкция
        instruction = QLabel(
            "Эта техника помогает успокоить нервную систему:\n\n"
            "• Вдохните через нос на 4 секунды\n"
            "• Задержите дыхание на 7 секунд\n"
            "• Медленно выдохните через рот на 8 секунд\n\n"
            "Повторите 5 раз"
        )
        instruction.setStyleSheet("""
            font-size: 14px;
            color: #5A5A5A;
            background-color: #F8F2E9;
            padding: 15px;
            border-radius: 10px;
            line-height: 1.5;
        """)
        instruction.setWordWrap(True)
        layout.addWidget(instruction)

        # Фаза дыхания
        self.phase_label = QLabel("🌬️ Приготовьтесь...")
        self.phase_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #B5E5CF;")
        self.phase_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.phase_label)

        # Таймер
        self.timer_label = QLabel("5")
        self.timer_label.setStyleSheet("font-size: 72px; font-weight: bold; color: #2C3E50;")
        self.timer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timer_label)

        # Счетчик циклов
        self.counter_label = QLabel("Цикл 0 из 5")
        self.counter_label.setStyleSheet("font-size: 16px; color: #8B7355;")
        self.counter_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.counter_label)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        self.start_btn = QPushButton("▶ Начать")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setFixedHeight(45)
        self.start_btn.clicked.connect(self.start_exercise)
        buttons_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏸ Пауза")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setFixedHeight(45)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.pause_exercise)
        buttons_layout.addWidget(self.stop_btn)

        layout.addLayout(buttons_layout)

        # Кнопка закрытия
        close_btn = QPushButton("✕ Закрыть")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedHeight(35)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def start_exercise(self):
        """Начать упражнение"""
        self.cycle_count = 0
        self.current_phase = "inhale"
        self.phase_label.setText("🌬️ Вдох")
        self.counter_label.setText(f"Цикл {self.cycle_count + 1} из {self.max_cycles}")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.time_left = 4
        self.timer_label.setText(str(self.time_left))
        self.timer.start(1000)

    def pause_exercise(self):
        """Поставить на паузу"""
        self.timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.phase_label.setText("⏸ Пауза")

    def next_phase(self):
        """Переход к следующей фазе"""
        self.time_left -= 1
        self.timer_label.setText(str(self.time_left))

        if self.time_left <= 0:
            if self.current_phase == "inhale":
                self.current_phase = "hold"
                self.phase_label.setText("💭 Задержка")
                self.time_left = 7

            elif self.current_phase == "hold":
                self.current_phase = "exhale"
                self.phase_label.setText("🌪️ Выдох")
                self.time_left = 8

            elif self.current_phase == "exhale":
                self.cycle_count += 1
                self.counter_label.setText(f"Цикл {self.cycle_count + 1} из {self.max_cycles}")

                if self.cycle_count < self.max_cycles:
                    self.current_phase = "inhale"
                    self.phase_label.setText("🌬️ Вдох")
                    self.time_left = 4
                else:
                    self.finish_exercise()
                    return

            self.timer_label.setText(str(self.time_left))

    def finish_exercise(self):
        """Завершить упражнение"""
        self.timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.phase_label.setText("✅ Завершено!")
        self.timer_label.setText("🎉")
        self.counter_label.setText("Отлично!")

        QMessageBox.information(self, "Молодец!",
                                "✅ Вы успешно выполнили дыхательное упражнение!\n\n"
                                "Регулярная практика помогает снижать тревожность и улучшать самочувствие.")

    def closeEvent(self, event):
        """При закрытии останавливаем таймер"""
        self.timer.stop()
        event.accept()


class MusicButton(QPushButton):
    """Кнопка для вызова музыкального плеера"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("🎵")
        self.setFixedSize(50, 50)
        self.setStyleSheet("""
            QPushButton {
                background-color: #B5E5CF;
                border: 2px solid #9BD1B8;
                border-radius: 25px;
                font-size: 24px;
                color: #2C3E50;
            }
            QPushButton:hover {
                background-color: #9BD1B8;
            }
        """)
        self.music_player = None
        self.clicked.connect(self.show_music_player)

    def show_music_player(self):
        """Показать музыкальный плеер"""
        if not self.music_player:
            self.music_player = SimpleMusicPlayer()  # Без parent!

        if self.music_player.isVisible():
            self.music_player.hide()
        else:
            # Центрируем относительно главного окна
            main_window = self.window()
            if main_window:
                main_rect = main_window.geometry()
                player_rect = self.music_player.geometry()

                x = main_rect.x() + (main_rect.width() - player_rect.width()) // 2
                y = main_rect.y() + (main_rect.height() - player_rect.height()) // 2

                self.music_player.move(x, y)

            self.music_player.show()
            self.music_player.raise_()


if __name__ == '__main__':
    main()