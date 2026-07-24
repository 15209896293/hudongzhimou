from PyQt5.QtWidgets import QPushButton, QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen


class ToggleSwitch(QPushButton):
    """iOS-style sliding switch button"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.setMinimumWidth(44)
        self.setMaximumWidth(44)
        self.setMinimumHeight(26)
        self.setMaximumHeight(26)

        self.on_color = QColor("#34C759")
        self.off_color = QColor("#E5E5EA")
        self.thumb_color = QColor("#FFFFFF")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg_color = self.on_color if self.isChecked() else self.off_color

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 13, 13)

        thumb_diameter = 22
        thumb_x = self.width() - thumb_diameter - 2 if self.isChecked() else 2
        painter.setBrush(QBrush(QColor(0, 0, 0, 38)))
        painter.drawEllipse(thumb_x, 3, thumb_diameter, thumb_diameter)
        painter.setBrush(QBrush(self.thumb_color))
        painter.drawEllipse(thumb_x, 2, thumb_diameter, thumb_diameter)


class SwitchControl(QWidget):
    """Sliding switch control with label"""

    switched = pyqtSignal(bool)

    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignVCenter)

        self.toggle = ToggleSwitch()
        self.toggle.toggled.connect(self.switched.emit)

        self.label = QLabel(label_text)
        self.label.setStyleSheet("color: #1D1D1F; font-size: 15px;")

        self.layout.addWidget(self.label)
        self.layout.addStretch()
        self.layout.addWidget(self.toggle)

    def isChecked(self):
        return self.toggle.isChecked()

    def setChecked(self, checked):
        self.toggle.setChecked(checked)

    def setText(self, text):
        self.label.setText(text)