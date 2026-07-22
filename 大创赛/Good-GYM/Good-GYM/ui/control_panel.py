from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QComboBox, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import os
from .styles import AppStyles
from .custom_widgets import SwitchControl
from core.translations import Translations as T
from core.services import PathManager

try:
    from core.rtmpose_processor import _load_exercises_json as _load_cached_json
except ImportError:
    _load_cached_json = None


class ControlPanel(QWidget):
    """Control panel component - clean card-based layout"""

    exercise_changed = pyqtSignal(str)
    counter_reset = pyqtSignal()
    camera_changed = pyqtSignal(int)
    rotation_toggled = pyqtSignal(bool)
    skeleton_toggled = pyqtSignal(bool)
    counter_increase = pyqtSignal(int)
    counter_decrease = pyqtSignal(int)
    record_confirmed = pyqtSignal(str)
    model_changed = pyqtSignal(str)
    mirror_toggled = pyqtSignal(bool)
    device_changed = pyqtSignal(str)
    training_started = pyqtSignal()
    training_ended = pyqtSignal()
    training_paused = pyqtSignal()
    training_resumed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.exercise_colors = AppStyles.EXERCISE_COLORS
        self.exercise_display_map = self.load_exercise_display_map()
        self.model_display_map = {
            "lightweight": T.get("lightweight"),
            "balanced": T.get("balanced"),
            "performance": T.get("performance")
        }
        self.exercise_code_map = {v: k for k, v in self.exercise_display_map.items()}
        self.current_exercise = "overhead_press"

        # 训练状态管理（用属性而非按钮文字判断状态，避免 i18n 切换后行为错乱）
        self._training_state = 'idle'  # 'idle' | 'training' | 'paused'

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(12)
        self.setup_ui()

    def get_exercises_file_path(self):
        return PathManager.get_exercises_file_path()

    def load_exercise_display_map(self):
        if _load_cached_json is not None:
            data = _load_cached_json()
        else:
            exercises_file = PathManager.get_exercises_file_path()
            if os.path.exists(exercises_file):
                with open(exercises_file, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
            else:
                return {}
        exercises = data.get('exercises', {})
        exercise_map = {}
        current_lang = T.get_language()
        for exercise_type, config in exercises.items():
            if current_lang == 'zh':
                display_name = config.get('name_zh', '')
            elif current_lang == 'en':
                display_name = config.get('name_en', '')
            else:
                display_name = config.get('name_en', '')
            if not display_name:
                display_name = T.get(exercise_type)
            if display_name:
                exercise_map[exercise_type] = display_name
        return exercise_map

    # =====================================================================
    # UI Setup
    # =====================================================================

    def setup_ui(self):
        """Set up the clean card-based layout"""
        self._setup_counter_card()
        self._setup_settings_card()
        self._setup_display_card()
        self._setup_actions_card()
        self._setup_training_card()

        self.layout.addStretch()

    def _create_card(self):
        """Create a styled card widget"""
        card = QWidget()
        card.setStyleSheet(AppStyles.get_card_style())
        AppStyles.apply_card_shadow(card)
        return card

    def _create_caption(self, text):
        """Create a caption label"""
        lbl = QLabel(text)
        lbl.setStyleSheet(AppStyles.get_caption_style())
        return lbl

    def _setup_counter_card(self):
        """Card 1: Counter + Phase indicator"""
        card = self._create_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        counter_caption = self._create_caption(T.get("count_completed"))
        counter_caption.setAlignment(Qt.AlignCenter)
        layout.addWidget(counter_caption)

        self.counter_value = QLabel("0")
        self.counter_value.setStyleSheet(AppStyles.get_counter_value_style())
        self.counter_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.counter_value)

        pills = QHBoxLayout()
        pills.setSpacing(6)
        pills.setAlignment(Qt.AlignCenter)

        self.up_indicator = QLabel(T.get("up"))
        self.up_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
        self.up_indicator.setAlignment(Qt.AlignCenter)
        pills.addWidget(self.up_indicator)

        self.down_indicator = QLabel(T.get("down"))
        self.down_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
        self.down_indicator.setAlignment(Qt.AlignCenter)
        pills.addWidget(self.down_indicator)

        layout.addLayout(pills)

        self.stage_value = QLabel(T.get("prepare"))
        self.stage_value.setStyleSheet(AppStyles.get_stage_text_style())
        self.stage_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stage_value)

        self.layout.addWidget(card)

    def _setup_settings_card(self):
        """Card 2: Exercise, Model, Camera dropdowns"""
        card = self._create_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        ex_col = QVBoxLayout()
        ex_col.setSpacing(4)
        ex_col.addWidget(self._create_caption(T.get("exercise_type")))

        self.exercise_combo = QComboBox()
        self.exercise_combo.setStyleSheet(AppStyles.get_combo_style())
        for code, display in self.exercise_display_map.items():
            self.exercise_combo.addItem(display)
        overhead_press_text = self.exercise_display_map.get("overhead_press", "")
        if overhead_press_text:
            self.exercise_combo.setCurrentText(overhead_press_text)
        self.exercise_combo.currentTextChanged.connect(self._on_exercise_changed)
        ex_col.addWidget(self.exercise_combo)
        row1.addLayout(ex_col, 1)

        model_col = QVBoxLayout()
        model_col.setSpacing(4)
        model_col.addWidget(self._create_caption(T.get("model_type")))

        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet(AppStyles.get_combo_style())
        for model_code, model_display in self.model_display_map.items():
            self.model_combo.addItem(model_display, model_code)
        rtmpose_lightweight_index = list(self.model_display_map.keys()).index("lightweight")
        self.model_combo.setCurrentIndex(rtmpose_lightweight_index)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        model_col.addWidget(self.model_combo)
        row1.addLayout(model_col, 1)

        layout.addLayout(row1)

        cam_col = QVBoxLayout()
        cam_col.setSpacing(4)
        cam_col.addWidget(self._create_caption(T.get("camera")))

        self.camera_combo = QComboBox()
        from core.video_thread import scan_available_cameras
        cameras = scan_available_cameras()
        if not cameras:
            cameras = [(0, "摄像头 0")]
        self._camera_ids = []
        self.camera_combo.blockSignals(True)
        for cam_id, cam_name in cameras:
            self.camera_combo.addItem(cam_name)
            self._camera_ids.append(cam_id)
        self.camera_combo.blockSignals(False)
        self.camera_combo.currentIndexChanged.connect(self._on_camera_changed)
        self.camera_combo.setStyleSheet(AppStyles.get_combo_style())
        cam_col.addWidget(self.camera_combo)
        layout.addLayout(cam_col)

        self.layout.addWidget(card)

    def _setup_display_card(self):
        """Card 3: Display toggles in 2x2 grid"""
        card = self._create_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(16)

        self.rotation_switch = SwitchControl(T.get("rotation_mode"))
        self.rotation_switch.switched.connect(self._on_rotation_toggled)
        grid.addWidget(self.rotation_switch, 0, 0)

        self.skeleton_switch = SwitchControl(T.get("skeleton_display"))
        self.skeleton_switch.switched.connect(self._on_skeleton_toggled)
        grid.addWidget(self.skeleton_switch, 0, 1)

        self.mirror_switch = SwitchControl(T.get("mirror_mode"))
        self.mirror_switch.switched.connect(self._on_mirror_toggled)
        grid.addWidget(self.mirror_switch, 1, 0)

        self.gpu_switch = SwitchControl(T.get("gpu_acceleration"))
        self.gpu_switch.setChecked(False)
        self.gpu_switch.setEnabled(False)
        self.gpu_switch.switched.connect(self._on_device_toggled)
        grid.addWidget(self.gpu_switch, 1, 1)

        layout.addLayout(grid)
        self.layout.addWidget(card)

    def _setup_actions_card(self):
        """Card 4: Counter buttons + Action buttons"""
        card = self._create_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.decrease_button = QPushButton(T.get("decrease"))
        self.decrease_button.setStyleSheet(AppStyles.get_counter_button_style("decrease"))
        self.decrease_button.clicked.connect(self._on_decrease_counter)
        action_row.addWidget(self.decrease_button)

        self.reset_button = QPushButton(T.get("reset"))
        self.reset_button.setStyleSheet(AppStyles.get_secondary_button_style())
        self.reset_button.clicked.connect(self._on_reset_counter)
        action_row.addWidget(self.reset_button, 1)

        self.confirm_button = QPushButton(T.get("confirm"))
        self.confirm_button.setStyleSheet(AppStyles.get_primary_button_style())
        self.confirm_button.clicked.connect(self._on_confirm_record)
        action_row.addWidget(self.confirm_button, 1)

        self.increase_button = QPushButton(T.get("increase"))
        self.increase_button.setStyleSheet(AppStyles.get_counter_button_style("increase"))
        self.increase_button.clicked.connect(self._on_increase_counter)
        action_row.addWidget(self.increase_button)

        layout.addLayout(action_row)
        self.layout.addWidget(card)

    def _setup_training_card(self):
        """训练会话控制卡片"""
        card = self._create_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 24px; font-weight: 300; color: #8E8E93;")
        layout.addWidget(self.timer_label)

        self.risk_score_label = QLabel("安全评分: 100")
        self.risk_score_label.setAlignment(Qt.AlignCenter)
        self.risk_score_label.setStyleSheet("font-size: 12px; color: #34C759; font-weight: 500;")
        layout.addWidget(self.risk_score_label)

        self.training_button = QPushButton("开始训练")
        self.training_button.setStyleSheet(AppStyles.get_primary_button_style())
        self.training_button.clicked.connect(self._on_training_button)
        layout.addWidget(self.training_button)

        self.pause_button = QPushButton("暂停")
        self.pause_button.setStyleSheet(AppStyles.get_secondary_button_style())
        self.pause_button.clicked.connect(self._on_pause_button)
        self.pause_button.setVisible(False)
        layout.addWidget(self.pause_button)

        self.layout.addWidget(card)

    def _on_training_button(self):
        if self._training_state == 'idle':
            self._training_state = 'training'
            self.training_started.emit()
        else:
            self._training_state = 'idle'
            self.training_ended.emit()

    def _on_pause_button(self):
        if self._training_state == 'training':
            self._training_state = 'paused'
            self.training_paused.emit()
        else:
            self._training_state = 'training'
            self.training_resumed.emit()

    def update_timer(self, time_str):
        """更新计时器显示"""
        self.timer_label.setText(time_str)

    def update_risk_score(self, score):
        """更新风险评分"""
        if score >= 90:
            color = "#34C759"
        elif score >= 70:
            color = "#FF9500"
        elif score >= 50:
            color = "#FF6B00"
        else:
            color = "#FF3B30"
        self.risk_score_label.setText(f"安全评分: {score}")
        self.risk_score_label.setStyleSheet(f"font-size: 12px; color: {color}; font-weight: 500;")

    def set_training_state(self, state):
        """根据训练状态更新按钮"""
        self._training_state = state
        if state == 'training':
            self.training_button.setText("结束训练")
            self.training_button.setStyleSheet(AppStyles.get_counter_button_style("decrease"))
            self.pause_button.setText("暂停")
            self.pause_button.setVisible(True)
            self.exercise_combo.setEnabled(False)
            self.model_combo.setEnabled(False)
            self.camera_combo.setEnabled(False)
        elif state == 'paused':
            self.training_button.setText("结束训练")
            self.pause_button.setText("继续")
        elif state == 'idle':
            self.training_button.setText("开始训练")
            self.training_button.setStyleSheet(AppStyles.get_primary_button_style())
            self.pause_button.setVisible(False)
            self.timer_label.setText("00:00")
            self.risk_score_label.setText("安全评分: 100")
            self.risk_score_label.setStyleSheet("font-size: 12px; color: #34C759; font-weight: 500;")
            self.exercise_combo.setEnabled(True)
            self.model_combo.setEnabled(True)
            self.camera_combo.setEnabled(True)

    def set_training_ended(self):
        """训练结束，等待报告"""
        self.training_button.setText("开始训练")
        self.training_button.setStyleSheet(AppStyles.get_primary_button_style())
        self.pause_button.setVisible(False)
        self.exercise_combo.setEnabled(True)
        self.model_combo.setEnabled(True)
        self.camera_combo.setEnabled(True)

    # =====================================================================
    # Event Handlers
    # =====================================================================

    def _on_increase_counter(self):
        try:
            current_count = int(self.counter_value.text())
            new_count = current_count + 1
            self.counter_value.setText(str(new_count))
            self.counter_increase.emit(new_count)
            self.show_success_animation()
        except ValueError:
            self.counter_value.setText("1")
            self.counter_increase.emit(1)

    def _on_decrease_counter(self):
        try:
            current_count = int(self.counter_value.text())
            new_count = max(0, current_count - 1)
            self.counter_value.setText(str(new_count))
            self.counter_decrease.emit(new_count)
            self.update_counter_style()
        except ValueError:
            self.counter_value.setText("0")
            self.counter_decrease.emit(0)

    def _on_confirm_record(self):
        try:
            current_count = int(self.counter_value.text())
            if current_count > 0:
                self.record_confirmed.emit(self.current_exercise)
                self.confirm_button.setStyleSheet(AppStyles.get_success_button_style())
                QTimer.singleShot(1500, lambda: self.confirm_button.setStyleSheet(
                    AppStyles.get_primary_button_style()
                ))
        except ValueError:
            pass

    def _on_exercise_changed(self, exercise_display):
        if not exercise_display or exercise_display not in self.exercise_code_map:
            return
        exercise_code = self.exercise_code_map[exercise_display]
        self.current_exercise = exercise_code
        self.exercise_changed.emit(exercise_code)
        self.update_counter_style()

    def set_exercise(self, exercise_type):
        if exercise_type in self.exercise_display_map:
            display_name = self.exercise_display_map[exercise_type]
            self.exercise_combo.setCurrentText(display_name)
            self.current_exercise = exercise_type

    def _on_reset_counter(self):
        self.counter_reset.emit()

    def _on_camera_changed(self, index):
        if 0 <= index < len(self._camera_ids):
            real_id = self._camera_ids[index]
            self.camera_changed.emit(real_id)

    def _on_rotation_toggled(self, checked):
        self.rotation_toggled.emit(checked)

    def _on_skeleton_toggled(self, checked):
        self.skeleton_toggled.emit(checked)

    def _on_model_changed(self, index):
        model_mode = self.model_combo.currentData()
        self.model_changed.emit(model_mode)

    def _on_mirror_toggled(self, checked):
        self.mirror_toggled.emit(checked)

    def _on_device_toggled(self, checked):
        self.device_changed.emit('cuda' if checked else 'cpu')

    def set_gpu_available(self, available):
        self.gpu_switch.setEnabled(available)
        self.gpu_switch.setChecked(available)

    def update_counter(self, value):
        old_count = int(self.counter_value.text() or "0")
        new_count = int(value)
        self.counter_value.setText(str(value))
        if new_count > old_count:
            self.show_success_animation()

    def update_phase(self, stage):
        if stage == "up":
            self.stage_value.setText(T.get("up"))
            self.up_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(True))
            self.down_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
        elif stage == "down":
            self.stage_value.setText(T.get("down"))
            self.up_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
            self.down_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(True))
        else:
            self.stage_value.setText(T.get("prepare"))
            self.up_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
            self.down_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))

    def show_success_animation(self):
        self.counter_value.setStyleSheet(AppStyles.get_success_counter_style())

    def update_counter_style(self):
        try:
            current_exercise = self.exercise_display_map.get(self.current_exercise, "")
            if current_exercise in AppStyles.EXERCISE_COLORS:
                current_color = AppStyles.EXERCISE_COLORS[current_exercise]
            else:
                current_color = "#1D1D1F"
            self.counter_value.setStyleSheet(AppStyles.get_counter_value_style(current_color))
        except Exception as e:
            print(f"Error in update_counter_style: {e}")
            self.counter_value.setStyleSheet(AppStyles.get_counter_value_style("#1D1D1F"))

    def reset_counter_style(self):
        try:
            current_exercise = self.exercise_display_map.get(self.current_exercise, "")
            if current_exercise in AppStyles.EXERCISE_COLORS:
                current_color = AppStyles.EXERCISE_COLORS[current_exercise]
            else:
                current_color = "#1D1D1F"
            self.counter_value.setStyleSheet(AppStyles.get_counter_value_style(current_color))
        except Exception as e:
            print(f"Error in reset_counter_style: {e}")
            self.counter_value.setStyleSheet(AppStyles.get_counter_value_style("#1D1D1F"))

    def update_language(self):
        self.exercise_display_map = self.load_exercise_display_map()
        self.model_display_map = {
            "lightweight": T.get("lightweight"),
            "balanced": T.get("balanced"),
            "performance": T.get("performance")
        }
        self.exercise_code_map = {v: k for k, v in self.exercise_display_map.items()}

        self.rotation_switch.label.setText(T.get("rotation_mode"))
        self.skeleton_switch.label.setText(T.get("skeleton_display"))
        self.mirror_switch.label.setText(T.get("mirror_mode"))
        self.gpu_switch.label.setText(T.get("gpu_acceleration"))

        self.increase_button.setText(T.get("increase"))
        self.decrease_button.setText(T.get("decrease"))
        self.reset_button.setText(T.get("reset"))
        self.confirm_button.setText(T.get("confirm"))

        self._update_combo_items(self.exercise_combo, self.exercise_display_map)
        self._update_combo_items(self.model_combo, self.model_display_map)

    def _update_combo_items(self, combo_box, item_map):
        current_data = combo_box.currentData()
        current_text = combo_box.currentText()
        combo_box.clear()
        for code, display in item_map.items():
            combo_box.addItem(display, code)
        if current_data:
            for i in range(combo_box.count()):
                if combo_box.itemData(i) == current_data:
                    combo_box.setCurrentIndex(i)
                    break
        elif current_text:
            for i in range(combo_box.count()):
                if combo_box.itemText(i) == current_text:
                    combo_box.setCurrentIndex(i)
                    break