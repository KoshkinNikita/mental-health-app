# ui/main_window.py
"""Главное окно приложения"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from database.db_manager import DatabaseManager
from widgets.animated import AnimatedStackedWidget
from ui.login import LoginWindow
from ui.main_menu import MainMenuWindow


class MentalHealthApp(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тёплое убежище - поддержка ментального здоровья")
        self.setGeometry(100, 100, 1200, 800)

        self.db = DatabaseManager()
        self.current_user = None

        from ai.predictor import MoodPredictor
        from ai.triggers import TriggerIntelligence
        self.mood_predictor = MoodPredictor(self.db)
        self.trigger_intelligence = TriggerIntelligence(self.db)

        self.stacked_widget = AnimatedStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_ui()
        self.stacked_widget.setCurrentIndex(0)
        self.setup_styles()

    def set_current_user(self, user):
        """Установка текущего пользователя"""
        self.current_user = user
        if hasattr(self, 'main_menu'):
            self.main_menu.set_current_user(user)

        if hasattr(self, 'chat_window'):
            self.chat_window.set_current_user(user)

    def setup_styles(self):
        """Настройка стилей приложения"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFBF6;
            }
            QWidget {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                color: #5A5A5A;
            }
            QPushButton {
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            .PrimaryButton {
                background-color: #B5E5CF;
                color: #5A5A5A;
                border: 1px solid #9BD1B8;
            }
            .PrimaryButton:hover {
                background-color: #9BD1B8;
            }
            .SecondaryButton {
                background-color: #F8F2E9;
                color: #8B7355;
                border: 1px solid #E8DFD8;
            }
            .SecondaryButton:hover {
                background-color: #F0E6DC;
            }
            .EmergencyButton {
                background-color: #FFD6DC;
                color: #5A5A5A;
                border: 1px solid #FFC8D6;
            }
            .EmergencyButton:hover {
                background-color: #FFC8D6;
            }
            .Card {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E8DFD8;
            }
            .WarmCard {
                background-color: #F8F2E9;
                border-radius: 12px;
                border: 1px solid #E8DFD8;
            }
            .MintCard {
                background-color: #B5E5CF;
                border-radius: 12px;
                border: none;
            }
            .SoftPinkCard {
                background-color: #FFD6DC;
                border-radius: 12px;
                border: none;
            }
            .TitleLarge {
                font-size: 28px;
                font-weight: 700;
                color: #5A5A5A;
            }
            .TitleMedium {
                font-size: 20px;
                font-weight: 600;
                color: #5A5A5A;
            }
            .TitleSmall {
                font-size: 16px;
                font-weight: 600;
                color: #5A5A5A;
            }
            .TextRegular {
                font-size: 14px;
                color: #5A5A5A;
            }
            .TextSecondary {
                font-size: 13px;
                color: #8B7355;
            }
            .TextLight {
                font-size: 12px;
                color: #C4B6A6;
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

    def init_ui(self):
        """Инициализация всех окон"""
        print("=" * 50)
        print("ИНИЦИАЛИЗАЦИЯ ОКОН")
        print("=" * 50)

        # Окно входа
        self.login_window = LoginWindow(self)
        self.stacked_widget.addWidget(self.login_window)
        print(f"Добавлено окно входа: индекс 0")

        # Главное меню
        self.main_menu = MainMenuWindow(self)
        self.stacked_widget.addWidget(self.main_menu)
        print(f"Добавлено главное меню: индекс 1")

        from ui.diary_window import DiaryWindow
        self.diary_window = DiaryWindow(self)
        self.stacked_widget.addWidget(self.diary_window)
        print(f"Добавлено окно дневника: индекс {self.stacked_widget.count() - 1}")

        from ui.exercises_window import ExercisesWindow
        self.exercises_window = ExercisesWindow(self)
        self.stacked_widget.addWidget(self.exercises_window)
        print(f"Добавлено окно упражнений: индекс {self.stacked_widget.count() - 1}")

        from ui.history_window import HistoryWindow
        self.history_window = HistoryWindow(self)
        self.stacked_widget.addWidget(self.history_window)
        print(f"Добавлено окно истории: индекс {self.stacked_widget.count() - 1}")

        from ui.achievements import AchievementsWindow
        self.achievements_window = AchievementsWindow(self)
        self.stacked_widget.addWidget(self.achievements_window)
        print(f"Добавлено окно достижений: индекс {self.stacked_widget.count() - 1}")

        from ui.intelligence import IntelligenceDashboard
        self.intelligence_window = IntelligenceDashboard(self)
        self.stacked_widget.addWidget(self.intelligence_window)
        print(f"Добавлено окно интеллектуального анализа: индекс {self.stacked_widget.count() - 1}")

        # Окно ДНК профиля
        from ui.dna_profile import DNAProfileWindow
        self.dna_window = DNAProfileWindow(self)
        self.stacked_widget.addWidget(self.dna_window)
        print(f"Добавлено окно ДНК профиля: индекс {self.stacked_widget.count() - 1}")

        # Окно чата
        from ui.chat_window import ChatBotWindow
        self.chat_window = ChatBotWindow(self)
        self.stacked_widget.addWidget(self.chat_window)
        print(f"Добавлено окно чата: индекс {self.stacked_widget.count() - 1}")

        print(f"Всего окон: {self.stacked_widget.count()}")
        print("=" * 50)

    def show(self):
        """Показ окна с центрированием"""
        super().show()
        self.center_on_screen()

    def center_on_screen(self):
        """Центрирование окна на экране"""
        try:
            screen = QApplication.primaryScreen().geometry()
            window_geometry = self.frameGeometry()
            center_point = screen.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())
        except Exception as e:
            print(f"Ошибка центрирования: {e}")