# widgets/animated.py
"""Анимированные виджеты"""

from PyQt5.QtWidgets import QStackedWidget, QPushButton
from PyQt5.QtCore import QPropertyAnimation, QPoint, QEasingCurve, QRect

class AnimatedStackedWidget(QStackedWidget):
    """StackedWidget с анимацией перехода между окнами"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation_duration = 400
        self.next_index = None
        self.current_animation = None

    def setCurrentIndexWithAnimation(self, index):
        """Плавный переход к окну с индексом index"""
        if index == self.currentIndex():
            return

        if self.current_animation:
            self.current_animation.stop()

        self.next_index = index
        self.start_animation()

    def start_animation(self):
        """Запуск анимации перехода"""
        current_widget = self.currentWidget()
        next_widget = self.widget(self.next_index)

        if not current_widget or not next_widget:
            super().setCurrentIndex(self.next_index)
            return

        if self.next_index > self.currentIndex():
            next_widget.move(self.width(), 0)
        else:
            next_widget.move(-self.width(), 0)

        next_widget.show()
        next_widget.raise_()

        anim_current = QPropertyAnimation(current_widget, b"pos")
        anim_current.setDuration(self.animation_duration)
        anim_current.setStartValue(QPoint(0, 0))

        if self.next_index > self.currentIndex():
            anim_current.setEndValue(QPoint(-self.width(), 0))
        else:
            anim_current.setEndValue(QPoint(self.width(), 0))

        anim_current.setEasingCurve(QEasingCurve.OutCubic)

        anim_next = QPropertyAnimation(next_widget, b"pos")
        anim_next.setDuration(self.animation_duration)
        anim_next.setStartValue(next_widget.pos())
        anim_next.setEndValue(QPoint(0, 0))
        anim_next.setEasingCurve(QEasingCurve.OutCubic)

        anim_next.finished.connect(lambda: self.finish_animation())

        anim_current.start()
        anim_next.start()

        self.current_animation = anim_next

    def finish_animation(self):
        """Завершение анимации"""
        if self.current_animation:
            self.current_animation.stop()
            self.current_animation = None

        super().setCurrentIndex(self.next_index)

        for i in range(self.count()):
            widget = self.widget(i)
            widget.move(0, 0)


class AnimatedButton(QPushButton):
    """Кнопка с анимацией нажатия и отпускания"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.animation_duration = 150

    def mousePressEvent(self, event):
        self.animate_press()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.animate_release()
        super().mouseReleaseEvent(event)

    def animate_press(self):
        """Анимация при нажатии"""
        animation = QPropertyAnimation(self, b"geometry")
        animation.setDuration(self.animation_duration)

        current = self.geometry()
        pressed = QRect(
            current.x(),
            current.y() + 2,
            current.width(),
            current.height()
        )

        animation.setStartValue(current)
        animation.setEndValue(pressed)
        animation.setEasingCurve(QEasingCurve.OutQuad)
        animation.start()

    def animate_release(self):
        """Анимация при отпускании"""
        animation = QPropertyAnimation(self, b"geometry")
        animation.setDuration(self.animation_duration)

        current = self.geometry()
        released = QRect(
            current.x(),
            current.y() - 2,
            current.width(),
            current.height()
        )

        animation.setStartValue(current)
        animation.setEndValue(released)
        animation.setEasingCurve(QEasingCurve.OutQuad)
        animation.start()