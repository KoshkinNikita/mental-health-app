# widgets/dna_visualization.py
"""Виджет для визуализации ДНК профиля"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class DNAVisualizationWidget(QWidget):
    """Виджет для визуализации ДНК профиля"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        title = QLabel("🧬 Ваш профиль ментального здоровья")
        title.setProperty("class", "TitleMedium")
        layout.addWidget(title)

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

        self._render_summary()
        self._render_thinking_patterns()
        self._render_emotional_landscape()
        self._render_triggers()
        self._render_recommendations()

    def _render_summary(self):
        card = QFrame()
        card.setProperty("class", "MintCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        date_str = datetime.fromisoformat(self.profile['generated_at']).strftime("%d.%m.%Y")
        title = QLabel(f"Профиль от {date_str}")
        title.setProperty("class", "TitleSmall")
        layout.addWidget(title)

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

        for pattern, data in patterns.items():
            pattern_frame = QFrame()
            pattern_layout = QVBoxLayout(pattern_frame)
            pattern_layout.setSpacing(5)

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

            desc_label = QLabel(data['description'])
            desc_label.setProperty("class", "TextSecondary")
            desc_label.setWordWrap(True)
            pattern_layout.addWidget(desc_label)

            if data.get('typical_situations'):
                examples_label = QLabel("Примеры: " + ", ".join(data['typical_situations'][:2]))
                examples_label.setProperty("class", "TextLight")
                examples_label.setWordWrap(True)
                pattern_layout.addWidget(examples_label)

            layout.addWidget(pattern_frame)

        self.content_layout.addWidget(card)

    def _render_emotional_landscape(self):
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

            intensity_label = QLabel(f"Интенсивность: {data['avg_intensity']}/100 ({data['strength']})")
            intensity_label.setProperty("class", "TextSecondary")
            emotion_layout.addWidget(intensity_label)

            layout.addWidget(emotion_frame)

        self.content_layout.addWidget(card)

    def _render_triggers(self):
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

            if 'main_emotion' in data:
                emotion_label = QLabel(
                    f"Основная эмоция: {data['main_emotion']['name']} ({data['main_emotion']['intensity']}%)")
                emotion_label.setProperty("class", "TextSecondary")
                trigger_layout.addWidget(emotion_label)

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

                priority_color = "#FF6B6B" if rec['priority'] == 'high' else "#FFD166" if rec[
                                                                                              'priority'] == 'medium' else "#06D6A0"

                rec_frame.setStyleSheet(f"""
                    QFrame {{
                        border-left: 4px solid {priority_color};
                        padding-left: 10px;
                    }}
                """)

                title_label = QLabel(f"{i}. {rec['title']}")
                title_label.setStyleSheet("font-weight: bold; font-size: 15px;")
                rec_layout.addWidget(title_label)

                desc_label = QLabel(rec['description'])
                desc_label.setProperty("class", "TextRegular")
                desc_label.setWordWrap(True)
                rec_layout.addWidget(desc_label)

                if rec.get('exercises'):
                    exercises_label = QLabel("💡 Упражнения: " + ", ".join(rec['exercises']))
                    exercises_label.setProperty("class", "TextSecondary")
                    exercises_label.setWordWrap(True)
                    rec_layout.addWidget(exercises_label)

                layout.addWidget(rec_frame)

        self.content_layout.addWidget(card)