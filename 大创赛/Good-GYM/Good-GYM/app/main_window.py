"""
主窗口类 - 负责基本的UI设置和信号连接

重构后职责：
1. 创建 AppState、核心组件、各 Manager、FramePipeline、AppController
2. 设置 UI 布局（setup_ui）
3. 连接 UI 信号到 AppController（connect_signals）
4. 管理 VideoThread 生命周期（setup_video_thread / start_video / closeEvent）

不再持有业务状态变量，也不再包含业务方法中转。
"""

import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QStatusBar, QMessageBox, QScrollArea, QLabel)

from core.video_thread import VideoThread
from core.rtmpose_processor import RTMPoseProcessor
from core.sound_manager import SoundManager
from core.workout_tracker import WorkoutTracker
from core.translations import Translations as T
from core.angle_safety_detector import AngleSafetyDetector
from exercise_counters import ExerciseCounter
from ui.video_display import VideoDisplay
from ui.control_panel import ControlPanel
from ui.coach_panel import SafetyPanel
from ui.user_profile_panel import UserProfilePanel
from ui.styles import AppStyles

from .app_state import AppState
from .frame_pipeline import FramePipeline
from .app_controller import AppController
from .mode_manager import ModeManager
from .menu_manager import MenuManager
from .stats_manager import StatsManager
from .video_processor import VideoProcessor
from .counter_manager import CounterManager
from .training_session import TrainingSession
from ui.training_report_dialog import TrainingReportDialog


class WorkoutTrackerApp(QMainWindow):
    """AI Fitness Assistant Main Window Class"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(T.get("app_title"))
        self.setMinimumSize(1280, 720)

        # 1. 创建集中状态仓库
        self.app_state = AppState()

        # 2. 初始化核心组件（写入 app_state.device / model_mode / exercise_type）
        self._init_core_components()

        # 3. 创建各 Manager（ModeManager/MenuManager 需要 main_window 用于布局操作）
        self.mode_manager = ModeManager(self, self.app_state)
        self.menu_manager = MenuManager(self, self.app_state)
        self.stats_manager = StatsManager(self.app_state, self.workout_tracker)
        self.counter_manager = CounterManager(
            self.app_state, self.exercise_counter,
            self.safety_detector, self.workout_tracker
        )

        # 4. 构建 UI 布局（创建 video_display / safety_panel / control_panel）
        #    注意：此处暂不连接信号，AppController 尚未创建
        self.setup_ui()

        # 5. 创建统计面板（stats_panel），AppController 需要它
        self.stats_manager.init_workout_stats()
        # main_window 持有 stats_panel 引用，供 mode_manager 布局操作使用
        self.stats_panel = self.stats_manager.stats_panel

        # 6. 创建视频线程
        self.setup_video_thread()

        # 7. 创建帧处理流水线
        self.frame_pipeline = FramePipeline(
            self.app_state, self.pose_processor, self.exercise_counter,
            self.safety_detector, self.sound_manager
        )

        # 8. 创建视频处理器（需要 video_thread）
        self.video_processor = VideoProcessor(
            self.app_state, self.video_thread, self.pose_processor,
            self.video_display, self.counter_manager
        )

        # 8.5 创建训练会话管理器
        self.training_session = TrainingSession(self.app_state, self.safety_detector)

        # 9. 创建 AppController（连接 FramePipeline 信号到 UI）
        self.app_controller = AppController(
            self.app_state, self.counter_manager, self.stats_manager,
            self.mode_manager, self.menu_manager, self.video_processor,
            self.frame_pipeline, self.video_display, self.control_panel,
            self.safety_panel, self.stats_panel, self.sound_manager,
            self.workout_tracker, main_window=self, training_session=self.training_session
        )

        # 10. 连接 UI 信号到 AppController
        self.connect_signals()

        # 11. 初始化面板状态（GPU 开关等）
        self._init_panels()

        # 12. 启动视频
        self.start_video()

        # 13. 欢迎消息（模型延迟加载，首帧时通过 FramePipeline 提示就绪）
        self.statusBar.showMessage(T.get("welcome_loading"))

    # =====================================================================
    # 设备检测与核心组件初始化
    # =====================================================================
    @staticmethod
    def _register_nvidia_dll_dirs():
        """Add pip-installed NVIDIA package DLL directories to PATH so onnxruntime can find CUDA libs"""
        try:
            import nvidia
            nvidia_root = os.path.dirname(nvidia.__file__)
            paths_to_add = []
            for pkg in os.listdir(nvidia_root):
                bin_dir = os.path.join(nvidia_root, pkg, 'bin')
                if os.path.isdir(bin_dir):
                    paths_to_add.append(bin_dir)
            if paths_to_add:
                os.environ['PATH'] = ';'.join(paths_to_add) + ';' + os.environ.get('PATH', '')
                print(f"Added {len(paths_to_add)} NVIDIA DLL directories to PATH")
        except ImportError:
            pass  # No pip-installed nvidia packages
        except Exception as e:
            print(f"Warning: Failed to register NVIDIA DLL dirs: {e}")

    def _detect_device(self):
        """Detect available inference device by testing CUDA session creation"""
        self._register_nvidia_dll_dirs()
        try:
            import onnxruntime as ort
            if 'CUDAExecutionProvider' not in ort.get_available_providers():
                print("CUDAExecutionProvider not listed, using CPU")
                return 'cpu'
            from core.services import PathManager
            det_model = PathManager.get_model_path('yolox_nano_8xb8-300e_humanart-40f6f0d0.onnx')
            if not os.path.exists(det_model):
                print("No local model for CUDA test, using CPU")
                return 'cpu'
            sess_options = ort.SessionOptions()
            sess_options.log_severity_level = 4  # FATAL only
            devnull_fd = os.open(os.devnull, os.O_WRONLY)
            old_stderr_fd = os.dup(2)
            os.dup2(devnull_fd, 2)
            try:
                sess = ort.InferenceSession(
                    det_model, sess_options,
                    providers=['CUDAExecutionProvider']
                )
                active_providers = sess.get_providers()
                del sess
            finally:
                os.dup2(old_stderr_fd, 2)
                os.close(old_stderr_fd)
                os.close(devnull_fd)
            if 'CUDAExecutionProvider' in active_providers:
                print("CUDA GPU verified, using GPU inference")
                return 'cuda'
            else:
                print("CUDA runtime not available, using CPU")
                return 'cpu'
        except Exception as e:
            print(f"CUDA detection failed: {e}")
        print("Using CPU inference")
        return 'cpu'

    def _init_core_components(self):
        """初始化核心组件：设备、姿态处理器、计数器、安全检测、声音、追踪器"""
        # 设备设置 - 自动检测GPU
        self.app_state.device = self._detect_device()
        self.app_state.model_mode = 'lightweight'  # 默认轻量模型

        # 创建运动计数器
        self.exercise_counter = ExerciseCounter()

        # 初始化RTMPose姿态处理器（延迟加载模型，启动更快）
        print(f"Initializing RTMPose processor (mode: {self.app_state.model_mode}, device: {self.app_state.device})")
        self.pose_processor = RTMPoseProcessor(
            exercise_counter=self.exercise_counter,
            mode=self.app_state.model_mode,
            backend='onnxruntime',
            device=self.app_state.device
        )

        # 默认运动类型
        self.app_state.exercise_type = "squat"

        # 声音管理器
        self.sound_manager = SoundManager()

        # 运动追踪器
        self.workout_tracker = WorkoutTracker()

        # 安全检测模块
        self.safety_detector = AngleSafetyDetector()
        self.safety_detector.set_exercise(self.app_state.exercise_type)

    # =====================================================================
    # UI 布局
    # =====================================================================
    def setup_ui(self):
        """设置用户界面布局"""
        self.setPalette(AppStyles.get_window_palette())
        self.setStyleSheet(
            AppStyles.get_global_stylesheet() +
            AppStyles.get_scrollbar_style() +
            AppStyles.get_tab_widget_style()
        )

        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #F5F5F7;")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部导航栏
        self._setup_nav_bar(main_layout)

        # 主内容区域
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        # 左侧区域（视频显示）- 占70%
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.video_display = VideoDisplay()
        left_layout.addWidget(self.video_display)

        # 右侧区域（安全面板 + 控制面板）- 占30%，支持滚动
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)
        right_widget = QWidget()
        right_widget.setMaximumWidth(420)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        self.safety_panel = SafetyPanel()
        right_layout.addWidget(self.safety_panel)

        self.control_panel = ControlPanel()
        right_layout.addWidget(self.control_panel)

        self.user_profile_panel = UserProfilePanel()
        right_layout.addWidget(self.user_profile_panel)

        right_layout.addStretch()

        right_scroll.setWidget(right_widget)

        content_layout.addWidget(left_widget, 7)
        content_layout.addWidget(right_scroll, 3)

        main_layout.addLayout(content_layout)

        # 状态栏
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet(AppStyles.get_statusbar_style())
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(T.get("ready"))

        # 菜单栏
        self.menu_manager.setup_menu_bar()

    def _setup_nav_bar(self, parent_layout):
        """设置顶部导航栏"""
        nav_bar = QWidget()
        nav_bar.setFixedHeight(48)
        nav_bar.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E5EA;
            }
        """)
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(16, 0, 16, 0)
        nav_layout.setSpacing(12)

        nav_title = QLabel(T.get("app_title"))
        nav_title.setStyleSheet("""
            QLabel {
                font-size: 17px;
                font-weight: 700;
                color: #1D1D1F;
            }
        """)
        nav_layout.addWidget(nav_title)

        nav_layout.addStretch()

        nav_status = QLabel(T.get("ready"))
        nav_status.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #86868B;
            }
        """)
        nav_layout.addWidget(nav_status)

        parent_layout.addWidget(nav_bar)

    def connect_signals(self):
        """连接 UI 信号到 AppController（不再连接到 main_window 中转方法）"""
        ctrl = self.app_controller

        # 视频线程帧信号 → AppController（关键：必须在 app_controller 创建后连接）
        self.video_thread.change_pixmap_signal.connect(ctrl.on_frame_received)

        # 控制面板信号 → AppController
        self.control_panel.exercise_changed.connect(ctrl.on_exercise_changed)
        self.control_panel.counter_reset.connect(ctrl.on_counter_reset)
        self.control_panel.camera_changed.connect(ctrl.on_camera_changed)
        self.control_panel.rotation_toggled.connect(ctrl.on_rotation_toggled)
        self.control_panel.skeleton_toggled.connect(ctrl.on_skeleton_toggled)
        self.control_panel.model_changed.connect(ctrl.on_model_changed)
        self.control_panel.mirror_toggled.connect(ctrl.on_mirror_toggled)
        self.control_panel.device_changed.connect(ctrl.on_device_changed)
        self.control_panel.counter_increase.connect(ctrl.on_counter_increase)
        self.control_panel.counter_decrease.connect(ctrl.on_counter_decrease)
        self.control_panel.record_confirmed.connect(ctrl.on_record_confirmed)

        # 训练会话信号 → AppController
        self.control_panel.training_started.connect(ctrl.on_training_started)
        self.control_panel.training_ended.connect(ctrl.on_training_ended)
        self.control_panel.training_paused.connect(ctrl.on_training_paused)
        self.control_panel.training_resumed.connect(ctrl.on_training_resumed)

        # 统计面板信号 → AppController
        if hasattr(self, 'stats_panel'):
            self.stats_panel.goal_updated.connect(ctrl.on_goal_updated)
            self.stats_panel.weekly_goal_updated.connect(ctrl.on_weekly_goal_updated)
            self.stats_panel.month_changed.connect(ctrl.on_month_changed)

        # 语音开关 → 同步到 AppState + SoundManager
        self.safety_panel.voice_toggled.connect(self._on_voice_toggle_changed)

        # 用户档案保存后，将档案信息传递给安全检测器（用于个性化安全阈值）
        self.user_profile_panel.profile_saved.connect(self._on_profile_saved)

        # 菜单动作 → AppController（MenuManager 创建动作，此处连接信号）
        self.menu_manager.set_app_controller(ctrl)
        self.menu_manager.connect_actions()

        # AppController 的状态栏消息信号 → 状态栏
        ctrl.status_message.connect(self.statusBar.showMessage)

        # 训练报告信号 → 显示报告弹窗
        ctrl.show_report.connect(self._show_training_report)

    def _init_panels(self):
        """初始化面板状态（GPU 开关等）"""
        gpu_available = self.app_state.device == 'cuda'
        self.control_panel.set_gpu_available(gpu_available)
        self.stats_panel.setVisible(False)

    # =====================================================================
    # 视频线程生命周期
    # =====================================================================
    def setup_video_thread(self):
        """设置视频处理线程（关键：写入目标改为 AppState）"""
        from core.services import AppConfig
        self.video_thread = VideoThread(
            camera_id=0,
            rotate=True,
            display_width=AppConfig.DEFAULT_DISPLAY_WIDTH,
            display_height=AppConfig.DEFAULT_DISPLAY_HEIGHT,
            inference_width=AppConfig.DEFAULT_INFERENCE_WIDTH,
            inference_height=AppConfig.DEFAULT_INFERENCE_HEIGHT
        )

        # 关键修改：写入目标从 main_window 改为 app_state
        self.video_thread.app_state = self.app_state

        # 帧信号连接到 AppController（不再经过 main_window.update_image）
        if hasattr(self, 'app_controller'):
            self.video_thread.change_pixmap_signal.connect(self.app_controller.on_frame_received)
        self.video_thread.camera_error_signal.connect(self._on_camera_error)

        # 初始化 FPS 和推理帧（写入 AppState）
        self.app_state.current_fps = 0
        self.app_state.current_inference_frame = None

        # video_processor 持有 video_thread 引用，重建后需同步
        if hasattr(self, 'video_processor'):
            self.video_processor.video_thread = self.video_thread

    def start_video(self):
        """开始视频处理"""
        self.video_thread.start()

    def _on_camera_error(self, msg):
        """摄像头错误回调"""
        QMessageBox.warning(self, T.get("camera_error"), msg)

    def _on_voice_toggle_changed(self, checked):
        """语音开关回调：同步 AppState 和 SoundManager"""
        self.app_state.is_voice_enabled = checked
        self.sound_manager.set_voice_enabled(checked)

    def _on_profile_saved(self, profile_data):
        """用户档案保存后的回调 - 将档案信息同步到安全检测器和训练会话"""
        if hasattr(self, 'app_state'):
            self.app_state.user_profile = profile_data
        if hasattr(self, 'safety_detector'):
            self.safety_detector.apply_user_profile(profile_data)
        if hasattr(self, 'training_session'):
            self.training_session.apply_user_profile(profile_data)
        self.statusBar.showMessage(T.get("profile_saved"))

    def _show_training_report(self, report_data):
        """显示训练报告弹窗"""
        dialog = TrainingReportDialog(report_data, parent=self)
        dialog.saved.connect(self.app_controller.on_report_saved)
        dialog.discarded.connect(self.app_controller.on_report_discarded)
        dialog.exec_()

    # =====================================================================
    # 生命周期收尾
    # =====================================================================
    def closeEvent(self, event):
        """Clean up resources on close"""
        try:
            if hasattr(self, 'app_controller'):
                self.app_controller.shutdown()
        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            # 兜底：确保视频线程停止
            if hasattr(self, 'video_thread') and self.video_thread.isRunning():
                self.video_thread.stop()
            event.accept()
