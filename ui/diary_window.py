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
        self.thoughts_input.setPlaceholderText("Запишите мысли, которые пришли в голову в этой ситуации...")
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

    def save_entry(self):
        """Сохранение записи в дневнике"""
        try:
            if not self.parent.current_user:
                QMessageBox.warning(self, "Ошибка", "Вы не авторизованы. Войдите в систему.")
                return

            situation = self.situation_input.toPlainText().strip()
            thoughts = self.thoughts_input.toPlainText().strip()

            if not situation or not thoughts:
                QMessageBox.warning(self, "Внимание",
                                    "Пожалуйста, заполните обязательные поля: Ситуация и Автоматические мысли.")
                return

            # Собираем эмоции
            emotions_data = {}
            for emotion, slider in self.emotion_inputs.items():
                emotions_data[emotion] = slider.value()

            # Собираем искажения
            distortions = []
            for name, checkbox in self.distortion_checks.items():
                if checkbox.isChecked():
                    distortions.append(name)

            alternative = self.alternative_input.toPlainText().strip()
            reassessment = self.reassessment_input.toPlainText().strip()

            # Сохраняем в БД
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
                # Обновляем статистику
                stats = self.parent.db.get_user_stats(user_id)
                if stats:
                    new_total = stats["total_entries"] + 1
                    self.parent.db.update_user_stats(user_id, {'total_entries': new_total})

                self.update_streak_days()

                # Проверяем достижения
                new_achievements = self.parent.db.check_achievements(user_id)
                if new_achievements:
                    self.show_achievement_notification(new_achievements)

                QMessageBox.information(
                    self,
                    "Сохранено",
                    f"✅ Запись успешно сохранена!\n\n"
                    f"Выявлено искажений: {len(distortions)}\n"
                    f"Это важный шаг к осознанности!"
                )

                self.clear_form()

                # Обновляем главное меню
                if hasattr(self.parent, 'main_menu'):
                    self.parent.main_menu.update_display()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить запись")

        except Exception as e:
            print(f"Ошибка сохранения записи: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения записи: {str(e)}")

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