# ui/main_menu.py
"""Главное меню приложения"""

import sys
import os
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from widgets.animated import AnimatedButton
from widgets.mood_button import MoodButton
from widgets.mood_chart import MoodChartWidget

class MainMenuWindow(QWidget):
    """Главное меню приложения"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_user = None
        self.mood_buttons = []
        self.welcome_label = None
        self.user_info_label = None
        self.logout_btn = None
        self.stats_widgets = {}
        self.init_ui()

    def set_current_user(self, user):
        """Установка текущего пользователя"""
        self.current_user = user
        self.update_display()
        self.update_user_info()

        if hasattr(self.parent, 'chat_window'):
            self.parent.chat_window.set_current_user(user)

    def update_display(self):
        """Обновление отображения главного меню"""
        try:
            if not self.current_user:
                name = "Гость"
                if self.welcome_label:
                    self.welcome_label.setText(f"Добро пожаловать, {name}! 🌼")
                return

            name = self.current_user.get('name', 'Пользователь')
            if self.welcome_label:
                self.welcome_label.setText(f"Добро пожаловать, {name}! 🌼")

            self.update_mood_display()
            self.update_chart_data()
            self.update_stats_section()
            self.update_insights()

        except Exception as e:
            print(f"Ошибка обновления отображения: {e}")

    def update_user_info(self):
        """Обновление информации о пользователе"""
        try:
            if self.user_info_label:
                if self.current_user:
                    name = self.current_user.get('name', 'Пользователь')
                    self.user_info_label.setText(f"👤 {name}")
                    self.user_info_label.setProperty("class", "TextRegular")
                    if self.logout_btn:
                        self.logout_btn.setVisible(True)
                else:
                    self.user_info_label.setText("👤 Гость")
                    self.user_info_label.setProperty("class", "TextLight")
                    if self.logout_btn:
                        self.logout_btn.setVisible(False)
        except Exception as e:
            print(f"Ошибка обновления информации: {e}")

    def update_mood_display(self):
        """Обновление отображения настроения"""
        try:
            if not self.current_user:
                for btn in self.mood_buttons:
                    btn.setChecked(False)
                return

            today_mood = self.parent.db.get_today_mood(self.current_user['id'])

            for btn in self.mood_buttons:
                btn.setChecked(False)

            if today_mood and 1 <= today_mood <= 10:
                self.mood_buttons[today_mood - 1].setChecked(True)
        except Exception as e:
            print(f"Ошибка обновления настроения: {e}")

    def update_chart_data(self):
        """Обновление данных графика"""
        try:
            if not self.current_user or not hasattr(self, 'mood_chart'):
                return

            entries = self.parent.db.get_mood_entries(self.current_user['id'], days=7)

            if entries:
                self.mood_chart.update_with_real_data(entries)
            else:
                self.mood_chart.generate_sample_data()
                self.mood_chart.plot_chart()
        except Exception as e:
            print(f"Ошибка обновления графика: {e}")

    def update_insights(self):
        """Обновление карточки с инсайтами"""
        try:
            if hasattr(self, 'insights_card'):
                insights = self.generate_insights()

                layout = self.insights_card.layout()
                if layout:
                    while layout.count() > 1:
                        item = layout.takeAt(1)
                        if item.widget():
                            item.widget().deleteLater()

                    for insight in insights:
                        insight_frame = QFrame()
                        insight_layout = QHBoxLayout(insight_frame)
                        insight_layout.setContentsMargins(0, 0, 0, 0)
                        insight_layout.setSpacing(10)

                        icon = QLabel("✨")
                        icon.setStyleSheet("font-size: 16px;")
                        insight_layout.addWidget(icon)

                        text_label = QLabel(insight)
                        text_label.setProperty("class", "TextRegular")
                        text_label.setWordWrap(True)
                        insight_layout.addWidget(text_label, 1)

                        layout.addWidget(insight_frame)
        except Exception as e:
            print(f"Ошибка обновления инсайтов: {e}")

    def generate_insights(self):
        """Генерация персональных инсайтов"""
        if not self.current_user:
            return [
                "Войдите в систему, чтобы увидеть персональные инсайты",
                "Регулярное ведение дневника помогает отслеживать прогресс",
                "Начните с записи сегодняшнего настроения"
            ]

        try:
            mood_entries = self.parent.db.get_mood_entries(self.current_user['id'], days=7)
            diary_stats = self.parent.db.get_diary_stats(self.current_user['id'])

            insights = []

            if mood_entries and len(mood_entries) > 1:
                mood_scores = [entry['mood_score'] for entry in mood_entries]
                avg_mood = sum(mood_scores) / len(mood_scores)

                if avg_mood > 7:
                    insights.append(f"Ваше среднее настроение: {avg_mood:.1f}/10 - отличный результат! 🌟")
                elif avg_mood > 5:
                    insights.append(f"Ваше среднее настроение: {avg_mood:.1f}/10 - хороший уровень 👍")
                else:
                    insights.append(f"Ваше среднее настроение: {avg_mood:.1f}/10 - попробуйте упражнения")

                if len(mood_scores) >= 2:
                    trend = mood_scores[-1] - mood_scores[0]
                    if trend > 1:
                        insights.append("Настроение улучшается - продолжайте! ↗️")
                    elif trend < -1:
                        insights.append("Заметили спад настроения - отдохните 📉")

            if diary_stats['total_entries'] > 0:
                insights.append(f"Вы сделали {diary_stats['total_entries']} записей! 📝")

                if diary_stats['common_distortions']:
                    most_common = max(diary_stats['common_distortions'].items(), key=lambda x: x[1])
                    insights.append(f"Частое искажение: {most_common[0]} ({most_common[1]} раз)")

            if not insights:
                insights = [
                    "Начните вести дневник для получения инсайтов",
                    "Отмечайте настроение каждый день",
                    "Попробуйте упражнения КПТ"
                ]

            return insights[:3]

        except Exception as e:
            print(f"Ошибка генерации инсайтов: {e}")
            return [
                "Анализ данных временно недоступен",
                "Продолжайте использовать приложение",
                "Ваши данные сохраняются безопасно"
            ]

    def update_stats_section(self):
        """Обновление статистики"""
        try:
            if not self.current_user or not self.stats_widgets:
                return

            user_id = self.current_user['id']
            diary_stats = self.parent.db.get_diary_stats(user_id)
            user_stats = self.parent.db.get_user_stats(user_id)

            if not diary_stats or not user_stats:
                return

            if 'total_entries' in self.stats_widgets:
                self.stats_widgets['total_entries'].setText(str(diary_stats.get('total_entries', 0)))

            if 'streak_days' in self.stats_widgets:
                self.stats_widgets['streak_days'].setText(str(user_stats.get('streak_days', 0)))

        except Exception as e:
            print(f"Ошибка обновления статистики: {e}")

    def init_ui(self):
        """Инициализация интерфейса"""
        # Создаем график настроения
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
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        main_layout.addWidget(scroll_area)

        # Контент
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(30)
        content_layout.setContentsMargins(40, 30, 40, 40)

        self.create_welcome_section(content_layout)
        self.create_quick_actions(content_layout)
        self.create_main_functions(content_layout)
        self.create_bottom_section(content_layout)

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

        self.user_info_label = QLabel("👤 Гость")
        self.user_info_label.setProperty("class", "TextRegular")
        top_layout.addWidget(self.user_info_label)

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

        self.logout_btn = QPushButton("Выйти")
        self.logout_btn.setProperty("class", "SecondaryButton")
        self.logout_btn.clicked.connect(self.logout)
        top_layout.addWidget(self.logout_btn)

        parent_layout.addWidget(top_bar)

    def logout(self):
        """Выход из аккаунта"""
        try:
            self.parent.set_current_user(None)
            self.parent.stacked_widget.setCurrentIndexWithAnimation(0)
        except Exception as e:
            print(f"Ошибка выхода: {e}")

    def resizeEvent(self, event):
        """Обновление при изменении размера"""
        super().resizeEvent(event)
        # Обновляем размеры графиков и карточек при необходимости
        if hasattr(self, 'mood_chart'):
            self.mood_chart.setFixedHeight(300)

    def create_welcome_section(self, parent_layout):
        """Создание секции приветствия"""
        welcome_frame = QFrame()
        welcome_frame.setStyleSheet("background-color: transparent;")

        welcome_layout = QVBoxLayout(welcome_frame)
        welcome_layout.setSpacing(15)

        name = "Гость" if not self.current_user else self.current_user.get('name', 'Пользователь')
        self.welcome_label = QLabel(f"Добро пожаловать, {name}! 🌼")
        self.welcome_label.setProperty("class", "TitleLarge")
        welcome_layout.addWidget(self.welcome_label)

        date_label = QLabel(datetime.now().strftime("%d %B %Y"))
        date_label.setProperty("class", "TextSecondary")
        welcome_layout.addWidget(date_label)

        welcome_layout.addWidget(self.mood_chart)
        welcome_layout.addWidget(self.create_mood_card())
        welcome_layout.addWidget(self.create_insights_card())

        parent_layout.addWidget(welcome_frame)

    def create_mood_card(self):
        """Создание карточки выбора настроения"""
        card = QFrame()
        card.setProperty("class", "WarmCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(20)

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

        scale_widget = self.create_mood_scale()
        card_layout.addWidget(scale_widget)

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

        circles_frame = QFrame()
        circles_layout = QHBoxLayout(circles_frame)
        circles_layout.setSpacing(8)
        circles_layout.setAlignment(Qt.AlignCenter)

        self.mood_buttons = []
        for i in range(10):
            btn = MoodButton(i + 1, self)
            btn.setFixedSize(42, 42)
            circles_layout.addWidget(btn)
            self.mood_buttons.append(btn)

        layout.addWidget(circles_frame)

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

        title = QLabel("🚀 Быстрые действия")
        title.setProperty("class", "TitleMedium")
        layout.addWidget(title)

        actions_frame = QFrame()
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setSpacing(20)

        actions = [
            ("📝", "Новая запись", lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(2)),
            ("😊", "Настроение", lambda: self.show_message("Выберите настроение выше")),
            ("🌬️", "Дыхание", self.open_breathing_exercise),
            ("🎵", "Музыка", self.open_music_player),
            ("📊", "Статистика", lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(4)),
        ]

        for emoji, text, callback in actions:
            action_card = self.create_action_card(emoji, text, callback)
            actions_layout.addWidget(action_card)

        layout.addWidget(actions_frame)
        parent_layout.addWidget(frame)

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

        title = QLabel("📋 Основные функции")
        title.setProperty("class", "TitleMedium")
        layout.addWidget(title)

        functions = [
            ("Дневник мыслей", "Запись и анализ автоматических мыслей", "#B5E5CF",
             lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(2)),
            ("Упражнения КПТ", "Практики для работы с эмоциями", "#FFD6DC",
             lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(3)),
            ("История записей", "Просмотр вашего прогресса", "#FFB38E",
             lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(4)),
            ("Достижения", "Ваш прогресс и награды", "#FFD166",
             lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(5)),
            ("🤖 Интеллектуальный анализ", "Глубокий анализ и прогнозы", "#9B59B6", self.open_intelligence_dashboard),
            ("🧬 Профиль здоровья", "Ваш индивидуальный профиль ментального здоровья", "#9B59B6", self.open_dna_profile),
            ("💬 Душевный помощник", "Поговори с поддерживающим ботом", "#9B59B6", self.open_chat_bot),
        ]

        for func_title, description, color, callback in functions:
            func_card = self.create_function_card(func_title, description, color, callback)
            layout.addWidget(func_card)

        parent_layout.addWidget(frame)

    def create_function_card(self, title, description, color, callback):
        """Создание карточки функции"""
        card = AnimatedButton(title, parent=self)
        card.setCursor(Qt.PointingHandCursor)
        card.clicked.connect(callback)

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
            }}
            AnimatedButton:hover {{
                background-color: #F8F2E9;
                border-left: 8px solid {self.darken_color(color)};
            }}
        """)

        layout = QHBoxLayout(card)
        layout.setSpacing(20)

        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #5A5A5A;")
        text_layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 14px; color: #8B7355;")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)

        layout.addWidget(text_widget, 1)

        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("font-size: 28px; color: #C4B6A6; font-weight: bold;")
        layout.addWidget(arrow_label)

        card.setFixedHeight(120)
        return card

    def create_insights_card(self):
        """Карточка с инсайтами"""
        self.insights_card = QFrame()
        self.insights_card.setProperty("class", "SoftPinkCard")

        layout = QVBoxLayout(self.insights_card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

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

        return self.insights_card

    def create_bottom_section(self, parent_layout):
        """Создание нижней секции"""
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

        # Правая колонка - статистика
        right_column = QFrame()
        right_column.setStyleSheet("background-color: transparent;")
        right_layout = QVBoxLayout(right_column)
        right_layout.setSpacing(20)

        self.stats_card = QFrame()
        self.stats_card.setProperty("class", "WarmCard")

        stats_layout = QVBoxLayout(self.stats_card)
        stats_layout.setContentsMargins(25, 25, 25, 25)
        stats_layout.setSpacing(20)

        stats_title = QLabel("📊 Ваша статистика")
        stats_title.setProperty("class", "TitleSmall")
        stats_layout.addWidget(stats_title)

        stats_data = [
            ("Дней подряд", "streak_days", "0"),
            ("Всего записей", "total_entries", "0"),
        ]

        for label_text, key, default_value in stats_data:
            stat_frame = QFrame()
            stat_layout = QHBoxLayout(stat_frame)
            stat_layout.setContentsMargins(0, 0, 0, 0)

            label_widget = QLabel(label_text)
            label_widget.setProperty("class", "TextSecondary")
            stat_layout.addWidget(label_widget)

            stat_layout.addStretch()

            value_widget = QLabel(default_value)
            value_widget.setStyleSheet("font-size: 16px; font-weight: bold; color: #5A5A5A;")
            stat_layout.addWidget(value_widget)

            self.stats_widgets[key] = value_widget
            stats_layout.addWidget(stat_frame)

        right_layout.addWidget(self.stats_card)

        help_btn = QPushButton("💝 Мне нужна поддержка")
        help_btn.setProperty("class", "EmergencyButton")
        help_btn.setMinimumHeight(60)
        help_btn.clicked.connect(self.show_emergency_help)
        right_layout.addWidget(help_btn)

        layout.addWidget(right_column)
        parent_layout.addWidget(frame)

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

    def open_dna_profile(self):
        """Открытие окна профиля ДНК"""
        try:
            if not self.parent.current_user:
                QMessageBox.warning(self, "Ошибка", "Войдите в систему для доступа к профилю ДНК")
                return

            if not hasattr(self.parent, 'dna_window'):
                from ui.dna_profile import DNAProfileWindow
                self.parent.dna_window = DNAProfileWindow(self.parent)
                self.parent.stacked_widget.addWidget(self.parent.dna_window)

            self.parent.dna_window.update_profile()
            index = self.parent.stacked_widget.indexOf(self.parent.dna_window)
            self.parent.stacked_widget.setCurrentIndexWithAnimation(index)

        except Exception as e:
            print(f"Ошибка при открытии профиля ДНК: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть профиль ДНК")

    def open_chat_bot(self):
        """Открыть чат с ботом"""
        try:
            if not hasattr(self.parent, 'chat_window'):
                from ui.chat_window import ChatBotWindow
                self.parent.chat_window = ChatBotWindow(self.parent)
                self.parent.stacked_widget.addWidget(self.parent.chat_window)

            index = self.parent.stacked_widget.indexOf(self.parent.chat_window)
            self.parent.stacked_widget.setCurrentIndexWithAnimation(index)

        except Exception as e:
            print(f"Ошибка при открытии чата: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть чат")

    def open_breathing_exercise(self):
        """Открыть дыхательное упражнение"""
        try:
            from widgets.breathing import SimpleBreathingExercise
            if not hasattr(self.parent, 'breathing_window'):
                self.parent.breathing_window = SimpleBreathingExercise(self.parent)
            self.parent.breathing_window.show()
        except Exception as e:
            print(f"Ошибка открытия дыхательного упражнения: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть упражнение")

    def open_music_player(self):
        """Открыть музыкальный плеер"""
        try:
            from widgets.music_player import MusicButton
            if not hasattr(self, 'music_btn'):
                self.music_btn = MusicButton(self)
            self.music_btn.show_music_player()
        except Exception as e:
            print(f"Ошибка открытия музыкального плеера: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть музыкальный плеер")

    def darken_color(self, color):
        """Затемнить цвет"""
        colors = {
            "#B5E5CF": "#9BD1B8",
            "#FFD6DC": "#FFC8D6",
            "#FFB38E": "#FF9E70",
            "#E8DFD8": "#D7CCC8",
        }
        return colors.get(color, color)

    def show_success_message(self, text):
        """Показать успешное сообщение"""
        QMessageBox.information(self, "Успешно", text)

    def show_message(self, text):
        """Показать информационное сообщение"""
        QMessageBox.information(self, "Информация", text)

    def open_intelligence_dashboard(self):
        """Открытие интеллектуального анализа"""
        try:
            if not self.parent.current_user:
                QMessageBox.warning(self, "Ошибка", "Войдите в систему для доступа к анализу")
                return

            if hasattr(self.parent, 'intelligence_window'):
                self.parent.intelligence_window.load_intelligence_data()
                index = self.parent.stacked_widget.indexOf(self.parent.intelligence_window)
                self.parent.stacked_widget.setCurrentIndexWithAnimation(index)
        except Exception as e:
            print(f"Ошибка при открытии интеллектуального анализа: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть интеллектуальный анализ")

    def show_emergency_help(self):
        """Показать экстренную помощь"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Поддержка здесь")
        msg_box.setText("""
            <h3>💝 Если вам прямо сейчас тяжело:</h3>
            <p>1. <b>🌬 Сделайте 3 глубоких вдоха</b><br>
            Вдох на 4, задержка на 4, выдох на 6</p>

            <p>2. <b>📞 Позвоните на горячую линию</b><br>
            8-800-2000-122 (бесплатно по России)</p>

            <p>3. <b>🌿 Найдите 5 вещей вокруг вас</b><br>
            5 вещей, которые видите<br>
            4 вещи, которые чувствуете<br>
            3 звука, которые слышите</p>

            <p><i>Обращение за помощью — это признак силы.</i></p>
        """)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()