from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal
from .styles import AppStyles
from .custom_widgets import SwitchControl
from core.translations import Translations as T


class SafetyPanel(QWidget):
    """Safety monitoring panel - clean card-based layout"""

    voice_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_level = -1
        self._last_messages = ""
        self._last_stats_text = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        card = QWidget()
        card.setStyleSheet(AppStyles.get_card_style())
        AppStyles.apply_card_shadow(card)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(10)

        title_label = QLabel(T.get("safety_monitor"))
        title_label.setStyleSheet(AppStyles.get_caption_style())
        card_layout.addWidget(title_label)

        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        status_row.setAlignment(Qt.AlignLeft)

        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet("background-color: #34C759; border-radius: 4px;")
        status_row.addWidget(self.status_dot)

        self.status_indicator = QLabel(T.get("safe"))
        self.status_indicator.setStyleSheet(
            "font-size: 17px; font-weight: 600; color: #34C759;"
        )
        status_row.addWidget(self.status_indicator)
        status_row.addStretch()

        card_layout.addLayout(status_row)

        bubble_container = QHBoxLayout()
        bubble_container.setSpacing(10)

        self.avatar = QLabel()
        self.avatar.setFixedSize(24, 24)
        self.avatar.setStyleSheet("""
            QLabel {
                background-color: #34C759;
                border-radius: 12px;
            }
        """)
        bubble_container.addWidget(self.avatar)

        self.messages_label = QLabel(T.get("action_standard"))
        self.messages_label.setWordWrap(True)
        self.messages_label.setMinimumHeight(48)
        self.messages_label.setStyleSheet(AppStyles.get_chat_bubble_style("#34C759", "#F0F0F5"))
        bubble_container.addWidget(self.messages_label)

        card_layout.addLayout(bubble_container)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)
        bottom_row.setAlignment(Qt.AlignVCenter)

        self.stats_label = QLabel(T.get("safety_stats_format").format(total=0, warning=0, danger=0))
        self.stats_label.setStyleSheet("font-size: 12px; color: #86868B;")
        bottom_row.addWidget(self.stats_label)
        bottom_row.addStretch()

        self.voice_toggle = SwitchControl(T.get("voice_reminder"))
        self.voice_toggle.setChecked(True)
        self.voice_toggle.switched.connect(self.on_voice_toggled)
        bottom_row.addWidget(self.voice_toggle)

        card_layout.addLayout(bottom_row)
        layout.addWidget(card)

    def update_safety_status(self, safety_result):
        level = safety_result['level'].value

        if level != self._last_level:
            self._last_level = level

            if level == 0:
                self.status_dot.setStyleSheet("background-color: #34C759; border-radius: 4px;")
                self.status_indicator.setText(T.get("safe"))
                self.status_indicator.setStyleSheet(
                    "font-size: 17px; font-weight: 600; color: #34C759;"
                )
                self.avatar.setStyleSheet("""
                    QLabel {
                        background-color: #34C759;
                        border-radius: 12px;
                    }
                """)
                self.messages_label.setStyleSheet(AppStyles.get_chat_bubble_style("#34C759", "#F0F0F5"))
            elif level == 1:
                self.status_dot.setStyleSheet("background-color: #FF9F0A; border-radius: 4px;")
                self.status_indicator.setText(T.get("warning"))
                self.status_indicator.setStyleSheet(
                    "font-size: 17px; font-weight: 600; color: #FF9F0A;"
                )
                self.avatar.setStyleSheet("""
                    QLabel {
                        background-color: #FF9F0A;
                        border-radius: 12px;
                    }
                """)
                self.messages_label.setStyleSheet(AppStyles.get_chat_bubble_style("#FF9F0A", "#FFF5EE"))
            else:
                self.status_dot.setStyleSheet("background-color: #FF453A; border-radius: 4px;")
                self.status_indicator.setText(T.get("danger"))
                self.status_indicator.setStyleSheet(
                    "font-size: 17px; font-weight: 600; color: #FF453A;"
                )
                self.avatar.setStyleSheet("""
                    QLabel {
                        background-color: #FF453A;
                        border-radius: 12px;
                    }
                """)
                self.messages_label.setStyleSheet(AppStyles.get_chat_bubble_style("#FF453A", "#FFF0EE"))

        new_messages = "\n".join(safety_result['messages']) if safety_result['messages'] else T.get("action_standard")
        if new_messages != self._last_messages:
            self._last_messages = new_messages
            self.messages_label.setText(new_messages)

    def update_stats(self, stats):
        text = T.get("safety_stats_format").format(total=stats.get('total_checks', 0), warning=stats.get('warning_count', 0), danger=stats.get('danger_count', 0))
        if text != self._last_stats_text:
            self._last_stats_text = text
            self.stats_label.setText(text)

    def on_voice_toggled(self, checked):
        self.voice_toggled.emit(checked)

    def is_voice_enabled(self):
        return self.voice_toggle.isChecked()