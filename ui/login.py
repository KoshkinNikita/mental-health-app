# ui/login.py
"""Окно входа и регистрации"""

import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from database.db_manager import DatabaseManager

class RegistrationDialog(QDialog):
    """Диалог регистрации нового пользователя"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Создание аккаунта")
        self.setFixedSize(400, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("🌱 Создание аккаунта")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #5A5A5A;")
        layout.addWidget(title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ваше имя")
        self.name_input.setFixedHeight(40)
        layout.addWidget(self.name_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин (мин. 3 символа)")
        self.username_input.setFixedHeight(40)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль (мин. 6 символов)")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(40)
        layout.addWidget(self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Подтвердите пароль")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setFixedHeight(40)
        layout.addWidget(self.confirm_input)

        layout.addSpacing(10)

        buttons_layout = QHBoxLayout()

        register_btn = QPushButton("Создать аккаунт")
        register_btn.setProperty("class", "PrimaryButton")
        register_btn.clicked.connect(self.register)
        buttons_layout.addWidget(register_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setProperty("class", "SecondaryButton")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def register(self):
        """Регистрация нового пользователя"""
        try:
            name = self.name_input.text().strip()
            username = self.username_input.text().strip()
            password = self.password_input.text()
            confirm = self.confirm_input.text()

            if not name or not username or not password:
                QMessageBox.warning(self, "Ошибка", "Заполните все поля")
                return

            if len(username) < 3:
                QMessageBox.warning(self, "Ошибка", "Логин должен быть не менее 3 символов")
                return

            if len(password) < 6:
                QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 6 символов")
                return

            if password != confirm:
                QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
                return

            user_id = self.db.create_user(username, password, name)

            if user_id:
                QMessageBox.information(self, "Успешно", "Аккаунт создан!")
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином уже существует")
        except Exception as e:
            print(f"Ошибка регистрации: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка регистрации: {str(e)}")


class LoginWindow(QWidget):
    """Окно входа в систему"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(0)

        self.setStyleSheet("background-color: #FFFBF6;")

        container = QFrame()
        container.setFixedWidth(400)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(30)
        container_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("Тёплое убежище")
        title_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #5A5A5A;
            margin: 0;
            padding: 0;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title_label)

        subtitle_label = QLabel("Поддержка ментального здоровья через КПТ")
        subtitle_label.setStyleSheet("""
            font-size: 14px;
            color: #8B7355;
            margin: 0;
            padding: 0;
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(subtitle_label)

        container_layout.addSpacing(20)

        form_card = QFrame()
        form_card.setStyleSheet("""
            background-color: white;
            border-radius: 12px;
            border: 1px solid #E8DFD8;
        """)
        form_card.setFixedSize(400, 350)

        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(40, 30, 40, 30)
        form_layout.setSpacing(25)

        form_title = QLabel("Вход в систему")
        form_title.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
            color: #5A5A5A;
            margin: 0;
            padding: 0;
        """)
        form_title.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(form_title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин")
        self.username_input.setFixedHeight(45)
        self.username_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E8DFD8;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #B5E5CF;
            }
        """)
        form_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(45)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E8DFD8;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #B5E5CF;
            }
        """)
        form_layout.addWidget(self.password_input)

        login_btn = QPushButton("Войти с заботой ❤️")
        login_btn.setFixedHeight(50)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #B5E5CF;
                color: #5A5A5A;
                border-radius: 8px;
                border: none;
                font-weight: 600;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #9BD1B8;
            }
        """)
        login_btn.clicked.connect(self.login)
        form_layout.addWidget(login_btn)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #E8DFD8;")
        separator.setFixedHeight(1)
        form_layout.addWidget(separator)

        register_btn = QPushButton("Создать аккаунт")
        register_btn.setFixedHeight(45)
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8B7355;
                border: 1px solid #E8DFD8;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F8F2E9;
            }
        """)
        register_btn.clicked.connect(self.register)
        form_layout.addWidget(register_btn)

        container_layout.addWidget(form_card)

        demo_label = QLabel("Для демо-входа: логин: demo, пароль: demo123")
        demo_label.setStyleSheet("""
            font-size: 12px;
            color: #C4B6A6;
            font-style: italic;
            margin-top: 20px;
        """)
        demo_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(demo_label)

        main_layout.addWidget(container)

        self.password_input.returnPressed.connect(self.login)
        self.username_input.setFocus()

    def login(self):
        """Обработка входа пользователя"""
        try:
            username = self.username_input.text()
            password = self.password_input.text()

            if not username or not password:
                QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
                return

            user = self.parent.db.authenticate_user(username, password)

            if user:
                self.parent.set_current_user(user)
                self.parent.stacked_widget.setCurrentIndexWithAnimation(1)
                return

            if username == "demo" and password == "demo123":
                user = self.parent.db.authenticate_user("demo", "demo123")

                if not user:
                    print("Создаем демо-пользователя...")
                    user_id = self.parent.db.create_user("demo", "demo123", "Демо Пользователь")

                    if user_id:
                        self.create_demo_data(user_id)
                        user = self.parent.db.authenticate_user("demo", "demo123")

                if user:
                    self.parent.set_current_user(user)
                    self.parent.stacked_widget.setCurrentIndexWithAnimation(1)
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось создать демо-аккаунт")
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
        except Exception as e:
            print(f"Ошибка входа: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка входа: {str(e)}")

    def create_demo_data(self, user_id):
        """Создание демо-данных для нового пользователя"""
        try:
            print(f"Создание демо-данных для пользователя {user_id}")

            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                mood = random.randint(4, 8)
                self.parent.db.save_mood_entry(user_id, date, mood, "Демо-запись")

            demo_entries = [
                {
                    'situation': 'Коллега не ответил на мое приветствие',
                    'emotions': {'Тревога': 80, 'Грусть': 60},
                    'thoughts': 'Он меня ненавидит, я сделал что-то не так',
                    'distortions': ['Чтение мыслей', 'Катастрофизация'],
                    'alternative': 'Возможно, он был занят или не заметил меня'
                },
                {
                    'situation': 'Не получилось выполнить задачу идеально',
                    'emotions': {'Стыд': 90, 'Гнев': 40},
                    'thoughts': 'Я неудачник, у меня никогда ничего не получается',
                    'distortions': ['Черно-белое мышление', 'Персонализация'],
                    'alternative': 'Это одна задача из многих, я учусь и совершенствуюсь'
                }
            ]

            for entry in demo_entries:
                self.parent.db.save_diary_entry(
                    user_id=user_id,
                    situation=entry['situation'],
                    emotions=entry['emotions'],
                    thoughts=entry['thoughts'],
                    distortions=entry['distortions'],
                    alternative_thought=entry['alternative']
                )

            print("Демо-данные созданы")
        except Exception as e:
            print(f"Ошибка создания демо-данных: {e}")

    def register(self):
        """Открытие диалога регистрации"""
        try:
            dialog = RegistrationDialog(self.parent.db, self)
            if dialog.exec_():
                QMessageBox.information(self, "Успешно", "Аккаунт создан! Можете войти.")
        except Exception as e:
            print(f"Ошибка регистрации: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка регистрации: {str(e)}")