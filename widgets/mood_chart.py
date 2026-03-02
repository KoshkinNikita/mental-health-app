# widgets/mood_chart.py
"""Виджет для отображения графика настроения"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class MoodChartWidget(QWidget):
    """Виджет для отображения графика настроения"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(300)
        self.parent_app = parent
        self.init_ui()

    def init_ui(self):
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

        title = QLabel("Статистика настроения")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #5A5A5A;")
        layout.addWidget(title)

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
            value_widget.setStyleSheet("font-size: 16px; font-weight: bold; color: #5A5A5A;")
            stat_layout.addWidget(value_widget)

            layout.addWidget(stat_frame)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #E8DFD8;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        tip_label = QLabel("💡 Совет: Регулярное отслеживание настроения помогает замечать закономерности")
        tip_label.setProperty("class", "TextSecondary")
        tip_label.setWordWrap(True)
        layout.addWidget(tip_label)

        close_btn = QPushButton("Закрыть")
        close_btn.setProperty("class", "PrimaryButton")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec_()

    def generate_sample_data(self):
        """Генерация демо-данных"""
        self.days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        np.random.seed(42)
        self.mood_values = np.random.randint(3, 9, 7)
        self.mood_values[-1] = 6

        self.colors = []
        for value in self.mood_values:
            if value <= 3:
                self.colors.append('#FF6B6B')
            elif value <= 5:
                self.colors.append('#FFD166')
            elif value <= 7:
                self.colors.append('#06D6A0')
            else:
                self.colors.append('#118AB2')

    def plot_chart(self):
        """Отрисовка графика"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        ax.set_facecolor('#FFFBF6')
        self.figure.patch.set_facecolor('#FFFBF6')
        ax.set_ylim(0, 10.5)

        ax.plot(self.days, self.mood_values,
                color='#9BD1B8',
                linewidth=2.5,
                marker='o',
                markersize=8,
                markerfacecolor='white',
                markeredgewidth=2)

        ax.fill_between(self.days, self.mood_values,
                        color='#9BD1B8',
                        alpha=0.1)

        for i, (day, value, color) in enumerate(zip(self.days, self.mood_values, self.colors)):
            ax.scatter(day, value,
                       color=color,
                       s=100,
                       zorder=5,
                       edgecolors='white',
                       linewidths=2)

            ax.text(day, value + 0.3, str(value),
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    fontweight='bold',
                    color='#5A5A5A')

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#E8DFD8')
        ax.spines['bottom'].set_color('#E8DFD8')

        ax.tick_params(axis='x', colors='#8B7355', labelsize=11)
        ax.tick_params(axis='y', colors='#8B7355', labelsize=11)

        ax.set_title('📈 Ваше настроение за неделю',
                     fontsize=14,
                     fontweight='bold',
                     color='#5A5A5A',
                     pad=15)

        ax.set_xlabel('Дни', fontsize=11, color='#8B7355', labelpad=10)
        ax.set_ylabel('Настроение (1-10)', fontsize=11, color='#8B7355', labelpad=10)

        ax.grid(True, alpha=0.2, linestyle='--', color='#C4B6A6')

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

        self.figure.tight_layout()
        self.canvas.draw()

    def update_with_real_data(self, entries):
        """Обновление с реальными данными из БД"""
        if not entries:
            self.generate_sample_data()
        else:
            self.days = []
            self.mood_values = []

            for entry in entries:
                date_str = entry['date']
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                day_name = date_obj.strftime('%a')
                day_name_rus = {
                    'Mon': 'Пн', 'Tue': 'Вт', 'Wed': 'Ср',
                    'Thu': 'Чт', 'Fri': 'Пт', 'Sat': 'Сб', 'Sun': 'Вс'
                }.get(day_name, day_name)

                self.days.append(day_name_rus)
                self.mood_values.append(entry['mood_score'])

            while len(self.days) < 7:
                self.days.insert(0, "")
                self.mood_values.insert(0, 0)

            self.update_colors()
            self.plot_chart()

    def update_colors(self):
        """Обновление цветов на основе реальных значений"""
        self.colors = []
        for value in self.mood_values:
            if value == 0:
                self.colors.append('#E8DFD8')
            elif value <= 3:
                self.colors.append('#FF6B6B')
            elif value <= 5:
                self.colors.append('#FFD166')
            elif value <= 7:
                self.colors.append('#06D6A0')
            else:
                self.colors.append('#118AB2')