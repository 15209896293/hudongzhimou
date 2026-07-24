"""
User Profile Panel - 可折叠的用户档案面板
用户录入个人身体信息和运动损伤史，为个性化安全阈值提供数据基础
"""

import os
import json
import datetime
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QComboBox, QSpinBox, QCheckBox, QGroupBox,
                             QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from .styles import AppStyles
from core.translations import Translations as T


class UserProfilePanel(QWidget):
    """可折叠的用户档案面板组件"""

    profile_saved = pyqtSignal(dict)
    profile_loaded = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_expanded = False
        self._data_file = self._get_profiles_file_path()
        self._current_user = "default"

        self.setup_ui()
        self._load_profile()

    def _get_profiles_file_path(self):
        """获取 user_profiles.json 文件路径，兼容开发环境和打包环境"""
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            external_file = os.path.join(exe_dir, 'data', 'user_profiles.json')
            if os.path.exists(os.path.dirname(external_file)):
                return external_file
            base_path = sys._MEIPASS
            return os.path.join(base_path, 'data', 'user_profiles.json')
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_dir, 'data', 'user_profiles.json')

    def setup_ui(self):
        """构建UI"""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # ── 标题栏（可点击展开/折叠）──
        self._header = QFrame()
        self._header.setCursor(Qt.PointingHandCursor)
        self._header.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                padding: 10px 16px;
                border: 1px solid #E5E5EA;
            }
            QFrame:hover {
                background-color: #F0F0F5;
            }
        """)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self._toggle_arrow = QLabel("▶")
        self._toggle_arrow.setStyleSheet("color: #86868B; font-size: 10pt;")
        self._toggle_arrow.setFixedWidth(16)
        header_layout.addWidget(self._toggle_arrow)

        self._header_label = QLabel(T.get("user_profile"))
        self._header_label.setStyleSheet("font-weight: 600; color: #1D1D1F; font-size: 15px;")
        header_layout.addWidget(self._header_label)

        header_layout.addStretch()

        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet("color: #86868B; font-size: 13px;")
        header_layout.addWidget(self._summary_label)

        self._header.mousePressEvent = self._toggle_expand
        self._layout.addWidget(self._header)

        # ── 内容区（折叠时隐藏）──
        self._content_frame = QFrame()
        self._content_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 0 0 12px 12px;
                padding: 20px;
                border: 1px solid #E5E5EA;
                border-top: none;
            }
        """)
        self._content_layout = QVBoxLayout(self._content_frame)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)

        self._build_form()

        self._content_frame.setVisible(False)
        self._layout.addWidget(self._content_frame)

    def _build_form(self):
        """构建表单字段"""
        info_group = QWidget()
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)

        # 姓名
        name_row = QHBoxLayout()
        name_label = QLabel(T.get("name") + ":")
        name_label.setFixedWidth(70)
        name_label.setStyleSheet("color: #86868B; font-size: 15px;")
        name_row.addWidget(name_label)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(T.get("name"))
        self.name_edit.setStyleSheet(AppStyles.get_input_style())
        name_row.addWidget(self.name_edit)
        info_layout.addLayout(name_row)

        # 性别
        gender_row = QHBoxLayout()
        gender_label = QLabel(T.get("gender") + ":")
        gender_label.setFixedWidth(70)
        gender_label.setStyleSheet("color: #86868B; font-size: 15px;")
        gender_row.addWidget(gender_label)
        self.gender_combo = QComboBox()
        self.gender_combo.addItem(T.get("male"), "male")
        self.gender_combo.addItem(T.get("female"), "female")
        self.gender_combo.setStyleSheet(AppStyles.get_input_style())
        gender_row.addWidget(self.gender_combo)
        info_layout.addLayout(gender_row)

        # 年龄
        age_row = QHBoxLayout()
        age_label = QLabel(T.get("age") + ":")
        age_label.setFixedWidth(70)
        age_label.setStyleSheet("color: #86868B; font-size: 15px;")
        age_row.addWidget(age_label)
        self.age_spin = QSpinBox()
        self.age_spin.setRange(1, 120)
        self.age_spin.setValue(25)
        self.age_spin.setStyleSheet(AppStyles.get_input_style())
        age_row.addWidget(self.age_spin)
        age_row.addStretch()
        info_layout.addLayout(age_row)

        # 身高
        height_row = QHBoxLayout()
        height_label = QLabel(T.get("height") + ":")
        height_label.setFixedWidth(70)
        height_label.setStyleSheet("color: #86868B; font-size: 15px;")
        height_row.addWidget(height_label)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 250)
        self.height_spin.setValue(170)
        self.height_spin.setSuffix(" cm")
        self.height_spin.setStyleSheet(AppStyles.get_input_style())
        height_row.addWidget(self.height_spin)
        height_row.addStretch()
        info_layout.addLayout(height_row)

        # 体重
        weight_row = QHBoxLayout()
        weight_label = QLabel(T.get("weight") + ":")
        weight_label.setFixedWidth(70)
        weight_label.setStyleSheet("color: #86868B; font-size: 15px;")
        weight_row.addWidget(weight_label)
        self.weight_spin = QSpinBox()
        self.weight_spin.setRange(30, 200)
        self.weight_spin.setValue(65)
        self.weight_spin.setSuffix(" kg")
        self.weight_spin.setStyleSheet(AppStyles.get_input_style())
        weight_row.addWidget(self.weight_spin)
        weight_row.addStretch()
        info_layout.addLayout(weight_row)

        self._content_layout.addWidget(info_group)

        # 损伤史
        injury_title = QLabel(T.get("injury_history"))
        injury_title.setStyleSheet(AppStyles.get_section_title_style())
        self._content_layout.addWidget(injury_title)

        injury_layout = QVBoxLayout()
        injury_layout.setSpacing(6)

        self.injury_checkboxes = {}

        # 无损伤史
        self.no_injury_cb = QCheckBox(T.get("no_injury"))
        self.no_injury_cb.setChecked(True)
        self.no_injury_cb.stateChanged.connect(self._on_no_injury_toggled)
        self.no_injury_cb.setStyleSheet("""
            QCheckBox {
                background-color: #F0F0F5;
                border-radius: 100px;
                padding: 8px 16px;
                color: #1D1D1F;
                font-size: 14px;
                border: 1px solid #E5E5EA;
            }
            QCheckBox:checked {
                background-color: rgba(52, 199, 89, 0.08);
                color: #34C759;
                border-color: #34C759;
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
        """)
        injury_layout.addWidget(self.no_injury_cb)

        injury_keys = [
            ("left_knee", T.get("left_knee")),
            ("right_knee", T.get("right_knee")),
            ("lower_back", T.get("lower_back")),
            ("left_shoulder", T.get("left_shoulder")),
            ("right_shoulder", T.get("right_shoulder")),
            ("neck", T.get("neck")),
        ]

        for key, label in injury_keys:
            cb = QCheckBox(label)
            cb.stateChanged.connect(self._on_injury_changed)
            cb.setStyleSheet("""
                QCheckBox {
                    background-color: #F0F0F5;
                    border-radius: 100px;
                    padding: 8px 16px;
                    color: #1D1D1F;
                    font-size: 14px;
                    border: 1px solid #E5E5EA;
                }
                QCheckBox:checked {
                    background-color: rgba(52, 199, 89, 0.08);
                    color: #34C759;
                    border-color: #34C759;
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
            """)
            self.injury_checkboxes[key] = cb
            injury_layout.addWidget(cb)

        self._content_layout.addLayout(injury_layout)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.save_btn = QPushButton(T.get("save_profile"))
        self.save_btn.setStyleSheet(AppStyles.get_success_button_style())
        self.save_btn.clicked.connect(self._on_save_clicked)
        btn_row.addWidget(self.save_btn)

        self.reset_btn = QPushButton(T.get("reset_form"))
        self.reset_btn.setStyleSheet(AppStyles.get_reset_button_style())
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        btn_row.addWidget(self.reset_btn)

        self._content_layout.addLayout(btn_row)

        # 保存成功提示
        self._save_status = QLabel("")
        self._save_status.setAlignment(Qt.AlignCenter)
        self._save_status.setStyleSheet("""
            QLabel {
                color: #34C759;
                font-weight: 600;
                font-size: 14px;
                padding: 8px;
                background-color: rgba(52, 199, 89, 0.08);
                border-radius: 100px;
            }
        """)
        self._save_status.setVisible(False)
        self._content_layout.addWidget(self._save_status)

        # 错误提示
        self._error_label = QLabel("")
        self._error_label.setAlignment(Qt.AlignCenter)
        self._error_label.setStyleSheet("""
            QLabel {
                color: #FF453A;
                font-size: 13px;
                padding: 8px;
                background-color: rgba(255, 69, 58, 0.08);
                border-radius: 100px;
            }
        """)
        self._error_label.setVisible(False)
        self._content_layout.addWidget(self._error_label)

    def _toggle_expand(self, event):
        """切换展开/折叠状态"""
        self._is_expanded = not self._is_expanded
        self._content_frame.setVisible(self._is_expanded)
        if self._is_expanded:
            self._toggle_arrow.setText("▼")
        else:
            self._toggle_arrow.setText("▶")

    def _on_no_injury_toggled(self, state):
        """无损伤史复选框切换"""
        if state == Qt.Checked:
            for cb in self.injury_checkboxes.values():
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.blockSignals(False)

    def _on_injury_changed(self, state):
        """损伤史复选框变化"""
        if state == Qt.Checked:
            self.no_injury_cb.blockSignals(True)
            self.no_injury_cb.setChecked(False)
            self.no_injury_cb.blockSignals(False)

    def _get_injury_history(self):
        """获取当前选中的损伤史列表"""
        if self.no_injury_cb.isChecked():
            return []
        injuries = []
        for key, cb in self.injury_checkboxes.items():
            if cb.isChecked():
                injuries.append(key)
        return injuries

    def _collect_form_data(self):
        """收集表单数据为字典"""
        return {
            "name": self.name_edit.text().strip(),
            "gender": self.gender_combo.currentData(),
            "age": self.age_spin.value(),
            "height": self.height_spin.value(),
            "weight": self.weight_spin.value(),
            "injury_history": self._get_injury_history(),
        }

    def _validate_form(self):
        """验证表单，返回 (is_valid, error_message)"""
        data = self._collect_form_data()
        if not data["height"] or data["height"] <= 0:
            return False, T.get("height_weight_required")
        if not data["weight"] or data["weight"] <= 0:
            return False, T.get("height_weight_required")
        return True, ""

    def _on_save_clicked(self):
        """保存按钮点击"""
        self._error_label.setVisible(False)

        is_valid, error_msg = self._validate_form()
        if not is_valid:
            self._error_label.setText(error_msg)
            self._error_label.setVisible(True)
            QTimer.singleShot(3000, lambda: self._error_label.setVisible(False))
            return

        data = self._collect_form_data()
        self._save_profile(data)
        self._show_save_success()
        self._update_summary(data)
        self.profile_saved.emit(data)

    def _on_reset_clicked(self):
        """重置按钮点击"""
        self.name_edit.clear()
        self.gender_combo.setCurrentIndex(0)
        self.age_spin.setValue(25)
        self.height_spin.setValue(170)
        self.weight_spin.setValue(65)
        self.no_injury_cb.setChecked(True)
        for cb in self.injury_checkboxes.values():
            cb.setChecked(False)
        self._error_label.setVisible(False)
        self._save_status.setVisible(False)

    def _show_save_success(self):
        """显示保存成功提示，2秒后消失"""
        self._save_status.setText(T.get("profile_saved"))
        self._save_status.setVisible(True)
        QTimer.singleShot(2000, lambda: self._save_status.setVisible(False))

    def _update_summary(self, data):
        """更新标题栏上的摘要文字"""
        parts = []
        if data.get("height"):
            parts.append(f"{data['height']}cm")
        if data.get("weight"):
            parts.append(f"{data['weight']}kg")
        if data.get("injury_history"):
            parts.append(f"{len(data['injury_history'])}项损伤")
        self._summary_label.setText("  |  ".join(parts) if parts else "")

    # =====================================================================
    # 数据持久化
    # =====================================================================

    def _load_profile(self):
        """加载用户档案（启动时自动调用）"""
        if not os.path.exists(self._data_file):
            self._save_profile(self._collect_form_data(), initial=True)
            self._update_summary(self._collect_form_data())
            return

        try:
            with open(self._data_file, 'r', encoding='utf-8') as f:
                profiles_data = json.load(f)

            current_user = profiles_data.get("current_user", "default")
            users = profiles_data.get("users", {})
            user_data = users.get(current_user, {})

            self._populate_form(user_data)
            self._update_summary(user_data)
            self.profile_loaded.emit(user_data)

        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading user profile: {e}")
            self._save_profile(self._collect_form_data(), initial=True)

    def _populate_form(self, data):
        """用数据填充表单"""
        if not data:
            return

        if "name" in data:
            self.name_edit.setText(data["name"])
        if "gender" in data:
            idx = self.gender_combo.findData(data["gender"])
            if idx >= 0:
                self.gender_combo.setCurrentIndex(idx)
        if "age" in data and data["age"] is not None:
            self.age_spin.setValue(int(data["age"]))
        if "height" in data and data["height"] is not None:
            self.height_spin.setValue(int(data["height"]))
        if "weight" in data and data["weight"] is not None:
            self.weight_spin.setValue(int(data["weight"]))
        if "injury_history" in data:
            injuries = data["injury_history"]
            if not injuries:
                self.no_injury_cb.setChecked(True)
                for cb in self.injury_checkboxes.values():
                    cb.setChecked(False)
            else:
                self.no_injury_cb.setChecked(False)
                for key, cb in self.injury_checkboxes.items():
                    cb.setChecked(key in injuries)

    def _save_profile(self, data, initial=False):
        """保存用户档案到 JSON 文件"""
        os.makedirs(os.path.dirname(self._data_file), exist_ok=True)

        profiles_data = {
            "current_user": self._current_user,
            "users": {}
        }

        if os.path.exists(self._data_file) and not initial:
            try:
                with open(self._data_file, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        if "users" not in profiles_data:
            profiles_data["users"] = {}

        if self._current_user not in profiles_data["users"]:
            profiles_data["users"][self._current_user] = {}

        profiles_data["current_user"] = self._current_user
        profiles_data["users"][self._current_user] = {
            **profiles_data["users"].get(self._current_user, {}),
            **data,
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if "created_at" not in profiles_data["users"][self._current_user]:
            profiles_data["users"][self._current_user]["created_at"] = \
                datetime.datetime.now().strftime("%Y-%m-%d")

        try:
            with open(self._data_file, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving user profile: {e}")

    def update_language(self):
        """更新界面语言（语言切换时调用）"""
        self._header_label.setText(T.get("user_profile"))

        injury_labels = {
            "left_knee": T.get("left_knee"),
            "right_knee": T.get("right_knee"),
            "lower_back": T.get("lower_back"),
            "left_shoulder": T.get("left_shoulder"),
            "right_shoulder": T.get("right_shoulder"),
            "neck": T.get("neck"),
        }
        self.no_injury_cb.setText(T.get("no_injury"))
        for key, cb in self.injury_checkboxes.items():
            if key in injury_labels:
                cb.setText(injury_labels[key])

        current_gender = self.gender_combo.currentData()
        self.gender_combo.clear()
        self.gender_combo.addItem(T.get("male"), "male")
        self.gender_combo.addItem(T.get("female"), "female")
        idx = self.gender_combo.findData(current_gender)
        if idx >= 0:
            self.gender_combo.setCurrentIndex(idx)

        self.name_edit.setPlaceholderText(T.get("name"))
        self.height_spin.setSuffix(" cm")
        self.weight_spin.setSuffix(" kg")

        self.save_btn.setText(T.get("save_profile"))
        self.reset_btn.setText(T.get("reset_form"))

        self._update_summary(self._collect_form_data())