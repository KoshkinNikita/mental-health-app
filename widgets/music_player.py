# widgets/music_player.py
"""Простой музыкальный плеер для релаксации"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Попытка импорта pygame (опционально)
try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️ Pygame не установлен. Музыка будет в демо-режиме. Установите: pip install pygame")


class SimpleMusicPlayer(QWidget):
    """Простой музыкальный плеер"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎵 Музыка")
        self.setFixedSize(350, 300)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFBF6;
                border: 2px solid #E8DFD8;
                border-radius: 10px;
            }
        """)

        self.is_playing = False
        self.volume = 50
        self.current_track_index = 0
        self.pygame = None
        self.audio_available = PYGAME_AVAILABLE

        # Треки
        self.tracks = [
            {"name": "🌊 Звуки океана", "file": "ocean.mp3"},
            {"name": "🌧️ Шум дождя", "file": "rain.mp3"},
            {"name": "🔥 Потрескивание костра", "file": "fire.mp3"},
            {"name": "🎹 Фортепиано", "file": "piano.mp3"},
            {"name": "🧘 Медитация", "file": "meditation.mp3"}
        ]

        # Получаем полный путь к папке music
        self.music_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "music")

        # Создаем папку, если её нет
        os.makedirs(self.music_dir, exist_ok=True)

        # Добавляем полные пути к файлам
        for track in self.tracks:
            track["full_path"] = os.path.join(self.music_dir, track["file"])

        self.init_ui()
        self.init_audio()
        self.check_music_files()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок
        title = QLabel("🎵 Расслабляющая музыка")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #5A5A5A;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Статус файлов
        self.files_status = QLabel("")
        self.files_status.setStyleSheet("color: #8B7355; font-size: 10px;")
        self.files_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.files_status)

        # Информация о pygame
        if not self.audio_available:
            pygame_warning = QLabel("⚠️ Pygame не установлен\nМузыка не будет работать")
            pygame_warning.setStyleSheet("color: #FF6B6B; font-size: 11px; padding: 5px;")
            pygame_warning.setAlignment(Qt.AlignCenter)
            pygame_warning.setWordWrap(True)
            layout.addWidget(pygame_warning)

        # Выбор трека
        track_frame = QFrame()
        track_layout = QHBoxLayout(track_frame)
        track_layout.setContentsMargins(0, 0, 0, 0)

        track_label = QLabel("Трек:")
        track_label.setStyleSheet("color: #8B7355;")
        track_layout.addWidget(track_label)

        self.track_combo = QComboBox()
        self.track_combo.addItems([t["name"] for t in self.tracks])
        self.track_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #E8DFD8;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
                min-width: 180px;
            }
            QComboBox:hover {
                border-color: #B5E5CF;
            }
        """)
        self.track_combo.currentIndexChanged.connect(self.change_track)
        track_layout.addWidget(self.track_combo)

        layout.addWidget(track_frame)

        # Кнопки управления
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(15)

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(60, 40)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #B5E5CF;
                border: none;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9BD1B8;
            }
            QPushButton:disabled {
                background-color: #E8DFD8;
                color: #C4B6A6;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.play_btn)

        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setFixedSize(60, 40)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFD6DC;
                border: none;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFC8D6;
            }
            QPushButton:disabled {
                background-color: #E8DFD8;
                color: #C4B6A6;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_music)
        controls_layout.addWidget(self.stop_btn)

        layout.addWidget(controls_frame)

        # Громкость
        volume_frame = QFrame()
        volume_layout = QHBoxLayout(volume_frame)
        volume_layout.setContentsMargins(0, 0, 0, 0)

        volume_label = QLabel("🔊")
        volume_label.setStyleSheet("color: #8B7355; font-size: 16px;")
        volume_layout.addWidget(volume_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.volume)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #E8DFD8;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #B5E5CF;
                width: 15px;
                margin: -4px 0;
                border-radius: 7px;
            }
        """)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)

        self.volume_value = QLabel(f"{self.volume}%")
        self.volume_value.setStyleSheet("color: #5A5A5A; min-width: 35px;")
        volume_layout.addWidget(self.volume_value)

        layout.addWidget(volume_frame)

        # Статус
        self.status_label = QLabel("⏸ Готов")
        self.status_label.setStyleSheet("color: #C4B6A6; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Инструкция по добавлению музыки
        if not self.audio_available:
            help_label = QLabel(
                "Для добавления музыки:\n"
                "1. Установите pygame: pip install pygame\n"
                "2. Положите MP3 файлы в папку:\n"
                f"{self.music_dir}"
            )
            help_label.setStyleSheet("color: #8B7355; font-size: 10px; padding: 5px;")
            help_label.setWordWrap(True)
            help_label.setAlignment(Qt.AlignLeft)
            layout.addWidget(help_label)

        layout.addStretch()

    def init_audio(self):
        """Инициализация аудио"""
        if not PYGAME_AVAILABLE:
            return

        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            self.pygame = pygame
            self.audio_available = True
            print("✅ Аудио система инициализирована")
        except Exception as e:
            print(f"⚠️ Ошибка инициализации аудио: {e}")
            self.audio_available = False

    def check_music_files(self):
        """Проверка наличия музыкальных файлов"""
        found_files = []

        for track in self.tracks:
            if os.path.exists(track["full_path"]):
                found_files.append(track["name"])
                print(f"✅ Найден: {track['file']}")
            else:
                print(f"❌ Не найден: {track['file']}")

                # Создаем пустой файл-заглушку (только для демо)
                try:
                    with open(track["full_path"], 'w') as f:
                        f.write("Placeholder for music file")
                except:
                    pass

        if found_files:
            self.files_status.setText(f"✅ Найдено файлов: {len(found_files)}/{len(self.tracks)}")
            self.play_btn.setEnabled(self.audio_available)
            self.stop_btn.setEnabled(self.audio_available)
        else:
            self.files_status.setText("📝 Положите MP3 файлы в папку music")
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)

    def toggle_play(self):
        """Воспроизведение/пауза"""
        if not self.audio_available or not self.pygame:
            self.show_install_instructions()
            return

        current_track = self.tracks[self.track_combo.currentIndex()]

        if not os.path.exists(current_track["full_path"]):
            self.status_label.setText(f"❌ Файл не найден: {current_track['file']}")
            return

        try:
            if self.is_playing:
                self.pygame.mixer.music.pause()
                self.play_btn.setText("▶")
                self.status_label.setText(f"⏸ Пауза")
                self.is_playing = False
            else:
                self.pygame.mixer.music.stop()

                self.pygame.mixer.music.load(current_track["full_path"])
                self.pygame.mixer.music.play(-1)
                self.pygame.mixer.music.set_volume(self.volume / 100)
                self.play_btn.setText("⏸")
                self.status_label.setText(f"▶ Играет: {current_track['name']}")
                self.is_playing = True

        except Exception as e:
            print(f"❌ Ошибка воспроизведения: {e}")
            self.status_label.setText(f"❌ Ошибка воспроизведения")
            self.audio_available = False

    def stop_music(self):
        """Остановка музыки"""
        if not self.audio_available or not self.pygame:
            return

        try:
            self.pygame.mixer.music.stop()
            self.is_playing = False
            self.play_btn.setText("▶")
            self.status_label.setText("⏸ Остановлено")
        except Exception as e:
            print(f"Ошибка остановки: {e}")

    def change_track(self, index):
        """Смена трека"""
        self.current_track_index = index
        if self.is_playing:
            self.stop_music()

        track = self.tracks[index]
        if os.path.exists(track["full_path"]):
            self.status_label.setText(f"Выбран: {track['name']}")
        else:
            self.status_label.setText(f"❌ Файл {track['file']} не найден")

    def change_volume(self, value):
        """Изменение громкости"""
        self.volume = value
        self.volume_value.setText(f"{value}%")
        if self.audio_available and self.pygame and self.is_playing:
            try:
                self.pygame.mixer.music.set_volume(value / 100)
            except:
                pass

    def show_install_instructions(self):
        """Показать инструкции по установке"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Настройка музыки")
        msg.setText("🎵 Настройка музыкального плеера")
        msg.setInformativeText(
            "Установите pygame:\n\n"
            "pip install pygame\n\n"
            "После установки перезапустите приложение."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def closeEvent(self, event):
        """При закрытии останавливаем музыку"""
        self.stop_music()
        event.accept()


class MusicButton(QPushButton):
    """Кнопка для вызова музыкального плеера"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("🎵")
        self.setFixedSize(50, 50)
        self.setStyleSheet("""
            QPushButton {
                background-color: #B5E5CF;
                border: 2px solid #9BD1B8;
                border-radius: 25px;
                font-size: 24px;
                color: #2C3E50;
            }
            QPushButton:hover {
                background-color: #9BD1B8;
            }
        """)
        self.music_player = None
        self.clicked.connect(self.show_music_player)

    def show_music_player(self):
        """Показать музыкальный плеер"""
        if not self.music_player:
            self.music_player = SimpleMusicPlayer()

        if self.music_player.isVisible():
            self.music_player.hide()
        else:
            # Центрируем относительно главного окна
            main_window = self.window()
            if main_window:
                main_rect = main_window.geometry()
                player_rect = self.music_player.geometry()

                x = main_rect.x() + (main_rect.width() - player_rect.width()) // 2
                y = main_rect.y() + (main_rect.height() - player_rect.height()) // 2

                self.music_player.move(x, y)

            self.music_player.show()
            self.music_player.raise_()