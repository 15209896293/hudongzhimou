from PyQt5.QtGui import QColor, QPalette, QFont
from PyQt5.QtCore import Qt


class AppStyles:
    BG = "#F5F5F7"
    CARD = "#FFFFFF"
    SURFACE = "#FFFFFF"
    SURFACE_SUNKEN = "#EFEFF4"
    SURFACE_INSET = "#F0F0F5"
    TEXT = "#1D1D1F"
    TEXT2 = "#86868B"
    TEXT3 = "#AEAEB2"
    BORDER = "#E5E5EA"
    SEPARATOR = "#D2D2D7"
    GREEN = "#34C759"
    ORANGE = "#FF9F0A"
    RED = "#FF453A"
    BLUE = "#007AFF"
    BRAND = "#34C759"

    EXERCISE_COLORS = {
        "深蹲": "#34C759",
        "俯卧撑": "#FF453A",
        "仰卧起坐": "#007AFF",
        "二头弯举": "#FF9F0A",
        "三头臂屈伸": "#FF9F0A",
        "侧平举": "#AF52DE",
        "颈前推举": "#5AC8FA",
        "左右交替抬腿": "#FFCC00",
        "高抬腿": "#30D158",
        "提膝下压": "#AF52DE",
        "左侧提膝下压": "#AF52DE",
        "右侧提膝下压": "#BF5AF2",
        "Squat": "#34C759",
        "Push Up": "#FF453A",
        "Sit Up": "#007AFF",
        "Bicep Curl": "#FF9F0A",
        "Tricep Extension": "#FF9F0A",
        "Lateral Raise": "#AF52DE",
        "Overhead Press": "#5AC8FA",
        "Leg Raise": "#FFCC00",
        "Knee Raise": "#30D158",
        "Knee Press": "#AF52DE",
        "Left Knee Press": "#AF52DE",
        "Right Knee Press": "#BF5AF2"
    }

    @staticmethod
    def get_window_palette():
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(AppStyles.BG))
        palette.setColor(QPalette.WindowText, QColor(AppStyles.TEXT))
        palette.setColor(QPalette.Base, QColor(AppStyles.CARD))
        palette.setColor(QPalette.AlternateBase, QColor(AppStyles.SURFACE_INSET))
        palette.setColor(QPalette.Text, QColor(AppStyles.TEXT))
        palette.setColor(QPalette.Button, QColor(AppStyles.SURFACE_INSET))
        palette.setColor(QPalette.ButtonText, QColor(AppStyles.TEXT))
        return palette

    @staticmethod
    def get_global_stylesheet():
        return """
            QWidget {
                font-family: 'Inter', 'PingFang SC', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-size: 15px;
                font-weight: 400;
                color: #1D1D1F;
                background-color: #F5F5F7;
            }
            QComboBox {
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                padding: 8px 12px;
                background-color: #FFFFFF;
                color: #1D1D1F;
                min-height: 36px;
            }
            QComboBox:hover {
                border-color: #007AFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                selection-background-color: #007AFF;
                background-color: #FFFFFF;
                color: #1D1D1F;
                padding: 4px;
            }
            QLabel {
                color: #1D1D1F;
            }
            QCheckBox {
                spacing: 8px;
                color: #1D1D1F;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 6px;
                border: 1px solid #E5E5EA;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background-color: #34C759;
                border-color: #34C759;
            }
            QGroupBox {
                border: none;
                margin-top: 0;
                padding: 0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0;
                padding: 0;
                color: #86868B;
                font-size: 13px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """

    @staticmethod
    def get_exercise_combo_style():
        return """
            QComboBox {
                font-size: 15px;
                padding: 10px 14px;
                min-height: 40px;
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                background-color: #FFFFFF;
                color: #1D1D1F;
            }
            QComboBox:hover {
                border-color: #007AFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                selection-background-color: #007AFF;
                background-color: #FFFFFF;
                color: #1D1D1F;
            }
        """

    @staticmethod
    def get_camera_combo_style():
        return """
            QComboBox {
                font-size: 14px;
                padding: 8px 12px;
                min-height: 36px;
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                background-color: #FFFFFF;
                color: #1D1D1F;
            }
            QComboBox:hover {
                border-color: #007AFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                selection-background-color: #007AFF;
                background-color: #FFFFFF;
                color: #1D1D1F;
            }
        """

    @staticmethod
    def get_counter_value_style(color="#1D1D1F"):
        return f"""
            QLabel {{
                color: {color};
                background-color: transparent;
                border: none;
                min-width: 80px;
                text-align: center;
                font-size: 56pt;
                font-weight: 200;
                letter-spacing: -2px;
            }}
        """

    @staticmethod
    def get_success_counter_style():
        return """
            QLabel {
                color: #34C759;
                background-color: transparent;
                border: none;
                min-width: 80px;
                text-align: center;
                font-size: 56pt;
                font-weight: 200;
                letter-spacing: -2px;
            }
        """

    @staticmethod
    def get_angle_value_style(color="#1D1D1F", highlight=False):
        text_color = "#FF453A" if highlight else color
        return f"""
            QLabel {{
                color: {text_color};
                background-color: #FFFFFF;
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                padding: 8px 16px;
                min-width: 100px;
                text-align: center;
                font-size: 36pt;
                font-weight: 200;
            }}
        """

    @staticmethod
    def get_phase_indicator_style(active=False, color="#34C759"):
        bg_color = color if active else "#F0F0F5"
        text_color = "#FFFFFF" if active else "#86868B"
        border_color = "none" if active else "#E5E5EA"
        return f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {text_color};
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 100px;
                min-width: 80px;
                min-height: 32px;
                padding: 6px 16px;
                text-align: center;
            }}
        """

    @staticmethod
    def get_group_box_style():
        return """
            QGroupBox {
                border: none;
                margin-top: 0;
                padding: 0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0;
                padding: 0;
            }
        """

    @staticmethod
    def get_phase_group_style():
        return """
            QGroupBox {
                border: none;
                margin-top: 0;
                padding: 0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0;
                padding: 0;
                color: #86868B;
                font-size: 13px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """

    @staticmethod
    def get_increase_button_style():
        return """
            QPushButton {
                background-color: rgba(52, 199, 89, 0.1);
                color: #34C759;
                border-radius: 12px;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 15px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: rgba(52, 199, 89, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(52, 199, 89, 0.3);
            }
            QPushButton:disabled {
                background-color: #EFEFF4;
                color: #AEAEB2;
            }
        """

    @staticmethod
    def get_decrease_button_style():
        return """
            QPushButton {
                background-color: rgba(255, 159, 10, 0.1);
                color: #FF9F0A;
                border-radius: 12px;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 15px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: rgba(255, 159, 10, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 159, 10, 0.3);
            }
            QPushButton:disabled {
                background-color: #EFEFF4;
                color: #AEAEB2;
            }
        """

    @staticmethod
    def get_reset_button_style():
        return """
            QPushButton {
                background-color: #F0F0F5;
                color: #1D1D1F;
                border-radius: 12px;
                padding: 10px 16px;
                font-weight: 500;
                font-size: 15px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #E5E5EA;
            }
            QPushButton:pressed {
                background-color: #D2D2D7;
            }
            QPushButton:disabled {
                background-color: #EFEFF4;
                color: #AEAEB2;
            }
        """

    @staticmethod
    def get_confirm_button_style():
        return """
            QPushButton {
                background-color: #007AFF;
                color: #FFFFFF;
                border-radius: 12px;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 15px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0066D6;
            }
            QPushButton:pressed {
                background-color: #0052B3;
            }
            QPushButton:disabled {
                background-color: #EFEFF4;
                color: #AEAEB2;
            }
        """

    @staticmethod
    def get_success_button_style():
        return """
            QPushButton {
                background-color: #34C759;
                color: #FFFFFF;
                border-radius: 12px;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 15px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2DB84E;
            }
            QPushButton:pressed {
                background-color: #248A3D;
            }
            QPushButton:disabled {
                background-color: #EFEFF4;
                color: #AEAEB2;
            }
        """

    @staticmethod
    def get_toggle_button_style(checked=False):
        if checked:
            return """
                QPushButton {
                    background-color: #34C759;
                    color: #FFFFFF;
                    border-radius: 100px;
                    padding: 6px 20px;
                    font-weight: 600;
                    font-size: 13px;
                    border: none;
                    min-width: 50px;
                    max-width: 50px;
                    min-height: 28px;
                    max-height: 28px;
                }
                QPushButton:hover {
                    background-color: #2DB84E;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #E5E5EA;
                    color: #1D1D1F;
                    border-radius: 100px;
                    padding: 6px 20px;
                    font-weight: 500;
                    font-size: 13px;
                    border: none;
                    min-width: 50px;
                    max-width: 50px;
                    min-height: 28px;
                    max-height: 28px;
                }
                QPushButton:hover {
                    background-color: #D2D2D7;
                }
            """

    @staticmethod
    def get_card_style():
        return f"""
            background-color: {AppStyles.CARD};
            border-radius: 20px;
            padding: 16px;
        """

    @staticmethod
    def get_section_title_style():
        return """
            color: #86868B;
            font-size: 13px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        """

    @staticmethod
    def get_status_badge_style(level=0):
        colors = [
            {"bg": "rgba(52, 199, 89, 0.10)", "text": "#34C759"},
            {"bg": "rgba(255, 159, 10, 0.10)", "text": "#FF9F0A"},
            {"bg": "rgba(255, 69, 58, 0.10)", "text": "#FF453A"},
        ]
        c = colors[min(level, 2)]
        return f"""
            background-color: {c['bg']};
            color: {c['text']};
            border-radius: 100px;
            padding: 6px 16px;
            font-size: 13px;
            font-weight: 600;
        """

    @staticmethod
    def get_input_style():
        return """
            QLineEdit, QSpinBox, QComboBox {
                background-color: #FFFFFF;
                color: #1D1D1F;
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 15px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #007AFF;
                outline: none;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                width: 24px;
            }
        """

    @staticmethod
    def get_scrollbar_style():
        return """
            QScrollBar:vertical {
                background-color: #F0F0F5;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar:horizontal {
                background-color: #F0F0F5;
                height: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background-color: #AEAEB2;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal {
                background-color: #AEAEB2;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #86868B;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #86868B;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                height: 0;
                width: 0;
            }
        """

    @staticmethod
    def get_table_style():
        return """
            QTableWidget {
                background-color: #FFFFFF;
                border: none;
                gridline-color: #F0F0F5;
                color: #1D1D1F;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border: none;
            }
            QTableWidget::item:alternate {
                background-color: #F5F5F7;
            }
            QTableWidget::item:selected {
                background-color: rgba(0, 122, 255, 0.1);
                color: #1D1D1F;
            }
            QHeaderView::section {
                background-color: #F0F0F5;
                color: #1D1D1F;
                padding: 10px 12px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
            QTableWidget QScrollBar:vertical {
                background-color: #F0F0F5;
                width: 6px;
                border-radius: 3px;
            }
            QTableWidget QScrollBar::handle:vertical {
                background-color: #AEAEB2;
                border-radius: 3px;
            }
        """

    @staticmethod
    def get_progressbar_style(color="#34C759"):
        return f"""
            QProgressBar {{
                background-color: #E5E5EA;
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                color: transparent;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """

    @staticmethod
    def get_tab_widget_style():
        return """
            QTabWidget::pane {
                border: none;
                background-color: #F5F5F7;
            }
            QTabBar::tab {
                background-color: transparent;
                color: #86868B;
                padding: 8px 20px;
                border-radius: 100px;
                margin-right: 8px;
                font-size: 14px;
                font-weight: 500;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #1D1D1F;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                color: #1D1D1F;
            }
        """

    @staticmethod
    def get_statusbar_style():
        return """
            QStatusBar {
                background-color: #FFFFFF;
                color: #AEAEB2;
                border-top: 1px solid #E5E5EA;
                font-size: 11px;
            }
        """

    @staticmethod
    def get_panel_title_style():
        return """
            font-size: 17px;
            font-weight: 600;
            color: #1D1D1F;
            letter-spacing: 0px;
        """

    @staticmethod
    def get_caption_style():
        return """
            color: #86868B;
            font-size: 13px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        """

    @staticmethod
    def get_stage_text_style():
        return """
            color: #1D1D1F;
            font-size: 16px;
            font-weight: 600;
        """

    @staticmethod
    def get_combo_style():
        return """
            QComboBox {
                font-size: 14px;
                padding: 8px 12px;
                min-height: 36px;
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                background-color: #FFFFFF;
                color: #1D1D1F;
            }
            QComboBox:hover {
                border-color: #007AFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                selection-background-color: #007AFF;
                background-color: #FFFFFF;
                color: #1D1D1F;
                padding: 4px;
            }
        """

    @staticmethod
    def get_counter_button_style(btn_type="increase"):
        if btn_type == "increase":
            bg = "rgba(52, 199, 89, 0.1)"
            hover = "rgba(52, 199, 89, 0.2)"
            pressed = "rgba(52, 199, 89, 0.3)"
            text_color = "#34C759"
        elif btn_type == "decrease":
            bg = "rgba(255, 159, 10, 0.1)"
            hover = "rgba(255, 159, 10, 0.2)"
            pressed = "rgba(255, 159, 10, 0.3)"
            text_color = "#FF9F0A"
        else:
            bg = "#F0F0F5"
            hover = "#E5E5EA"
            pressed = "#D2D2D7"
            text_color = "#1D1D1F"
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {text_color};
                border-radius: 12px;
                padding: 8px;
                font-weight: 600;
                font-size: 16px;
                border: none;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {pressed};
            }}
            QPushButton:disabled {{
                background-color: #EFEFF4;
                color: #AEAEB2;
            }}
        """

    @staticmethod
    def get_primary_button_style():
        return """
            QPushButton {
                background-color: #007AFF;
                color: #FFFFFF;
                border-radius: 12px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 14px;
                border: none;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #0066D6;
            }
            QPushButton:pressed {
                background-color: #0052B3;
            }
            QPushButton:disabled {
                background-color: #EFEFF4;
                color: #AEAEB2;
            }
        """

    @staticmethod
    def get_secondary_button_style():
        return """
            QPushButton {
                background-color: #F0F0F5;
                color: #1D1D1F;
                border-radius: 12px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 14px;
                border: 1px solid #E5E5EA;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #E5E5EA;
                border-color: #D2D2D7;
            }
            QPushButton:pressed {
                background-color: #D2D2D7;
            }
            QPushButton:disabled {
                background-color: #EFEFF4;
                color: #AEAEB2;
                border-color: #E5E5EA;
            }
        """

    @staticmethod
    def get_divider_style():
        return """
            background-color: #E5E5EA;
            width: 1px;
        """

    @staticmethod
    def get_safety_gradient_bar_style():
        return """
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #34C759,
                    stop:0.5 #FF9F0A,
                    stop:1 #FF453A
                );
                border: none;
                border-radius: 0px;
            }
        """

    @staticmethod
    def get_chat_bubble_style(border_color="#34C759", bg_color="#F0F0F5"):
        return f"""
            QLabel {{
                padding: 12px 16px;
                background-color: {bg_color};
                border-radius: 12px;
                font-size: 15px;
                color: #1D1D1F;
                border-left: 3px solid {border_color};
            }}
        """

    @staticmethod
    def get_nav_bar_style():
        return """
            QWidget {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E5EA;
            }
        """

    @staticmethod
    def get_score_badge_style():
        return """
            QWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid #34C759;
                border-radius: 36px;
            }
        """

    @staticmethod
    def get_drawer_style():
        return """
            QWidget {
                background-color: #FFFFFF;
                border-left: 1px solid #E5E5EA;
            }
        """

    @staticmethod
    def apply_card_shadow(widget, offset_y=1, blur_radius=4, opacity=0.05):
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setOffset(0, offset_y)
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(QColor(0, 0, 0, int(opacity * 255)))
        widget.setGraphicsEffect(shadow)
        return shadow

    @staticmethod
    def get_dark_input_style():
        return """
            QSpinBox {
                background-color: #FFFFFF;
                color: #1D1D1F;
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 15px;
            }
            QSpinBox:focus {
                border-color: #007AFF;
                outline: none;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                width: 24px;
            }
        """