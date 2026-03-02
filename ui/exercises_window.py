# ui/exercises_window.py
"""Окно упражнений КПТ"""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from models.exercise import ExerciseLibrary
from widgets.exercise_session import ExerciseSessionWindow


class ExercisesWindow(QWidget):
    """Окно упражнений КПТ"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.exercise_library = ExerciseLibrary()
        self.current_category = 'все'
        self.category_buttons = []
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

        # Заголовок
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

        # Все упражнения
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
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2C3E50;")
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
            self.display_all_exercises()
        else:
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

        # Обновляем статистику после выполнения
        if self.parent.current_user:
            self.create_stats_card()

    def open_random_exercise(self):
        """Открыть случайное упражнение"""
        if not self.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему для выполнения упражнений")
            return

        exercise = self.exercise_library.get_random_exercise()
        if exercise:
            self.start_exercise(exercise)