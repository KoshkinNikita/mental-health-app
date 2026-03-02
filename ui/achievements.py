# ui/achievements.py
"""Окно достижений и прогресса"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class AchievementsWidget(QWidget):
    """Виджет для отображения достижений"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        title_label = QLabel("🏆 Достижения")
        title_label.setProperty("class", "TitleMedium")
        layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        self.achievements_layout = QVBoxLayout(content_widget)
        self.achievements_layout.setSpacing(10)

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

    def update_achievements(self, user_id):
        """Обновление списка достижений"""
        # Очищаем старые достижения
        while self.achievements_layout.count():
            item = self.achievements_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not user_id:
            return

        achievements = self.parent_app.db.get_user_achievements(user_id)

        if not achievements:
            no_achievements = QLabel("Начните использовать приложение, чтобы получить достижения!")
            no_achievements.setProperty("class", "TextSecondary")
            no_achievements.setAlignment(Qt.AlignCenter)
            self.achievements_layout.addWidget(no_achievements)
            return

        for ach in achievements:
            achievement_card = self.create_achievement_card(ach)
            self.achievements_layout.addWidget(achievement_card)

        self.achievements_layout.addStretch()

    def create_achievement_card(self, achievement):
        """Создание карточки достижения"""
        card = QFrame()
        card.setProperty("class", "Card")
        card.setMinimumHeight(120)  # Фиксируем минимальную высоту

        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Иконка
        icon_label = QLabel(achievement['icon'])
        icon_label.setStyleSheet("font-size: 32px; min-width: 50px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Информация
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Название
        name_label = QLabel(achievement['name'])
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #5A5A5A;")
        name_label.setWordWrap(True)
        info_layout.addWidget(name_label)

        # Описание
        desc_label = QLabel(achievement['description'])
        desc_label.setProperty("class", "TextSecondary")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        # Прогресс
        if achievement['completed']:
            progress_text = f"✅ Выполнено!"
            if achievement['completed_at']:
                date = achievement['completed_at'].split()[0]
                progress_text += f" ({date})"
        else:
            progress = achievement['progress'] or 0
            required = achievement['requirement_value']
            percentage = min(100, int((progress / required) * 100))
            progress_text = f"Прогресс: {progress}/{required} ({percentage}%)"

        progress_label = QLabel(progress_text)
        progress_label.setProperty("class", "TextLight")
        progress_label.setWordWrap(True)
        info_layout.addWidget(progress_label)

        layout.addWidget(info_widget, 1)

        # XP
        if achievement['completed']:
            xp_label = QLabel(f"+{achievement['xp_reward']} XP")
            xp_label.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #FFD166;
                background-color: rgba(255, 209, 102, 0.1);
                padding: 5px 10px;
                border-radius: 10px;
                min-width: 60px;
            """)
            xp_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(xp_label)

        return card


class ProgressWidget(QWidget):
    """Виджет прогресса пользователя"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # Карточка прогресса
        self.progress_card = QFrame()
        self.progress_card.setProperty("class", "MintCard")

        card_layout = QVBoxLayout(self.progress_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # Уровень
        self.level_label = QLabel("Уровень 1")
        self.level_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #5A5A5A;")
        self.level_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.level_label)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 20px;
                border-radius: 10px;
                background-color: #E8DFD8;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #B5E5CF;
                border-radius: 10px;
            }
        """)
        card_layout.addWidget(self.progress_bar)

        # XP
        self.xp_label = QLabel("0/100 XP")
        self.xp_label.setProperty("class", "TextRegular")
        self.xp_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.xp_label)

        layout.addWidget(self.progress_card)

        # Статистика
        stats_frame = QFrame()
        stats_frame.setProperty("class", "WarmCard")

        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(15, 15, 15, 15)
        stats_layout.setSpacing(10)

        stats_title = QLabel("📊 Ваша статистика")
        stats_title.setProperty("class", "TitleSmall")
        stats_layout.addWidget(stats_title)

        # Показатели
        self.stats_labels = {}
        stats_data = [
            ("🔥", "Дней подряд", "streak_days"),
            ("📝", "Всего записей", "total_entries"),
            ("🏆", "Достижений", "achievements_completed"),
            ("🎯", "Текущий уровень", "level"),
        ]

        for icon, text, key in stats_data:
            stat_frame = QFrame()
            stat_layout = QHBoxLayout(stat_frame)
            stat_layout.setContentsMargins(0, 0, 0, 0)

            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 16px;")
            stat_layout.addWidget(icon_label)

            text_label = QLabel(text)
            text_label.setProperty("class", "TextSecondary")
            stat_layout.addWidget(text_label)

            stat_layout.addStretch()

            value_label = QLabel("0")
            value_label.setProperty("class", "TextRegular")
            value_label.setStyleSheet("font-weight: bold;")
            stat_layout.addWidget(value_label)

            self.stats_labels[key] = value_label
            stats_layout.addWidget(stat_frame)

        layout.addWidget(stats_frame)

    def update_progress(self, user_id):
        """Обновление прогресса пользователя"""
        if not user_id:
            return

        stats = self.parent_app.db.get_user_stats(user_id)
        if not stats:
            return

        level_info = self.parent_app.db.get_level_info(stats['xp'])

        self.level_label.setText(f"Уровень {level_info['level']}")
        self.progress_bar.setValue(int(level_info['progress']))
        self.xp_label.setText(f"{stats['xp']}/{level_info['xp_for_next']} XP")

        self.stats_labels['streak_days'].setText(str(stats['streak_days']))
        self.stats_labels['total_entries'].setText(str(stats['total_entries']))
        self.stats_labels['level'].setText(str(level_info['level']))

        cursor = self.parent_app.db.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM user_achievements 
            WHERE user_id = ? AND completed = TRUE
        ''', (user_id,))
        completed_count = cursor.fetchone()['count']
        self.stats_labels['achievements_completed'].setText(str(completed_count))


class AchievementsWindow(QWidget):
    """Окно достижений и прогресса"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Верхняя панель
        self.create_top_bar(main_layout)

        # Контент
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(25)
        content_layout.setContentsMargins(40, 30, 40, 40)

        # Заголовок
        header_label = QLabel("🎮 Прогресс и достижения")
        header_label.setProperty("class", "TitleLarge")
        content_layout.addWidget(header_label)

        # Виджет прогресса
        self.progress_widget = ProgressWidget(self.parent)
        content_layout.addWidget(self.progress_widget)

        # Табы для переключения
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

        self.all_achievements_widget = AchievementsWidget(self.parent)
        self.tab_widget.addTab(self.all_achievements_widget, "Все достижения")

        self.completed_achievements_widget = AchievementsWidget(self.parent)
        self.tab_widget.addTab(self.completed_achievements_widget, "Выполненные")

        content_layout.addWidget(self.tab_widget)

        # Прокручиваемая область
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidget(content_widget)

        main_layout.addWidget(scroll_area)

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

        title = QLabel("Достижения")
        title.setProperty("class", "TitleMedium")
        top_layout.addWidget(title)

        top_layout.addStretch()

        dummy_btn = QPushButton()
        dummy_btn.setFixedSize(back_btn.sizeHint())
        dummy_btn.setVisible(False)
        top_layout.addWidget(dummy_btn)

        parent_layout.addWidget(top_bar)

    def update_display(self):
        """Обновление отображения"""
        if self.parent.current_user:
            user_id = self.parent.current_user['id']
            self.progress_widget.update_progress(user_id)
            self.all_achievements_widget.update_achievements(user_id)

            # Получаем только выполненные
            cursor = self.parent.db.conn.cursor()
            cursor.execute('''
                SELECT a.*, ua.progress, ua.completed, ua.completed_at
                FROM achievements a
                JOIN user_achievements ua ON a.id = ua.achievement_id
                WHERE ua.user_id = ? AND ua.completed = TRUE
                ORDER BY ua.completed_at DESC
            ''', (user_id,))
            completed = cursor.fetchall()
            self.completed_achievements_widget.update_achievements(user_id)