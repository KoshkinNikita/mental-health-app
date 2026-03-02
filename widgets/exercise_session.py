# widgets/exercise_session.py
"""Окно для выполнения упражнения"""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from models.exercise import BreathingExercise, CognitiveExercise


class ExerciseSessionWindow(QDialog):
    """Окно для выполнения упражнения с интерактивным таймером"""

    def __init__(self, exercise, parent=None):
        super().__init__(parent)
        self.exercise = exercise
        self.parent_app = parent
        self.current_step = 0
        self.timer_running = False
        self.seconds_remaining = 0
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
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2C3E50;")
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
        step_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50; padding: 10px 0;")
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
        self.breath_timer.start(1000)

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
                xp_reward = self.exercise.duration * 2
                new_xp = stats['xp'] + xp_reward
                self.parent_app.db.update_user_stats(
                    self.parent_app.current_user['id'],
                    {'xp': new_xp}
                )

        QMessageBox.information(self, "Поздравляю!",
                                f"✅ Вы успешно выполнили упражнение!\n\n"
                                f"Продолжайте практиковаться для лучших результатов.")

        self.accept()