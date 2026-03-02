"""
Тёплое убежище - приложение для поддержки ментального здоровья
Главная точка входа
"""

import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MentalHealthApp


def main():
    """Запуск приложения"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MentalHealthApp()
    window.show()

    return sys.exit(app.exec_())


if __name__ == '__main__':
    main()