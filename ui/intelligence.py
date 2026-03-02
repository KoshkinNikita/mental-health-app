# ui/intelligence.py
"""Дашборд интеллектуального анализа"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from ai.predictor import MoodPredictor
from ai.triggers import TriggerIntelligence
from ai.recommender import IntelligentRecommender
from ai.progress import ProgressAnalyzer


class IntelligenceDashboard(QWidget):
    """Дашборд интеллектуального анализа"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.predictor = MoodPredictor(parent.db)
        self.trigger_intel = TriggerIntelligence(parent.db)
        self.recommender = IntelligentRecommender(parent.db)
        self.progress_analyzer = ProgressAnalyzer(parent.db)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Верхняя панель
        self.create_top_bar(layout)

        # Табы
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

        self.create_overview_tab()
        self.create_progress_tab()
        self.create_insights_tab()

        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        layout.addWidget(self.tab_widget)

        # Загружаем данные
        self.load_intelligence_data()

    def on_tab_changed(self, index):
        """Обработчик смены вкладки"""
        if self.parent.current_user:
            user_id = self.parent.current_user['id']
            tab_name = self.tab_widget.tabText(index)

            if "Обзор" in tab_name:
                self.update_overview_tab(user_id)
            elif "Прогресс" in tab_name:
                self.update_progress_tab(user_id)
            elif "Инсайты" in tab_name:
                self.update_insights_tab(user_id)

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

        back_btn = QPushButton("← Назад")
        back_btn.setProperty("class", "SecondaryButton")
        back_btn.clicked.connect(
            lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(1)
        )
        top_layout.addWidget(back_btn)

        top_layout.addStretch()

        title = QLabel("🤖 Интеллектуальный анализ")
        title.setProperty("class", "TitleMedium")
        top_layout.addWidget(title)

        top_layout.addStretch()

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

        self.overview_layout = layout

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
        """Вкладка с инсайтами"""
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

    def load_intelligence_data(self):
        """Загрузка данных"""
        if not self.parent.current_user:
            self.show_no_data_message("Войдите в систему для доступа к анализу")
            return

        user_id = self.parent.current_user['id']

        self.update_overview_tab(user_id)
        self.update_progress_tab(user_id)
        self.update_insights_tab(user_id)

    def show_no_data_message(self, message):
        """Показать сообщение об отсутствии данных"""
        label = QLabel(message)
        label.setProperty("class", "TextSecondary")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("padding: 40px; font-size: 16px;")

        self.overview_layout.addWidget(label)
        self.progress_layout.addWidget(label)
        self.insights_layout.addWidget(label)

    def update_overview_tab(self, user_id):
        """Обновление вкладки обзора"""
        while self.overview_layout.count():
            item = self.overview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        title = QLabel("📊 Общий обзор")
        title.setProperty("class", "TitleMedium")
        self.overview_layout.addWidget(title)

        # Ключевые показатели
        key_card = QFrame()
        key_card.setProperty("class", "MintCard")
        key_layout = QVBoxLayout(key_card)
        key_layout.setContentsMargins(25, 25, 25, 25)
        key_layout.setSpacing(15)

        key_title = QLabel("🔑 Ключевые показатели")
        key_title.setProperty("class", "TitleSmall")
        key_layout.addWidget(key_title)

        try:
            diary_stats = self.parent.db.get_diary_stats(user_id)
            user_stats = self.parent.db.get_user_stats(user_id)
            mood_entries = self.parent.db.get_mood_entries(user_id, days=30)

            if diary_stats and user_stats:
                # Всего записей
                total_frame = QFrame()
                total_layout = QHBoxLayout(total_frame)
                total_label = QLabel("📝 Всего записей:")
                total_label.setProperty("class", "TextRegular")
                total_layout.addWidget(total_label)
                total_layout.addStretch()
                total_value = QLabel(str(diary_stats.get('total_entries', 0)))
                total_value.setStyleSheet("font-weight: bold; font-size: 16px;")
                total_layout.addWidget(total_value)
                key_layout.addWidget(total_frame)

                # Дней подряд
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

                # Среднее настроение
                if mood_entries:
                    mood_scores = [e['mood_score'] for e in mood_entries if e['mood_score'] > 0]
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

                # Частое искажение
                distortions = diary_stats.get('common_distortions', {})
                if distortions:
                    most_common = max(distortions.items(), key=lambda x: x[1])
                    dist_frame = QFrame()
                    dist_layout = QHBoxLayout(dist_frame)
                    dist_label = QLabel("🧠 Частое искажение:")
                    dist_label.setProperty("class", "TextRegular")
                    dist_layout.addWidget(dist_label)
                    dist_layout.addStretch()
                    dist_value = QLabel(f"{most_common[0]} ({most_common[1]} раз)")
                    dist_value.setStyleSheet("font-weight: bold; font-size: 16px;")
                    dist_layout.addWidget(dist_value)
                    key_layout.addWidget(dist_frame)
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

        self.overview_layout.addWidget(key_card)
        self.overview_layout.addStretch()

    def update_progress_tab(self, user_id):
        """Обновление вкладки прогресса"""
        while self.progress_layout.count():
            item = self.progress_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        title = QLabel("📈 Анализ прогресса")
        title.setProperty("class", "TitleMedium")
        self.progress_layout.addWidget(title)

        try:
            progress_data = self.progress_analyzer.analyze_progress_trends(user_id)

            if not progress_data.get('has_data'):
                no_data = QLabel("Недостаточно данных для анализа прогресса")
                no_data.setProperty("class", "TextSecondary")
                no_data.setAlignment(Qt.AlignCenter)
                self.progress_layout.addWidget(no_data)
                self.progress_layout.addStretch()
                return

            # Карточка прогресса
            score_card = QFrame()
            score_card.setProperty("class", "WarmCard")
            score_layout = QVBoxLayout(score_card)
            score_layout.setContentsMargins(25, 25, 25, 25)
            score_layout.setSpacing(15)

            score_title = QLabel("🎯 Общий балл прогресса")
            score_title.setProperty("class", "TitleSmall")
            score_layout.addWidget(score_title)

            progress_frame = QFrame()
            progress_layout_inner = QVBoxLayout(progress_frame)
            progress_layout_inner.setAlignment(Qt.AlignCenter)

            progress_value = progress_data.get('progress_score', 0)
            progress_level = progress_data.get('progress_level', 'Новичок')

            score_label = QLabel(f"{progress_value}/100")
            score_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #5A5A5A;")
            score_label.setAlignment(Qt.AlignCenter)
            progress_layout_inner.addWidget(score_label)

            level_label = QLabel(f"Уровень: {progress_level}")
            level_label.setProperty("class", "TextRegular")
            level_label.setAlignment(Qt.AlignCenter)
            progress_layout_inner.addWidget(level_label)

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

                for goal in progress_data['goals_achieved'][:5]:
                    goal_label = QLabel(f"• {goal}")
                    goal_label.setProperty("class", "TextRegular")
                    goal_label.setWordWrap(True)
                    goals_layout.addWidget(goal_label)

                self.progress_layout.addWidget(goals_card)

            # Области для улучшения
            if progress_data.get('areas_for_improvement'):
                improve_card = QFrame()
                improve_card.setProperty("class", "MintCard")
                improve_layout = QVBoxLayout(improve_card)
                improve_layout.setContentsMargins(25, 25, 25, 25)
                improve_layout.setSpacing(15)

                improve_title = QLabel("💡 Области для улучшения")
                improve_title.setProperty("class", "TitleSmall")
                improve_layout.addWidget(improve_title)

                for area in progress_data['areas_for_improvement'][:3]:
                    area_label = QLabel(f"• {area}")
                    area_label.setProperty("class", "TextRegular")
                    area_label.setWordWrap(True)
                    improve_layout.addWidget(area_label)

                self.progress_layout.addWidget(improve_card)

        except Exception as e:
            print(f"Ошибка обновления прогресса: {e}")
            error_label = QLabel("Ошибка загрузки данных прогресса")
            error_label.setProperty("class", "TextSecondary")
            error_label.setAlignment(Qt.AlignCenter)
            self.progress_layout.addWidget(error_label)

        self.progress_layout.addStretch()

    def update_insights_tab(self, user_id):
        """Обновление вкладки инсайтов"""
        while self.insights_layout.count():
            item = self.insights_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        title = QLabel("💡 Персонализированные инсайты")
        title.setProperty("class", "TitleMedium")
        self.insights_layout.addWidget(title)

        try:
            recommendations = self.recommender.generate_personalized_recommendations(user_id)

            if not recommendations:
                no_data = QLabel("Недостаточно данных для генерации инсайтов")
                no_data.setProperty("class", "TextSecondary")
                no_data.setAlignment(Qt.AlignCenter)
                self.insights_layout.addWidget(no_data)
                self.insights_layout.addStretch()
                return

            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            recommendations.sort(key=lambda x: priority_order[x.get('priority', 'medium')])

            for i, rec in enumerate(recommendations[:5], 1):
                rec_card = QFrame()

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

                header_frame = QFrame()
                header_layout = QHBoxLayout(header_frame)
                header_layout.setContentsMargins(0, 0, 0, 0)

                rec_title = QLabel(f"{i}. {rec.get('title', 'Рекомендация')}")
                rec_title.setStyleSheet("font-weight: bold; font-size: 16px;")
                header_layout.addWidget(rec_title)
                header_layout.addStretch()

                priority_icon = "🔴" if rec.get('priority') == 'high' else "🟡" if rec.get(
                    'priority') == 'medium' else "🟢"
                priority_label = QLabel(priority_icon)
                header_layout.addWidget(priority_label)

                rec_layout.addWidget(header_frame)

                rec_desc = QLabel(rec.get('description', ''))
                rec_desc.setProperty("class", "TextRegular")
                rec_desc.setWordWrap(True)
                rec_layout.addWidget(rec_desc)

                if rec.get('category'):
                    category_frame = QFrame()
                    category_layout = QHBoxLayout(category_frame)
                    category_layout.setContentsMargins(0, 0, 0, 0)
                    category_label = QLabel(f"🏷️ {rec.get('category')}")
                    category_label.setProperty("class", "TextLight")
                    category_layout.addWidget(category_label)
                    category_layout.addStretch()
                    rec_layout.addWidget(category_frame)

                if rec.get('exercises'):
                    exercises_label = QLabel(f"💪 Упражнения: {', '.join(rec['exercises'][:2])}")
                    exercises_label.setProperty("class", "TextSecondary")
                    exercises_label.setWordWrap(True)
                    rec_layout.addWidget(exercises_label)

                self.insights_layout.addWidget(rec_card)

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

                trend_icon = "📈" if prediction['trend'] == 'повышательный' else "📉" if prediction[
                                                                                           'trend'] == 'понижательный' else "➡️"
                trend_label = QLabel(f"Тренд: {trend_icon} {prediction['trend']}")
                trend_label.setProperty("class", "TextRegular")
                forecast_layout.addWidget(trend_label)

                if prediction.get('predictions'):
                    days = ['Сегодня', 'Завтра', 'Послезавтра']

                    for i, (day, pred) in enumerate(zip(days[:3], prediction['predictions'][:3])):
                        day_frame = QFrame()
                        day_layout = QHBoxLayout(day_frame)
                        day_layout.setContentsMargins(0, 0, 0, 0)

                        day_label = QLabel(day)
                        day_label.setFixedWidth(100)
                        day_layout.addWidget(day_label)

                        mood_icon = "😊" if pred >= 7 else "😐" if pred >= 5 else "😔"
                        mood_label = QLabel(f"{mood_icon} {pred:.1f}/10")
                        mood_label.setStyleSheet("font-weight: bold;")
                        day_layout.addWidget(mood_label)

                        forecast_layout.addWidget(day_frame)

                if prediction.get('recommendation'):
                    rec_label = QLabel(f"💡 {prediction['recommendation']}")
                    rec_label.setProperty("class", "TextSecondary")
                    rec_label.setWordWrap(True)
                    forecast_layout.addWidget(rec_label)

                self.insights_layout.addWidget(forecast_card)

        except Exception as e:
            print(f"Ошибка прогноза настроения: {e}")