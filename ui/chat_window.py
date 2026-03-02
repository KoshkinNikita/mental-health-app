# ui/chat_window.py
"""Окно чата с ботом"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from ai.mental_health_bot import MentalHealthBot
from ai.sentiment import SentimentAnalyzer


class ChatBotWindow(QWidget):
    """Окно чата с ботом"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.bot = None
        self.current_user = None
        self.sentiment_analyzer = SentimentAnalyzer()
        self.messages = []
        self.init_ui()


    def init_bot(self):
        """Инициализация бота"""
        if self.parent.current_user:
            self.bot = MentalHealthBot(self.parent.db, self.parent.current_user['id'])
            # Добавляем приветствие с именем
            self.add_bot_message(
                f"Привет, {self.parent.current_user['name']}! Я твой душевный помощник 🤗\n\n"
                "Я здесь, чтобы:\n"
                "• Выслушать и поддержать\n"
                "• Предложить упражнения КПТ\n"
                "• Дать мотивирующую цитату\n"
                "• Помочь разобраться в чувствах\n\n"
                "Расскажи, как ты сегодня?"
            )
        else:
            self.bot = MentalHealthBot(self.parent.db)
            self.add_bot_message(
                "Привет! Я твой душевный помощник 🤗\n\n"
                "👤 Войдите в систему, чтобы я мог запоминать нашу историю и давать персонализированные советы!\n\n"
                "А пока я могу:\n"
                "• Дать мотивирующую цитату\n"
                "• Предложить упражнение\n"
                "• Просто поболтать"
            )

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setStyleSheet("""
            QWidget {
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

        history_title = QLabel("📋 История")
        history_title.setProperty("class", "TitleSmall")
        history_layout.addWidget(history_title)

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

        history_layout.addWidget(self.history_list)

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

        parent_layout.addWidget(chat_widget, 1)


    def send_message(self):
        """Отправка сообщения"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return

        self.add_user_message(message)
        self.message_input.clear()

        if self.bot:
            response = self.bot.get_response(message)
            self.add_bot_message(response)

            if self.bot.user_id:
                recommendation = self.bot.get_personalized_recommendation()
                if recommendation:
                    self.add_bot_message(f"💡 *Персональная заметка:* {recommendation}")
        else:
            self.add_bot_message("Извини, я временно недоступен. Попробуй позже!")

    def add_user_message(self, message):
        """Добавление сообщения пользователя"""
        sentiment = self.sentiment_analyzer.analyze_sentiment(message)
        dominant = self.sentiment_analyzer.get_dominant_emotion(sentiment)

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

        self.messages.append({
            'sender': 'user',
            'text': message,
            'time': datetime.now(),
            'sentiment': sentiment
        })

        container = QWidget()
        container.setMaximumWidth(800)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(10, 5, 10, 5)
        container_layout.addStretch()

        message_widget = QFrame()
        message_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        message_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 18px 18px 5px 18px;
                border: 2px solid {border_color};
            }}
        """)

        layout = QVBoxLayout(message_widget)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        text = QLabel(message)
        text.setWordWrap(True)
        text.setMinimumWidth(200)
        text.setMaximumWidth(500)
        text.setStyleSheet("color: #2C3E50; font-size: 14px; font-weight: 500;")
        layout.addWidget(text)

        bottom_frame = QFrame()
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

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
        time_label.setStyleSheet("color: #7F8C8D; font-size: 11px;")
        bottom_layout.addWidget(time_label)

        bottom_layout.addStretch()
        layout.addWidget(bottom_frame)

        container_layout.addWidget(message_widget)

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
        self.scroll_to_bottom()

    def add_bot_message(self, message):
        """Добавление сообщения бота"""
        self.messages.append({
            'sender': 'bot',
            'text': message,
            'time': datetime.now()
        })

        container = QWidget()
        container.setMaximumWidth(800)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(10, 5, 10, 5)

        message_widget = QFrame()
        message_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        message_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 18px 18px 18px 5px;
                border: 2px solid #9BD1B8;
            }
        """)

        layout = QVBoxLayout(message_widget)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        text = QLabel(message)
        text.setWordWrap(True)
        text.setMinimumWidth(200)
        text.setMaximumWidth(500)
        text.setStyleSheet("color: #2C3E50; font-size: 14px; font-weight: 500; line-height: 1.5;")
        layout.addWidget(text)

        bottom_frame = QFrame()
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        bot_icon = QLabel("🤖")
        bot_icon.setStyleSheet("font-size: 14px;")
        bottom_layout.addWidget(bot_icon)

        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setStyleSheet("color: #95A5A6; font-size: 11px;")
        bottom_layout.addWidget(time_label)

        bottom_layout.addStretch()
        layout.addWidget(bottom_frame)

        container_layout.addWidget(message_widget)
        container_layout.addStretch()

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
        self.scroll_to_bottom()

    def get_quote(self):
        """Получить цитату дня"""
        if not self.bot:
            from ai.mental_health_bot import MentalHealthBot
            if self.current_user:
                self.bot = MentalHealthBot(self.parent.db, self.current_user['id'])
            else:
                self.bot = MentalHealthBot(self.parent.db)

        self.add_bot_message(self.bot.get_random_quote())

    def get_random_exercise(self):
        """Получить случайное упражнение"""
        if not self.bot:
            from ai.mental_health_bot import MentalHealthBot
            if self.current_user:
                self.bot = MentalHealthBot(self.parent.db, self.current_user['id'])
            else:
                self.bot = MentalHealthBot(self.parent.db)

        self.add_bot_message(self.bot.suggest_exercise(""))

    def set_current_user(self, user):
        """Обновление пользователя в чате"""
        self.current_user = user
        if user:
            # Если пользователь авторизован, пересоздаем бота с его данными
            from ai.mental_health_bot import MentalHealthBot
            self.bot = MentalHealthBot(self.parent.db, user['id'])

            # Добавляем сообщение о успешном входе
            self.add_bot_message(
                f"✅ Вы вошли как {user['name']}!\n\n"
                f"Теперь я могу:\n"
                f"• Анализировать ваше настроение\n"
                f"• Давать персонализированные советы\n"
                f"• Запоминать нашу историю\n\n"
                f"Чем я могу помочь?"
            )

    def analyze_mood(self):
        """Анализ настроения"""
        if not self.current_user:  # Проверяем current_user, а не parent.current_user
            self.add_bot_message(
                "🔐 **Для анализа настроения нужно войти в систему!**\n\n"
                "Пожалуйста, войдите в свой аккаунт через главное меню."
            )
            return

        if not self.bot:
            from ai.mental_health_bot import MentalHealthBot
            self.bot = MentalHealthBot(self.parent.db, self.current_user['id'])

        # Получаем данные о настроении
        mood_entries = self.parent.db.get_mood_entries(self.current_user['id'], days=7)

        if len(mood_entries) < 3:
            self.add_bot_message(
                "📝 **Пока недостаточно данных для анализа настроения.**\n\n"
                f"У вас всего {len(mood_entries)} отмет(ок) настроения за последние 7 дней.\n\n"
                "Отмечайте своё настроение каждый день в главном меню, "
                "и через неделю я смогу дать подробный анализ!"
            )
            return

        # Рассчитываем статистику
        mood_scores = [e['mood_score'] for e in mood_entries]
        avg_mood = sum(mood_scores) / len(mood_scores)

        # Формируем ответ
        response = f"📊 **Анализ настроения за последние 7 дней**\n\n"
        response += f"📝 Всего отметок: {len(mood_entries)}\n"
        response += f"📈 Среднее настроение: {avg_mood:.1f}/10\n\n"

        if avg_mood >= 7:
            response += "🌟 **Отличный показатель!**\n"
            response += "• Ты хорошо справляешься с эмоциями\n"
            response += "• Продолжай в том же духе\n"
        elif avg_mood >= 5:
            response += "👍 **Стабильное настроение**\n"
            response += "• Есть куда расти, но уже хорошо\n"
            response += "• Попробуй упражнения на осознанность\n"
        else:
            response += "📉 **Настроение ниже среднего**\n"
            response += "• Рекомендую больше отдыхать\n"
            response += "• Попробуй дыхательные упражнения\n"

        # Тренд
        if len(mood_scores) >= 2:
            trend = mood_scores[-1] - mood_scores[0]
            if trend > 1:
                response += "\n📈 **Тренд:** улучшение ↗️\n"
            elif trend < -1:
                response += "\n📉 **Тренд:** ухудшение ↘️\n"
            else:
                response += "\n➡️ **Тренд:** стабильно\n"

        # Рекомендация
        recommendation = self.bot.get_personalized_recommendation()
        if recommendation:
            response += f"\n💡 **Рекомендация:** {recommendation}"

        self.add_bot_message(response)

    def clear_chat(self):
        """Очистка чата"""
        reply = QMessageBox.question(
            self, "Очистка чата",
            "Очистить историю сообщений?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            while self.messages_layout.count() > 1:
                item = self.messages_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self.add_bot_message(
                "Привет! Я твой душевный помощник 🤗\n\n"
                "Расскажи, как ты сегодня?"
            )

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