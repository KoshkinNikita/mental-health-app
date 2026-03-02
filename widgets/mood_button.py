# widgets/mood_button.py
"""Специальная кнопка для шкалы настроения с анимацией"""

from PyQt5.QtWidgets import QPushButton, QMessageBox
from PyQt5.QtCore import QPropertyAnimation, QRect, QEasingCurve, Qt
from datetime import datetime


class MoodButton(QPushButton):
    """Специальная кнопка для шкалы настроения с анимацией"""

    def __init__(self, number, parent=None):
        super().__init__(str(number), parent)
        self.number = number
        self.is_checked = False
        self.parent_window = parent

        self.update_style()

        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutBack)

    def update_style(self):
        """Обновление стиля в зависимости от состояния"""
        if self.is_checked:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #{self.get_color()};
                    color: #5A5A5A;
                    border-radius: 21px;
                    border: 3px solid #9BD1B8;
                    font-weight: bold;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #{self.get_hover_color()};
                    border: 3px solid #80BCA0;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #{self.get_color()};
                    color: #5A5A5A;
                    border-radius: 21px;
                    border: 2px solid #E8DFD8;
                    font-weight: 600;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: #{self.get_hover_color()};
                    border: 2px solid #D7CCC8;
                }}
            """)

    def get_color(self):
        """Получить цвет в зависимости от номера"""
        colors = [
            "FFD6DC",  # 1 - очень грустно
            "FFE2C6",  # 2
            "FFEEC6",  # 3
            "FFF3C6",  # 4
            "FFF8C6",  # 5
            "F5FFC6",  # 6
            "E5FFC6",  # 7
            "D5FFC6",  # 8
            "C5FFC6",  # 9
            "B5E5CF",  # 10 - очень радостно
        ]
        return colors[self.number - 1]

    def get_hover_color(self):
        """Цвет при наведении"""
        base_color = self.get_color()
        return self.darken_color(base_color)

    def darken_color(self, hex_color):
        """Затемнить HEX цвет на 20%"""
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = max(0, int(r * 0.8))
        g = max(0, int(g * 0.8))
        b = max(0, int(b * 0.8))

        return f"{r:02X}{g:02X}{b:02X}"

    def setChecked(self, checked):
        """Установить состояние с анимацией"""
        self.is_checked = checked

        current = self.geometry()
        if checked:
            target = QRect(
                current.x() - 3,
                current.y() - 3,
                current.width() + 6,
                current.height() + 6
            )
        else:
            target = current

        self.scale_animation.setStartValue(current)
        self.scale_animation.setEndValue(target)
        self.scale_animation.start()

        self.update_style()

    def mousePressEvent(self, event):
        """Анимация при нажатии"""
        self.scale_animation.setDuration(100)
        current = self.geometry()
        pressed = QRect(
            current.x() + 2,
            current.y() + 2,
            current.width() - 4,
            current.height() - 4
        )

        self.scale_animation.setStartValue(current)
        self.scale_animation.setEndValue(pressed)
        self.scale_animation.start()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Восстановление после нажатия"""
        self.setChecked(not self.is_checked)

        if not hasattr(self.parent_window, 'parent') or not self.parent_window.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему для сохранения настроения")
            self.setChecked(False)
            super().mouseReleaseEvent(event)
            return

        if self.is_checked:
            parent_app = self.parent_window.parent
            if parent_app.current_user:
                today = datetime.now().strftime('%Y-%m-%d')
                success = parent_app.db.save_mood_entry(
                    parent_app.current_user['id'],
                    today,
                    self.number
                )

                if success:
                    if hasattr(self.parent_window, 'mood_chart'):
                        entries = parent_app.db.get_mood_entries(
                            parent_app.current_user['id'],
                            days=7
                        )
                        self.parent_window.mood_chart.update_with_real_data(entries)

                    new_achievements = parent_app.db.check_achievements(parent_app.current_user['id'])
                    if new_achievements:
                        self.show_achievement_notification(new_achievements)
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось сохранить настроение")

        super().mouseReleaseEvent(event)

    def show_achievement_notification(self, achievements):
        """Показать уведомление о новых достижениях"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        from PyQt5.QtCore import Qt

        dialog = QDialog(self.parent_window)
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