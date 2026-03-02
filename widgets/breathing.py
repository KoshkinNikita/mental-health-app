# widgets/breathing.py
"""Простое дыхательное упражнение"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class SimpleBreathingExercise(QWidget):
    """Простое дыхательное упражнение"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("🌬 Дыхательное упражнение")
        self.setFixedSize(600, 650)  # Увеличил размер
        self.setWindowFlags(Qt.Window)
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
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#startBtn {
                background-color: #B5E5CF;
                color: #5A5A5A;
                min-width: 120px;
            }
            QPushButton#startBtn:hover {
                background-color: #9BD1B8;
            }
            QPushButton#stopBtn {
                background-color: #FFD6DC;
                color: #5A5A5A;
                min-width: 120px;
            }
            QPushButton#stopBtn:hover {
                background-color: #FFC8D6;
            }
            QPushButton#closeBtn {
                background-color: #F8F2E9;
                color: #8B7355;
                border: 1px solid #E8DFD8;
                min-width: 100px;
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
        title.setWordWrap(True)
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
            line-height: 1.6;
        """)
        instruction.setWordWrap(True)
        layout.addWidget(instruction)

        # Контейнер для анимации (фиксированный размер)
        anim_container = QFrame()
        anim_container.setFixedHeight(250)
        anim_container_layout = QVBoxLayout(anim_container)
        anim_container_layout.setAlignment(Qt.AlignCenter)

        # Круг для анимации
        self.animation_frame = QFrame()
        self.animation_frame.setFixedSize(200, 200)
        self.animation_frame.setStyleSheet("""
            QFrame {
                background-color: #B5E5CF;
                border-radius: 100px;
                border: 3px solid #9BD1B8;
            }
        """)

        circle_layout = QVBoxLayout(self.animation_frame)
        circle_layout.setAlignment(Qt.AlignCenter)

        self.phase_label = QLabel("🌬️")
        self.phase_label.setStyleSheet("font-size: 48px; background: transparent;")
        self.phase_label.setAlignment(Qt.AlignCenter)
        circle_layout.addWidget(self.phase_label)

        self.timer_label = QLabel("4")
        self.timer_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #2C3E50; background: transparent;")
        self.timer_label.setAlignment(Qt.AlignCenter)
        circle_layout.addWidget(self.timer_label)

        anim_container_layout.addWidget(self.animation_frame)
        layout.addWidget(anim_container)

        # Счетчик циклов
        self.counter_label = QLabel("Цикл 0 из 5")
        self.counter_label.setStyleSheet("font-size: 18px; color: #8B7355; font-weight: bold;")
        self.counter_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.counter_label)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)
        buttons_layout.setAlignment(Qt.AlignCenter)

        self.start_btn = QPushButton("▶ Начать")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setFixedHeight(50)
        self.start_btn.clicked.connect(self.start_exercise)
        buttons_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏸ Пауза")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setFixedHeight(50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.pause_exercise)
        buttons_layout.addWidget(self.stop_btn)

        layout.addLayout(buttons_layout)

        # Кнопка закрытия
        close_btn = QPushButton("✕ Закрыть")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedHeight(40)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, 0, Qt.AlignCenter)

        # Анимация изменения размера круга
        self.size_animation = QPropertyAnimation(self.animation_frame, b"geometry")
        self.size_animation.setDuration(1000)
        self.size_animation.setEasingCurve(QEasingCurve.InOutQuad)

    def start_exercise(self):
        """Начать упражнение"""
        self.cycle_count = 0
        self.current_phase = "inhale"
        self.phase_label.setText("🌬️")
        self.counter_label.setText(f"Цикл {self.cycle_count + 1} из {self.max_cycles}")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.time_left = 4
        self.timer_label.setText(str(self.time_left))
        self.animate_circle(250)  # Увеличиваем круг для вдоха
        self.timer.start(1000)

    def pause_exercise(self):
        """Поставить на паузу"""
        self.timer.stop()
        self.size_animation.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.phase_label.setText("⏸️")

    def next_phase(self):
        """Переход к следующей фазе"""
        self.time_left -= 1
        self.timer_label.setText(str(self.time_left))

        if self.time_left <= 0:
            if self.current_phase == "inhale":
                self.current_phase = "hold"
                self.phase_label.setText("💭")
                self.time_left = 7
                self.animate_circle(280)  # Максимальный размер на задержке

            elif self.current_phase == "hold":
                self.current_phase = "exhale"
                self.phase_label.setText("🌪️")
                self.time_left = 8
                self.animate_circle(180)  # Уменьшаем круг для выдоха

            elif self.current_phase == "exhale":
                self.cycle_count += 1
                self.counter_label.setText(f"Цикл {self.cycle_count + 1} из {self.max_cycles}")

                if self.cycle_count < self.max_cycles:
                    self.current_phase = "inhale"
                    self.phase_label.setText("🌬️")
                    self.time_left = 4
                    self.animate_circle(250)
                else:
                    self.finish_exercise()
                    return

            self.timer_label.setText(str(self.time_left))

    def animate_circle(self, target_size):
        """Анимация изменения размера круга"""
        current_geo = self.animation_frame.geometry()
        center_x = current_geo.x() + current_geo.width() // 2
        center_y = current_geo.y() + current_geo.height() // 2

        new_geo = QRect(
            center_x - target_size // 2,
            center_y - target_size // 2,
            target_size,
            target_size
        )

        self.size_animation.setStartValue(current_geo)
        self.size_animation.setEndValue(new_geo)
        self.size_animation.start()

    def finish_exercise(self):
        """Завершить упражнение"""
        self.timer.stop()
        self.size_animation.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.phase_label.setText("✅")
        self.timer_label.setText("🎉")
        self.counter_label.setText("Отлично!")

        # Возвращаем круг к нормальному размеру
        current_geo = self.animation_frame.geometry()
        center_x = current_geo.x() + current_geo.width() // 2
        center_y = current_geo.y() + current_geo.height() // 2
        normal_geo = QRect(center_x - 100, center_y - 100, 200, 200)
        self.animation_frame.setGeometry(normal_geo)

        # Сохраняем в БД если есть пользователь
        if self.parent and self.parent.current_user:
            self.parent.db.save_exercise_log(
                user_id=self.parent.current_user['id'],
                exercise_name="Дыхательное упражнение 4-7-8",
                duration_minutes=3,
                notes="Выполнено дыхательное упражнение"
            )

            # Начисляем XP
            stats = self.parent.db.get_user_stats(self.parent.current_user['id'])
            if stats:
                new_xp = stats['xp'] + 20
                self.parent.db.update_user_stats(self.parent.current_user['id'], {'xp': new_xp})

        QMessageBox.information(self, "Молодец!",
                                "✅ Вы успешно выполнили дыхательное упражнение!\n\n"
                                "Регулярная практика помогает снижать тревожность и улучшать самочувствие.")

    def closeEvent(self, event):
        """При закрытии останавливаем таймер"""
        self.timer.stop()
        self.size_animation.stop()
        event.accept()