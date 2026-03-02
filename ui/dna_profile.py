# ui/dna_profile.py
"""Окно профиля ДНК ментального здоровья"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from ai.dna_analyzer import MentalHealthDNAAnalyzer
from widgets.dna_visualization import DNAVisualizationWidget


class DNAProfileWindow(QWidget):
    """Окно профиля ДНК ментального здоровья"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.analyzer = MentalHealthDNAAnalyzer(parent.db)
        self.visualization = DNAVisualizationWidget()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Верхняя панель
        top_bar = self.create_top_bar()
        layout.addWidget(top_bar)

        # Загрузка/генерация
        load_frame = QFrame()
        load_layout = QHBoxLayout(load_frame)

        generate_btn = QPushButton("🔄 Сгенерировать профиль")
        generate_btn.setProperty("class", "PrimaryButton")
        generate_btn.clicked.connect(self.generate_profile)
        load_layout.addWidget(generate_btn)

        export_btn = QPushButton("📤 Экспорт в PDF")
        export_btn.setProperty("class", "SecondaryButton")
        export_btn.clicked.connect(self.export_profile)
        load_layout.addWidget(export_btn)

        layout.addWidget(load_frame)

        # Визуализация
        layout.addWidget(self.visualization)

    def create_top_bar(self):
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

        title = QLabel("🧬 Профиль ДНК ментального здоровья")
        title.setProperty("class", "TitleMedium")
        top_layout.addWidget(title)

        top_layout.addStretch()

        dummy_btn = QPushButton()
        dummy_btn.setFixedSize(back_btn.sizeHint())
        dummy_btn.setVisible(False)
        top_layout.addWidget(dummy_btn)

        return top_bar

    def generate_profile(self):
        """Генерация профиля"""
        if not self.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему")
            return

        progress = QProgressDialog("Анализ ваших данных...", "Отмена", 0, 100, self)
        progress.setWindowTitle("Генерация профиля")
        progress.show()

        profile = self.analyzer.generate_dna_profile(self.parent.current_user['id'])
        self.parent.db.save_dna_profile(self.parent.current_user['id'], profile)

        progress.close()

        self.visualization.update_profile(profile)

        QMessageBox.information(self, "Готово", "Профиль успешно сгенерирован!")

    def export_profile(self):
        """Экспорт профиля в PDF"""
        QMessageBox.information(self, "Экспорт", "Функция экспорта в PDF будет доступна в следующем обновлении")

    def update_profile(self):
        """Обновление отображения профиля"""
        if not self.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему для просмотра профиля")
            return

        profile = self.parent.db.get_dna_profile(self.parent.current_user['id'])

        if profile:
            self.visualization.update_profile(profile)
            QMessageBox.information(self, "Профиль загружен", "Ваш профиль успешно загружен из базы данных")
        else:
            QMessageBox.information(self, "Профиль не найден",
                                    "У вас пока нет сгенерированного профиля.\n\n"
                                    "Нажмите 'Сгенерировать профиль' для создания анализа")