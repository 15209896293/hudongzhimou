"""
菜单管理模块 - 负责菜单栏的设置和语言切换

重构要点：
1. __init__ 接收 (main_window, app_state)，状态读写通过 app_state
2. 菜单动作创建后不立即连接，由 connect_actions() 统一连接到 AppController
3. change_language 重建菜单后会重新调用 connect_actions()
"""

from PyQt5.QtWidgets import QAction, QMessageBox
from core.translations import Translations as T


class MenuManager:
    """菜单管理器类"""

    def __init__(self, main_window, app_state):
        self.main_window = main_window
        self.state = app_state
        self.app_controller = None  # 由 main_window.connect_signals 注入

        # 菜单动作引用（connect_actions 时连接到 AppController）
        self.toggle_skeleton_action = None
        self.toggle_rotation_action = None
        self.open_action = None
        self.camera_mode_action = None
        self.workout_mode_action = None
        self.stats_mode_action = None
        self.chinese_action = None
        self.english_action = None
        self.about_action = None

    def set_app_controller(self, app_controller):
        """注入 AppController 引用，供 connect_actions 使用"""
        self.app_controller = app_controller

    def setup_menu_bar(self):
        """设置菜单栏（仅创建动作，不连接信号）"""
        menubar = self.main_window.menuBar()

        # 工具菜单
        tools_menu = menubar.addMenu(T.get("tools_menu"))

        self.toggle_skeleton_action = QAction(T.get("skeleton_display"), self.main_window, checkable=True)
        self.toggle_skeleton_action.setChecked(False)
        tools_menu.addAction(self.toggle_skeleton_action)

        self.toggle_rotation_action = QAction(T.get("rotation_mode"), self.main_window, checkable=True)
        self.toggle_rotation_action.setChecked(False)
        tools_menu.addAction(self.toggle_rotation_action)
        tools_menu.addSeparator()

        self.open_action = QAction(T.get("video_file"), self.main_window)
        self.open_action.setShortcut("Ctrl+O")
        tools_menu.addAction(self.open_action)

        self.camera_mode_action = QAction(T.get("camera_mode"), self.main_window)
        tools_menu.addAction(self.camera_mode_action)

        # 模式菜单
        mode_menu = menubar.addMenu(T.get("mode_menu"))
        self.workout_mode_action = QAction(T.get("workout_mode"), self.main_window)
        mode_menu.addAction(self.workout_mode_action)
        self.stats_mode_action = QAction(T.get("stats_mode"), self.main_window)
        mode_menu.addAction(self.stats_mode_action)

        # 语言菜单
        language_menu = menubar.addMenu(T.get("language_menu"))
        self.chinese_action = QAction(T.get("chinese"), self.main_window, checkable=True)
        self.chinese_action.setChecked(T.current_language == "zh")
        language_menu.addAction(self.chinese_action)
        self.english_action = QAction(T.get("english"), self.main_window, checkable=True)
        self.english_action.setChecked(T.current_language == "en")
        language_menu.addAction(self.english_action)

        # 帮助菜单
        help_menu = menubar.addMenu(T.get("help_menu"))
        self.about_action = QAction(T.get("about"), self.main_window)
        help_menu.addAction(self.about_action)

    def connect_actions(self):
        """将菜单动作连接到 AppController（setup_menu_bar 之后调用，语言切换后重新调用）"""
        if self.app_controller is None:
            return
        ctrl = self.app_controller

        self.toggle_skeleton_action.triggered.connect(ctrl.on_skeleton_toggled)
        self.toggle_rotation_action.triggered.connect(ctrl.on_rotation_toggled)
        self.open_action.triggered.connect(ctrl.on_open_video_file)
        self.camera_mode_action.triggered.connect(ctrl.on_switch_to_camera_mode)
        self.workout_mode_action.triggered.connect(ctrl.on_switch_to_workout_mode)
        self.stats_mode_action.triggered.connect(ctrl.on_switch_to_stats_mode)
        self.chinese_action.triggered.connect(lambda: ctrl.on_change_language("zh"))
        self.english_action.triggered.connect(lambda: ctrl.on_change_language("en"))
        self.about_action.triggered.connect(ctrl.on_show_about)

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self.main_window, T.get("about"), T.get("about_text"))

    def change_language(self, language):
        """更改界面语言（状态写入 AppState）"""
        if T.set_language(language):
            self.state.current_language = language

            # 更新菜单项选择状态
            self.chinese_action.setChecked(language == "zh")
            self.english_action.setChecked(language == "en")

            # 更新窗口标题
            self.main_window.setWindowTitle(T.get("app_title"))

            # 重建菜单并重新连接信号
            self.main_window.menuBar().clear()
            self.setup_menu_bar()
            self.connect_actions()

            # 更新控制面板文本
            if hasattr(self.main_window, 'control_panel'):
                self.main_window.control_panel.update_language()

            # 更新统计面板文本
            if hasattr(self.main_window, 'stats_panel'):
                self.main_window.stats_panel.update_language()

            # 更新用户档案面板文本
            if hasattr(self.main_window, 'user_profile_panel'):
                self.main_window.user_profile_panel.update_language()

            # 更新状态栏信息
            self.main_window.statusBar.showMessage(T.get("language_changed"))
