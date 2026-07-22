"""
训练报告弹窗 - 训练结束后显示本次训练的完整报告
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from .styles import AppStyles
from core.translations import Translations as T


class TrainingReportDialog(QDialog):
    """训练报告弹窗"""

    saved = pyqtSignal(dict)
    discarded = pyqtSignal()

    def __init__(self, report_data, parent=None):
        super().__init__(parent)
        self.report_data = report_data
        self.setWindowTitle("训练报告")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {AppStyles.BG};
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("训练报告")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #1D1D1F;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        time_label = QLabel(self.report_data.get('timestamp', ''))
        time_label.setStyleSheet("font-size: 13px; color: #86868B;")
        time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(time_label)

        stats_card = QWidget()
        stats_card.setStyleSheet(AppStyles.get_card_style())
        stats_layout = QHBoxLayout(stats_card)
        stats_layout.setContentsMargins(16, 12, 16, 12)

        exercise_name = T.get_exercise_display_name(self.report_data.get('exercise_type', ''))
        duration = self.report_data.get('duration_sec', 0)
        mins = duration // 60
        secs = duration % 60

        stats = [
            ("运动", exercise_name),
            ("时长", f"{mins:02d}:{secs:02d}"),
            ("次数", str(self.report_data.get('rep_count', 0)))
        ]
        for label_text, value_text in stats:
            col = QVBoxLayout()
            col.setSpacing(2)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 11px; color: #86868B; font-weight: 500;")
            lbl.setAlignment(Qt.AlignCenter)
            val = QLabel(value_text)
            val.setStyleSheet("font-size: 18px; font-weight: 600; color: #1D1D1F;")
            val.setAlignment(Qt.AlignCenter)
            col.addWidget(lbl)
            col.addWidget(val)
            stats_layout.addLayout(col, 1)

        layout.addWidget(stats_card)

        score_card = QWidget()
        score_card.setStyleSheet(AppStyles.get_card_style())
        score_layout = QVBoxLayout(score_card)
        score_layout.setContentsMargins(16, 12, 16, 12)
        score_layout.setSpacing(8)

        score_header = QHBoxLayout()
        score_title = QLabel("安全评分")
        score_title.setStyleSheet("font-size: 13px; color: #86868B; font-weight: 500;")
        score_header.addWidget(score_title)
        score_header.addStretch()

        risk_score = self.report_data.get('risk_score', 100)
        if risk_score >= 90:
            score_color = "#34C759"
        elif risk_score >= 70:
            score_color = "#FF9500"
        elif risk_score >= 50:
            score_color = "#FF6B00"
        else:
            score_color = "#FF3B30"

        score_value = QLabel(str(risk_score))
        score_value.setStyleSheet(f"font-size: 32px; font-weight: 700; color: {score_color};")
        score_header.addWidget(score_value)
        score_layout.addLayout(score_header)

        overall = QLabel(self.report_data.get('overall', ''))
        overall.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {score_color};")
        score_layout.addWidget(overall)

        layout.addWidget(score_card)

        risk_items = self.report_data.get('risk_items', [])
        if risk_items:
            risk_card = QWidget()
            risk_card.setStyleSheet(AppStyles.get_card_style())
            risk_layout = QVBoxLayout(risk_card)
            risk_layout.setContentsMargins(16, 12, 16, 12)
            risk_layout.setSpacing(6)

            risk_title = QLabel("风险提示")
            risk_title.setStyleSheet("font-size: 13px; color: #86868B; font-weight: 500;")
            risk_layout.addWidget(risk_title)

            for item in risk_items:
                color = "#FF3B30" if item['level'] >= 2 else "#FF9500"
                item_label = QLabel(f"  {item['text']}")
                item_label.setStyleSheet(f"font-size: 13px; color: {color};")
                item_label.setWordWrap(True)
                risk_layout.addWidget(item_label)

            layout.addWidget(risk_card)

        suggestion = self.report_data.get('suggestion', '')
        if suggestion:
            suggest_card = QWidget()
            suggest_card.setStyleSheet(AppStyles.get_card_style())
            suggest_layout = QVBoxLayout(suggest_card)
            suggest_layout.setContentsMargins(16, 12, 16, 12)

            suggest_title = QLabel("训练建议")
            suggest_title.setStyleSheet("font-size: 13px; color: #86868B; font-weight: 500;")
            suggest_layout.addWidget(suggest_title)

            suggest_text = QLabel(suggestion)
            suggest_text.setStyleSheet("font-size: 14px; color: #1D1D1F;")
            suggest_text.setWordWrap(True)
            suggest_layout.addWidget(suggest_text)

            layout.addWidget(suggest_card)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        discard_btn = QPushButton("不保存")
        discard_btn.setStyleSheet(AppStyles.get_secondary_button_style())
        discard_btn.clicked.connect(self._on_discard)
        btn_row.addWidget(discard_btn)

        save_btn = QPushButton("保存记录")
        save_btn.setStyleSheet(AppStyles.get_primary_button_style())
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _on_save(self):
        self.saved.emit(self.report_data)
        self.accept()

    def _on_discard(self):
        self.discarded.emit()
        self.reject()