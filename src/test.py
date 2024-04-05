import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtCore import QRectF, QPropertyAnimation, QEasingCurve, Qt, pyqtProperty
from PyQt5.QtGui import QPainter, QColor

class EyelidWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.eye_center = (100, 100)
        self.eye_radius = 50
        self.blink_up = 10
        self.blink_down = 10
        self.eyelid_color = QColor(Qt.gray)

        # Initial start and span angles
        self._start_angle = 0
        self._span_angle = 180

        # Create animation objects for custom properties
        self.start_angle_animation = QPropertyAnimation(self, b"_start_angle")
        self.span_angle_animation = QPropertyAnimation(self, b"_span_angle")

        # Set animation duration and easing curve
        self.start_angle_animation.setDuration(1000)
        self.span_angle_animation.setDuration(1000)
        self.start_angle_animation.setEasingCurve(QEasingCurve.Linear)
        self.span_angle_animation.setEasingCurve(QEasingCurve.Linear)

        # Connect finished signals to animation loop
        self.start_angle_animation.finished.connect(self.animate)
        self.span_angle_animation.finished.connect(self.animate)

        # Start the animation loop
        self.animate()

    # Define custom properties for animation
    def _get_start_angle(self):
        return self._start_angle

    def _set_start_angle(self, value):
        self._start_angle = value
        self.update()

    start_angle = pyqtProperty(int, _get_start_angle, _set_start_angle)

    def _get_span_angle(self):
        return self._span_angle

    def _set_span_angle(self, value):
        self._span_angle = value
        self.update()

    span_angle = pyqtProperty(int, _get_span_angle, _set_span_angle)

    def animate(self):
        # Set random values for start and span angles
        self.start_angle_animation.setStartValue(0)
        self.start_angle_animation.setEndValue(360)
        self.start_angle_animation.start()

        self.span_angle_animation.setStartValue(180)
        self.span_angle_animation.setEndValue(0)
        self.span_angle_animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        eyelid_rect_top = QRectF(self.eye_center[0] - self.eye_radius - self.eye_radius * 0.25, 
                                 self.eye_center[1] - self.eye_radius - self.eye_radius * 0.25,
                                 (self.eye_radius * 1.2) * 2, 
                                 self.eye_radius + self.blink_up)
        
        eyelid_rect_bot = QRectF(self.eye_center[0] - self.eye_radius - self.eye_radius * 0.25, 
                                 self.eye_center[1] - self.eye_radius + self.eye_radius * 0.75,
                                 (self.eye_radius * 1.2) * 2, 
                                 self.eye_radius + self.blink_down)

        painter.setBrush(self.eyelid_color)
        painter.setPen(Qt.NoPen)

        painter.drawChord(eyelid_rect_top, self.start_angle * 16, self.span_angle * 16)
        painter.drawChord(eyelid_rect_bot, (-self.start_angle) * 16, (-self.span_angle) * 16)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    eyelid_widget = EyelidWidget()
    window.setCentralWidget(eyelid_widget)
    window.setGeometry(100, 100, 300, 200)
    window.setWindowTitle("Eyelid Animation")
    window.show()
    sys.exit(app.exec_())
