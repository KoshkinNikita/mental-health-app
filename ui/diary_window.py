# ui/diary_window.py
"""Окно дневника мыслей"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class DiaryWindow(QWidget):
    """Окно дневника мыслей"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_user = None
        self.similarity_analyzer = None
        self.pause_timer = None
        self.notification_widget = None
        self.init_ui()

    def set_current_user(self, user):
        """Установка текущего пользователя"""
        self.current_user = user

    def init_ui(self):
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Верхняя панель
        self.create_top_bar(main_layout)

        # Прокручиваемая область
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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

        # Информационная карточка
        info_card = self.create_info_card()
        content_layout.addWidget(info_card)

        # Форма записи
        form_card = self.create_diary_form()
        content_layout.addWidget(form_card)

        # Виджет для уведомлений (скрытый)
        self.notification_widget = self.create_notification_widget()
        content_layout.addWidget(self.notification_widget)

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

        back_btn = QPushButton("← Назад")
        back_btn.setProperty("class", "SecondaryButton")
        back_btn.clicked.connect(
            lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(1)
        )
        top_layout.addWidget(back_btn)

        top_layout.addStretch()

        title = QLabel("Дневник мыслей")
        title.setProperty("class", "TitleMedium")
        top_layout.addWidget(title)

        top_layout.addStretch()

        save_btn = QPushButton("💾 Сохранить")
        save_btn.setProperty("class", "PrimaryButton")
        save_btn.clicked.connect(self.save_entry)
        top_layout.addWidget(save_btn)

        parent_layout.addWidget(top_bar)

    def create_info_card(self):
        """Карточка с информацией о КПТ"""
        card = QFrame()
        card.setProperty("class", "WarmCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel("🤔 Что такое автоматические мысли?")
        title.setProperty("class", "TitleSmall")
        layout.addWidget(title)

        description = QLabel(
            "Автоматические мысли — это быстрые, мимолетные мысли, которые возникают "
            "в ответ на события. Они часто бывают искаженными и влияют на наши эмоции и поведение. "
            "В КПТ мы учимся распознавать и анализировать эти мысли."
        )
        description.setProperty("class", "TextRegular")
        description.setWordWrap(True)
        layout.addWidget(description)

        return card

    def create_notification_widget(self):
        """Создание виджета для уведомлений"""
        widget = QFrame()
        widget.setProperty("class", "MintCard")
        widget.setVisible(False)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Заголовок
        title_frame = QFrame()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)

        icon = QLabel("💡")
        icon.setStyleSheet("font-size: 20px;")
        title_layout.addWidget(icon)

        title = QLabel("Найдены похожие ситуации")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #C4B6A6;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #FF6B6B;
            }
        """)
        close_btn.clicked.connect(lambda: widget.setVisible(False))
        title_layout.addWidget(close_btn)

        layout.addWidget(title_frame)

        # Контейнер для списка похожих
        self.notification_list = QVBoxLayout()
        layout.addLayout(self.notification_list)

        # Кнопка "Показать все"
        show_all_btn = QPushButton("🔍 Показать все похожие")
        show_all_btn.setProperty("class", "SecondaryButton")
        show_all_btn.setFixedHeight(30)
        show_all_btn.clicked.connect(self.show_all_similar)
        layout.addWidget(show_all_btn)

        return widget

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
        self.situation_input.textChanged.connect(self.on_situation_changed)
        self.situation_input.setPlaceholderText("Опишите ситуацию, которая вызвала эмоциональную реакцию...")
        self.situation_input.setMaximumHeight(100)
        layout.addWidget(self.situation_input)

        help_button = QPushButton("💡 Нужна подсказка?")
        help_button.setProperty("class", "SecondaryButton")
        help_button.clicked.connect(self.find_similar_situations)
        layout.addWidget(help_button)

        # Эмоции
        emotions_label = QLabel("2. Эмоции и их интенсивность (0-100%):")
        emotions_label.setProperty("class", "TextRegular")
        emotions_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(emotions_label)

        emotions_frame = QFrame()
        emotions_layout = QVBoxLayout(emotions_frame)
        emotions_layout.setSpacing(10)

        emotions = ["Тревога", "Грусть", "Гнев", "Стыд", "Радость"]
        self.emotion_inputs = {}

        for emotion in emotions:
            emotion_frame = QFrame()
            emotion_layout = QHBoxLayout(emotion_frame)
            emotion_layout.setContentsMargins(0, 0, 0, 0)

            emotion_label = QLabel(f"{emotion}:")
            emotion_label.setProperty("class", "TextRegular")
            emotion_label.setFixedWidth(100)
            emotion_layout.addWidget(emotion_label)

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

            value_label = QLabel("0%")
            value_label.setProperty("class", "TextRegular")
            value_label.setFixedWidth(40)
            emotion_layout.addWidget(value_label)

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
        self.thoughts_input.setPlaceholderText("Запишите мысли, которые пришли в голову...")
        self.thoughts_input.setMaximumHeight(100)
        layout.addWidget(self.thoughts_input)

        # Когнитивные искажения
        distortions_label = QLabel("4. Возможные когнитивные искажения:")
        distortions_label.setProperty("class", "TextRegular")
        distortions_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(distortions_label)

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
        self.alternative_input.setPlaceholderText("Попробуйте найти более сбалансированный взгляд...")
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

        title = QLabel("📚 Примеры записей:")
        title.setProperty("class", "TitleSmall")
        layout.addWidget(title)

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

            sit_label = QLabel(f"<b>Ситуация:</b> {example['situation']}")
            sit_label.setProperty("class", "TextRegular")
            sit_label.setTextFormat(Qt.RichText)
            sit_label.setWordWrap(True)
            example_layout.addWidget(sit_label)

            emo_label = QLabel(f"<b>Эмоции:</b> {example['emotions']}")
            emo_label.setProperty("class", "TextRegular")
            emo_label.setTextFormat(Qt.RichText)
            example_layout.addWidget(emo_label)

            th_label = QLabel(f"<b>Мысль:</b> {example['thought']}")
            th_label.setProperty("class", "TextRegular")
            th_label.setTextFormat(Qt.RichText)
            th_label.setWordWrap(True)
            example_layout.addWidget(th_label)

            dis_label = QLabel(f"<b>Искажения:</b> {example['distortion']}")
            dis_label.setProperty("class", "TextRegular")
            dis_label.setTextFormat(Qt.RichText)
            example_layout.addWidget(dis_label)

            alt_label = QLabel(f"<b>Альтернатива:</b> {example['alternative']}")
            alt_label.setProperty("class", "TextRegular")
            alt_label.setTextFormat(Qt.RichText)
            alt_label.setWordWrap(True)
            example_layout.addWidget(alt_label)

            layout.addWidget(example_frame)

            if i < len(examples):
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setStyleSheet("background-color: rgba(155, 209, 184, 0.5);")
                separator.setFixedHeight(1)
                layout.addWidget(separator)

        return card

    # ==================== ПОИСК ПОХОЖИХ СИТУАЦИЙ ====================

    def find_similar_situations(self):
        """Поиск похожих ситуаций по кнопке"""
        situation = self.situation_input.toPlainText().strip()

        if len(situation) < 20:
            QMessageBox.information(self, "Подсказка",
                                    "Опишите ситуацию подробнее (минимум 20 символов)")
            return

        from ai.similarity_analyzer import SimilarityAnalyzer
        if not self.similarity_analyzer:
            self.similarity_analyzer = SimilarityAnalyzer(self.parent.db)

        similar = self.similarity_analyzer.find_similar_situations(
            self.parent.current_user['id'],
            situation,
            limit=5
        )

        self.show_similar_dialog(similar)

    def show_similar_dialog(self, similar):
        """Показать диалог с похожими ситуациями"""
        dialog = QDialog(self)
        dialog.setWindowTitle("🔍 Похожие ситуации")
        dialog.resize(550, 500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #FFFBF6;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        if not similar:
            layout.addWidget(QLabel("Похожих ситуаций не найдено."))
        else:
            layout.addWidget(QLabel(f"Найдено {len(similar)} похожих ситуаций:"))

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.setSpacing(15)

            for item in similar:
                entry = item['entry']
                card = self.create_similar_card(item, entry)
                content_layout.addWidget(card)

            content_layout.addStretch()
            scroll.setWidget(content)
            layout.addWidget(scroll, 1)

        close_btn = QPushButton("Закрыть")
        close_btn.setProperty("class", "PrimaryButton")
        close_btn.setFixedHeight(35)
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, 0, Qt.AlignCenter)

        dialog.exec_()

    def create_similar_card(self, item, entry):
        """Создать карточку похожей ситуации"""
        card = QFrame()
        card.setProperty("class", "Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        # Заголовок
        header = QHBoxLayout()
        date_label = QLabel(f"📅 {item['date']}")
        date_label.setStyleSheet("font-weight: bold;")
        header.addWidget(date_label)
        header.addStretch()
        sim_label = QLabel(f"Схожесть: {item['similarity']}%")
        sim_label.setStyleSheet("color: #8B7355;")
        header.addWidget(sim_label)
        layout.addLayout(header)

        # Ситуация
        sit_label = QLabel(f"<b>Ситуация:</b><br>{entry['situation'][:150]}...")
        sit_label.setWordWrap(True)
        sit_label.setTextFormat(Qt.RichText)
        layout.addWidget(sit_label)

        # Что помогло
        if entry.get('alternative_thought'):
            help_label = QLabel(f"💡 <b>Помогло:</b><br>{entry['alternative_thought'][:100]}...")
            help_label.setWordWrap(True)
            help_label.setTextFormat(Qt.RichText)
            layout.addWidget(help_label)

        # Кнопка "Посмотреть"
        view_btn = QPushButton("👁️ Подробнее")
        view_btn.setProperty("class", "SecondaryButton")
        view_btn.setFixedHeight(30)
        view_btn.clicked.connect(lambda: self.view_full_entry(entry))
        layout.addWidget(view_btn)

        return card

    def view_full_entry(self, entry):
        """Просмотр полной записи"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Запись от {entry['created_at'][:10]}")
        dialog.resize(550, 500)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)

        # Дата
        date_label = QLabel(f"📅 <b>{entry['created_at']}</b>")
        date_label.setTextFormat(Qt.RichText)
        content_layout.addWidget(date_label)

        # Ситуация
        sit_label = QLabel(f"<b>Ситуация:</b><br>{entry['situation']}")
        sit_label.setWordWrap(True)
        sit_label.setTextFormat(Qt.RichText)
        content_layout.addWidget(sit_label)

        # Мысли
        if entry.get('thoughts'):
            thought_label = QLabel(f"<b>Автоматические мысли:</b><br>{entry['thoughts']}")
            thought_label.setWordWrap(True)
            thought_label.setTextFormat(Qt.RichText)
            content_layout.addWidget(thought_label)

        # Эмоции
        if entry.get('emotions'):
            emotions_text = "<b>Эмоции:</b><br>"
            for emotion, intensity in entry['emotions'].items():
                if intensity > 0:
                    emotions_text += f"• {emotion}: {intensity}%<br>"
            emo_label = QLabel(emotions_text)
            emo_label.setWordWrap(True)
            emo_label.setTextFormat(Qt.RichText)
            content_layout.addWidget(emo_label)

        # Искажения
        if entry.get('distortions'):
            dist_text = "<b>Когнитивные искажения:</b><br>• " + "<br>• ".join(entry['distortions'])
            dist_label = QLabel(dist_text)
            dist_label.setWordWrap(True)
            dist_label.setTextFormat(Qt.RichText)
            content_layout.addWidget(dist_label)

        # Альтернативная мысль
        if entry.get('alternative_thought'):
            alt_label = QLabel(f"<b>Альтернативная мысль:</b><br>{entry['alternative_thought']}")
            alt_label.setWordWrap(True)
            alt_label.setTextFormat(Qt.RichText)
            content_layout.addWidget(alt_label)

        # Переоценка
        if entry.get('reassessment'):
            reass_label = QLabel(f"<b>Переоценка:</b><br>{entry['reassessment']}")
            reass_label.setWordWrap(True)
            reass_label.setTextFormat(Qt.RichText)
            content_layout.addWidget(reass_label)

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        close_btn = QPushButton("Закрыть")
        close_btn.setProperty("class", "PrimaryButton")
        close_btn.setFixedHeight(35)
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, 0, Qt.AlignCenter)

        dialog.exec_()

    def show_all_similar(self):
        """Показать все похожие (из уведомления)"""
        self.find_similar_situations()

    def on_situation_changed(self):
        """При изменении текста - сбрасываем таймер"""
        if self.notification_widget:
            self.notification_widget.setVisible(False)

        text_length = len(self.situation_input.toPlainText().strip())

        if self.pause_timer:
            self.pause_timer.stop()
            self.pause_timer.deleteLater()
            self.pause_timer = None

        if text_length >= 20:
            self.pause_timer = QTimer()
            self.pause_timer.setSingleShot(True)
            self.pause_timer.timeout.connect(self.on_writing_pause)
            self.pause_timer.start(3000)

    def on_writing_pause(self):
        """Пользователь сделал паузу в письме"""
        situation = self.situation_input.toPlainText().strip()
        if len(situation) >= 20:
            self.find_and_show_notification(situation)

    def find_and_show_notification(self, situation):
        """Найти похожие и показать уведомление"""
        from ai.similarity_analyzer import SimilarityAnalyzer
        if not self.similarity_analyzer:
            self.similarity_analyzer = SimilarityAnalyzer(self.parent.db)

        similar = self.similarity_analyzer.find_similar_situations(
            self.parent.current_user['id'],
            situation,
            limit=2
        )

        if similar:
            self.show_notification(similar)

    def show_notification(self, similar):
        """Показать уведомление с похожими ситуациями"""
        # Очищаем старый список
        while self.notification_list.count():
            item = self.notification_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for item in similar[:2]:
            entry = item['entry']

            item_frame = QFrame()
            item_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.5);
                    border-radius: 5px;
                    padding: 5px;
                }
            """)

            item_layout = QVBoxLayout(item_frame)
            item_layout.setSpacing(3)

            # Дата
            header = QHBoxLayout()
            date_label = QLabel(f"📅 {item['date']}")
            date_label.setStyleSheet("font-size: 11px; font-weight: bold;")
            header.addWidget(date_label)
            header.addStretch()
            sim_label = QLabel(f"{item['similarity']}%")
            sim_label.setStyleSheet("color: #8B7355; font-size: 11px;")
            header.addWidget(sim_label)
            item_layout.addLayout(header)

            # Ситуация
            sit_label = QLabel(item['situation'][:60] + "...")
            sit_label.setStyleSheet("font-size: 11px;")
            sit_label.setWordWrap(True)
            item_layout.addWidget(sit_label)

            # Что помогло
            if entry.get('alternative_thought'):
                help_label = QLabel(f"💡 {entry['alternative_thought'][:50]}...")
                help_label.setStyleSheet("font-size: 10px; color: #06D6A0;")
                help_label.setWordWrap(True)
                item_layout.addWidget(help_label)

            # Кнопка "Посмотреть"
            view_btn = QPushButton("👁️")
            view_btn.setFixedSize(25, 20)
            view_btn.setStyleSheet("font-size: 12px;")
            view_btn.clicked.connect(lambda checked, e=entry: self.view_full_entry(e))
            item_layout.addWidget(view_btn, 0, Qt.AlignRight)

            self.notification_list.addWidget(item_frame)

        self.notification_widget.setVisible(True)

    # ==================== СОХРАНЕНИЕ ЗАПИСИ ====================

    def save_entry(self):
        """Сохранение записи в дневнике"""
        try:
            if not self.parent.current_user:
                QMessageBox.warning(self, "Ошибка", "Вы не авторизованы.")
                return

            situation = self.situation_input.toPlainText().strip()
            thoughts = self.thoughts_input.toPlainText().strip()

            if not situation or not thoughts:
                QMessageBox.warning(self, "Внимание",
                                    "Заполните обязательные поля: Ситуация и Автоматические мысли.")
                return

            # Собираем данные
            emotions_data = {emotion: slider.value() for emotion, slider in self.emotion_inputs.items()}
            distortions = [name for name, checkbox in self.distortion_checks.items() if checkbox.isChecked()]
            alternative = self.alternative_input.toPlainText().strip()
            reassessment = self.reassessment_input.toPlainText().strip()

            # Сохраняем
            user_id = self.parent.current_user['id']
            entry_id = self.parent.db.save_diary_entry(
                user_id=user_id,
                situation=situation,
                emotions=emotions_data,
                thoughts=thoughts,
                distortions=distortions,
                alternative_thought=alternative if alternative else None,
                reassessment=reassessment if reassessment else None
            )

            if entry_id:
                self.update_stats(user_id)
                self.update_streak_days()
                self.clear_form()

                QMessageBox.information(self, "Сохранено",
                                        f"✅ Запись успешно сохранена!\n"
                                        f"Выявлено искажений: {len(distortions)}")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить запись")

        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")

    def update_stats(self, user_id):
        """Обновление статистики"""
        stats = self.parent.db.get_user_stats(user_id)
        if stats:
            new_total = stats["total_entries"] + 1
            self.parent.db.update_user_stats(user_id, {'total_entries': new_total})

        # Проверяем достижения
        new_achievements = self.parent.db.check_achievements(user_id)
        if new_achievements:
            self.show_achievement_notification(new_achievements)

    def update_streak_days(self):
        """Обновление дней подряд"""
        user_id = self.parent.current_user['id']
        stats = self.parent.db.get_user_stats(user_id)
        today = datetime.now().strftime('%Y-%m-%d')
        last_date = stats.get('last_activity_date')

        if last_date:
            last_dt = datetime.strptime(last_date, '%Y-%m-%d')
            today_dt = datetime.strptime(today, '%Y-%m-%d')
            if (today_dt - last_dt).days == 1:
                new_streak = stats['streak_days'] + 1
            elif (today_dt - last_dt).days == 0:
                new_streak = stats['streak_days']
            else:
                new_streak = 1
        else:
            new_streak = 1

        self.parent.db.update_user_stats(user_id, {
            'streak_days': new_streak,
            'last_activity_date': today
        })

    def clear_form(self):
        """Очистка формы"""
        self.situation_input.clear()
        self.thoughts_input.clear()
        self.alternative_input.clear()
        self.reassessment_input.clear()
        for slider in self.emotion_inputs.values():
            slider.setValue(0)
        for checkbox in self.distortion_checks.values():
            checkbox.setChecked(False)

    def show_achievement_notification(self, achievements):
        """Показать уведомление о достижении"""
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

        confetti_label = QLabel("🎊")
        confetti_label.setStyleSheet("font-size: 48px;")
        confetti_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(confetti_label)

        title = QLabel("Поздравляем!")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #5A5A5A;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        for ach in achievements:
            ach_frame = QFrame()
            ach_layout = QHBoxLayout(ach_frame)
            ach_layout.setSpacing(15)

            icon_label = QLabel(ach['icon'])
            icon_label.setStyleSheet("font-size: 24px;")
            ach_layout.addWidget(icon_label)

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

        ok_btn = QPushButton("Отлично!")
        ok_btn.setProperty("class", "PrimaryButton")
        ok_btn.clicked.connect(dialog.close)
        layout.addWidget(ok_btn)

        dialog.exec_()