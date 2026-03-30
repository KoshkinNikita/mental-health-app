# ui/history_window.py
"""Окно истории записей"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class HistoryWindow(QWidget):
    """Окно истории записей"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_user = None
        self.entries_layout = None
        self.stats_card = None
        self.stats_widgets = {}
        self.init_ui()

    def set_current_user(self, user):
        """Установка текущего пользователя"""
        self.current_user = user
        self.update_display()

    def showEvent(self, event):
        """Событие при показе окна"""
        super().showEvent(event)
        self.update_display()

    def update_display(self):
        """Обновление отображения истории"""
        try:
            if not self.parent or not self.parent.current_user:
                self.show_guest_message()
                return

            user_id = self.parent.current_user['id']

            # Очищаем старые записи
            if hasattr(self, 'entries_layout') and self.entries_layout:
                while self.entries_layout.count() > 2:
                    item = self.entries_layout.takeAt(2)
                    if item and item.widget():
                        item.widget().deleteLater()

            # Загружаем записи
            entries = self.parent.db.get_diary_entries(user_id, limit=20)

            if entries:
                for entry in entries:
                    entry_card = self.create_real_entry_card(entry)
                    if self.entries_layout:
                        self.entries_layout.insertWidget(self.entries_layout.count() - 1, entry_card)
            else:
                no_entries = QLabel("📭 У вас пока нет записей в дневнике\n\n"
                                    "Создайте первую запись в разделе «Дневник мыслей»")
                no_entries.setProperty("class", "TextSecondary")
                no_entries.setAlignment(Qt.AlignCenter)
                no_entries.setStyleSheet("padding: 40px; font-size: 16px;")
                if self.entries_layout:
                    self.entries_layout.insertWidget(1, no_entries)

            self.update_stats_section()

        except Exception as e:
            print(f"Ошибка обновления истории: {e}")
            import traceback
            traceback.print_exc()

    def update_stats_section(self):
        """Обновление статистики"""
        try:
            if not self.parent.current_user:
                return

            user_id = self.parent.current_user['id']
            diary_stats = self.parent.db.get_diary_stats(user_id)
            mood_entries = self.parent.db.get_mood_entries(user_id, days=30)

            # Рассчитываем среднее настроение
            avg_mood = 0
            if mood_entries and len(mood_entries) > 0:
                mood_scores = [entry['mood_score'] for entry in mood_entries if entry['mood_score'] > 0]
                avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0

            # Обновляем виджеты статистики
            if 'total_entries' in self.stats_widgets:
                self.stats_widgets['total_entries'].setText(str(diary_stats.get('total_entries', 0)))

            if 'days_with_entries' in self.stats_widgets:
                self.stats_widgets['days_with_entries'].setText(str(diary_stats.get('days_with_entries', 0)))

            if 'avg_mood' in self.stats_widgets:
                self.stats_widgets['avg_mood'].setText(f"{avg_mood:.1f}/10")

            if 'common_distortion' in self.stats_widgets:
                common_distortions = diary_stats.get('common_distortions', {})
                if common_distortions:
                    most_common = max(common_distortions.items(), key=lambda x: x[1], default=("Нет данных", 0))
                    self.stats_widgets['common_distortion'].setText(f"{most_common[0]} ({most_common[1]} раз)")
                else:
                    self.stats_widgets['common_distortion'].setText("Нет данных")

        except Exception as e:
            print(f"Ошибка обновления статистики: {e}")

    def show_guest_message(self):
        """Показать сообщение для гостя"""
        if hasattr(self, 'entries_layout') and self.entries_layout:
            while self.entries_layout.count() > 2:
                item = self.entries_layout.takeAt(2)
                if item.widget():
                    item.widget().deleteLater()

            guest_message = QLabel("👤 Войдите в систему, чтобы увидеть историю записей")
            guest_message.setProperty("class", "TextSecondary")
            guest_message.setAlignment(Qt.AlignCenter)
            guest_message.setStyleSheet("padding: 40px; font-size: 16px;")
            self.entries_layout.insertWidget(1, guest_message)

    def create_real_entry_card(self, entry):
        """Создание карточки реальной записи"""
        card = QFrame()
        card.setProperty("class", "Card")
        card.setMinimumHeight(150)  # Фиксируем минимальную высоту

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Дата и время
        created_at = datetime.strptime(entry['created_at'], '%Y-%m-%d %H:%M:%S')
        date_str = created_at.strftime("%d.%m.%Y %H:%M")

        date_label = QLabel(f"📅 {date_str}")
        date_label.setProperty("class", "TextLight")
        layout.addWidget(date_label)

        # Ситуация
        situation_short = entry['situation'][:150] + "..." if len(entry['situation']) > 150 else entry['situation']
        situation_label = QLabel(f"<b>Ситуация:</b> {situation_short}")
        situation_label.setProperty("class", "TextRegular")
        situation_label.setTextFormat(Qt.RichText)
        situation_label.setWordWrap(True)
        layout.addWidget(situation_label)

        # Эмоции
        emotions = entry['emotions']
        top_emotions = sorted([(k, v) for k, v in emotions.items() if v > 0],
                              key=lambda x: x[1], reverse=True)[:3]
        if top_emotions:
            emotions_text = ", ".join([f"{e[0]}: {e[1]}%" for e in top_emotions])
            emotions_label = QLabel(f"<b>Эмоции:</b> {emotions_text}")
            emotions_label.setProperty("class", "TextSecondary")
            emotions_label.setTextFormat(Qt.RichText)
            emotions_label.setWordWrap(True)
            layout.addWidget(emotions_label)

        # Когнитивные искажения
        if entry['distortions']:
            distortions_text = ", ".join(entry['distortions'])
            distortions_label = QLabel(f"<b>Искажения:</b> {distortions_text}")
            distortions_label.setProperty("class", "TextSecondary")
            distortions_label.setTextFormat(Qt.RichText)
            distortions_label.setWordWrap(True)
            layout.addWidget(distortions_label)

        exercises = self.parent.db.get_exercise_feedback_for_entry(entry['id'])
        if exercises:
            ex_frame = QFrame()
            ex_frame.setStyleSheet("background-color: #F8F2E9; border-radius: 8px; padding: 8px;")
            ex_layout = QVBoxLayout(ex_frame)
            ex_layout.addWidget(QLabel("🧘 Связанные упражнения:"))

            for ex in exercises:
                row = QHBoxLayout()

                # Название
                row.addWidget(QLabel(f"• {ex['exercise_name']}"), 1)

                # Оценка
                if ex['helped'] == 1:
                    row.addWidget(QLabel("✅ Помогло"))
                elif ex['helped'] == -1:
                    row.addWidget(QLabel("❌ Не помогло"))
                else:
                    # Кнопки для оценки
                    yes_btn = QPushButton("👍")
                    yes_btn.setFixedSize(25, 25)
                    yes_btn.clicked.connect(lambda _, eid=ex['id']: self.rate_exercise(eid, True))
                    no_btn = QPushButton("👎")
                    no_btn.setFixedSize(25, 25)
                    no_btn.clicked.connect(lambda _, eid=ex['id']: self.rate_exercise(eid, False))
                    row.addWidget(yes_btn)
                    row.addWidget(no_btn)

                ex_layout.addLayout(row)

            layout.addWidget(ex_frame)

        # Кнопка детального просмотра
        view_btn = QPushButton("👁️ Подробнее")
        view_btn.setProperty("class", "SecondaryButton")
        view_btn.setFixedHeight(35)
        view_btn.setFixedWidth(120)
        view_btn.clicked.connect(lambda checked, e=entry: self.show_entry_details(e))
        layout.addWidget(view_btn, 0, Qt.AlignRight)

        return card

    def rate_exercise(self, feedback_id, helped):
        cursor = self.parent.db.conn.cursor()
        cursor.execute('UPDATE exercise_feedback SET helped = ? WHERE id = ?',
                       (1 if helped else -1, feedback_id))
        self.parent.db.conn.commit()
        self.update_display()

    def show_entry_details(self, entry):
        """Показать детали записи"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Запись от {entry['created_at'][:10]}")
        dialog.setFixedSize(700, 600)  # Увеличил размер

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # Прокручиваемая область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)

        # Все поля записи
        fields = [
            ("📅 Дата", entry['created_at']),
            ("🎭 Ситуация", entry['situation']),
            ("💭 Автоматические мысли", entry['thoughts']),
            ("🧠 Альтернативная мысль", entry['alternative_thought'] or "Не указано"),
            ("📊 Переоценка", entry['reassessment'] or "Не указано"),
        ]

        for title, value in fields:
            frame = QFrame()
            frame_layout = QVBoxLayout(frame)
            frame_layout.setSpacing(8)

            title_label = QLabel(f"<b>{title}:</b>")
            title_label.setProperty("class", "TextRegular")
            title_label.setTextFormat(Qt.RichText)
            frame_layout.addWidget(title_label)

            value_label = QLabel(value)
            value_label.setProperty("class", "TextRegular")
            value_label.setWordWrap(True)
            value_label.setTextFormat(Qt.PlainText)
            frame_layout.addWidget(value_label)

            content_layout.addWidget(frame)

        # Эмоции
        if entry['emotions']:
            emotions_frame = QFrame()
            emotions_layout = QVBoxLayout(emotions_frame)
            emotions_layout.setSpacing(8)

            title = QLabel("<b>📈 Эмоции и интенсивность:</b>")
            title.setProperty("class", "TextRegular")
            title.setTextFormat(Qt.RichText)
            emotions_layout.addWidget(title)

            for emotion, value in entry['emotions'].items():
                if value > 0:
                    emotion_row = QFrame()
                    row_layout = QHBoxLayout(emotion_row)

                    label = QLabel(emotion)
                    label.setProperty("class", "TextRegular")
                    row_layout.addWidget(label)

                    row_layout.addStretch()

                    value_label = QLabel(f"{value}%")
                    value_label.setProperty("class", "TextRegular")
                    value_label.setStyleSheet("font-weight: bold;")
                    row_layout.addWidget(value_label)

                    emotions_layout.addWidget(emotion_row)

            content_layout.addWidget(emotions_frame)

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)  # Растягиваем

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setProperty("class", "PrimaryButton")
        close_btn.setFixedHeight(40)
        close_btn.setFixedWidth(120)
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, 0, Qt.AlignCenter)

        dialog.exec_()

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
        content_layout.setSpacing(25)
        content_layout.setContentsMargins(40, 30, 40, 40)

        # Заголовок
        header_label = QLabel("📊 История записей")
        header_label.setProperty("class", "TitleLarge")
        content_layout.addWidget(header_label)

        # Фильтры
        filters_frame = self.create_filters()
        content_layout.addWidget(filters_frame)

        # Статистика
        stats_frame = self.create_stats()
        content_layout.addWidget(stats_frame)

        # Записи
        entries_frame = self.create_entries()
        content_layout.addWidget(entries_frame)

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
        back_btn.clicked.connect(lambda: self.parent.stacked_widget.setCurrentIndexWithAnimation(1))
        top_layout.addWidget(back_btn)

        top_layout.addStretch()

        # Название
        title = QLabel("История записей")
        title.setProperty("class", "TitleMedium")
        top_layout.addWidget(title)

        top_layout.addStretch()

        # Заглушка для выравнивания
        dummy_btn = QPushButton()
        dummy_btn.setFixedSize(back_btn.sizeHint())
        dummy_btn.setVisible(False)
        top_layout.addWidget(dummy_btn)

        parent_layout.addWidget(top_bar)

    def create_filters(self):
        """Создание фильтров"""
        frame = QFrame()
        frame.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout(frame)
        layout.setSpacing(15)

        # Период
        period_label = QLabel("Период:")
        period_label.setProperty("class", "TextRegular")
        layout.addWidget(period_label)

        self.period_combo = QComboBox()
        self.period_combo.addItems(["За всё время", "За месяц", "За неделю", "За сегодня"])
        self.period_combo.setFixedWidth(150)
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        layout.addWidget(self.period_combo)

        layout.addStretch()

        # Кнопка экспорта
        export_btn = QPushButton("📤 Экспорт")
        export_btn.setProperty("class", "SecondaryButton")
        export_btn.clicked.connect(self.export_data)
        layout.addWidget(export_btn)

        return frame

    def on_period_changed(self, period):
        """Обработка изменения периода"""
        self.update_display()

    def export_data(self):
        """Экспорт данных"""
        if not self.parent.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в систему")
            return

        # Получаем выбранный период
        period = self.period_combo.currentText()

        # Определяем количество дней
        days = 365  # всё время
        if period == "За месяц":
            days = 30
        elif period == "За неделю":
            days = 7
        elif period == "За сегодня":
            days = 1

        # Получаем данные
        user_id = self.parent.current_user['id']
        entries = self.parent.db.get_diary_entries(user_id, limit=1000)
        mood_entries = self.parent.db.get_mood_entries(user_id, days=days)

        # Фильтруем по дате если нужно
        if days < 365:
            cutoff = datetime.now() - timedelta(days=days)
            entries = [e for e in entries if datetime.strptime(e['created_at'], '%Y-%m-%d %H:%M:%S') > cutoff]

        # Формируем текст для экспорта
        text = f"ЭКСПОРТ ДАННЫХ - {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        text += f"Пользователь: {self.parent.current_user['name']}\n"
        text += f"Период: {period}\n"
        text += "=" * 50 + "\n\n"

        text += "ЗАПИСИ НАСТРОЕНИЯ:\n"
        for entry in mood_entries:
            text += f"{entry['date']}: {entry['mood_score']}/10\n"

        text += "\nЗАПИСИ ДНЕВНИКА:\n"
        for entry in entries:
            text += f"\n--- {entry['created_at']} ---\n"
            text += f"Ситуация: {entry['situation']}\n"
            text += f"Мысли: {entry['thoughts']}\n"

        # Сохраняем файл
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить данные",
            f"export_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            "Text Files (*.txt)"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Готово", f"Данные сохранены в {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {str(e)}")

    def create_stats(self):
        """Создание статистики"""
        self.stats_card = QFrame()
        self.stats_card.setProperty("class", "WarmCard")

        layout = QVBoxLayout(self.stats_card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("📈 Ваша статистика")
        title.setProperty("class", "TitleSmall")
        layout.addWidget(title)

        self.stats_widgets = {}

        stats_data = [
            ("Всего записей", "total_entries", "0"),
            ("Дней с записями", "days_with_entries", "0"),
            ("Среднее настроение", "avg_mood", "0/10"),
            ("Частое искажение", "common_distortion", "Нет данных"),
        ]

        for label_text, key, default_value in stats_data:
            stat_frame = QFrame()
            stat_layout = QHBoxLayout(stat_frame)
            stat_layout.setContentsMargins(0, 0, 0, 0)

            label_widget = QLabel(label_text)
            label_widget.setProperty("class", "TextRegular")
            label_widget.setFixedWidth(150)
            stat_layout.addWidget(label_widget)

            stat_layout.addStretch()

            value_widget = QLabel(default_value)
            value_widget.setStyleSheet("font-size: 16px; font-weight: bold; color: #5A5A5A;")
            stat_layout.addWidget(value_widget)

            self.stats_widgets[key] = value_widget
            layout.addWidget(stat_frame)

        return self.stats_card

    def create_entries(self):
        """Создание списка записей"""
        frame = QFrame()
        frame.setStyleSheet("background-color: transparent;")

        self.entries_layout = QVBoxLayout(frame)
        self.entries_layout.setSpacing(15)

        # Заголовок
        title = QLabel("Последние записи")
        title.setProperty("class", "TitleSmall")
        self.entries_layout.addWidget(title)

        # Кнопка показать больше
        more_btn = QPushButton("Показать больше записей")
        more_btn.setProperty("class", "SecondaryButton")
        more_btn.clicked.connect(self.load_more_entries)
        self.entries_layout.addWidget(more_btn)

        return frame

    def load_more_entries(self):
        """Загрузка большего количества записей"""
        if not self.parent.current_user:
            return

        user_id = self.parent.current_user['id']
        entries = self.parent.db.get_diary_entries(user_id, limit=50)

        # Очищаем старые записи кроме заголовка и кнопки
        while self.entries_layout.count() > 2:
            item = self.entries_layout.takeAt(2)
            if item.widget():
                item.widget().deleteLater()

        # Добавляем все записи
        for entry in entries:
            entry_card = self.create_real_entry_card(entry)
            self.entries_layout.insertWidget(self.entries_layout.count() - 1, entry_card)

        QMessageBox.information(self, "Информация", f"Загружено {len(entries)} записей")