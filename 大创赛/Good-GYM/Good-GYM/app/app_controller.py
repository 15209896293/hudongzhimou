"""
AppController - UI信号与业务逻辑之间的唯一桥梁
接收所有UI信号，调用Manager执行业务逻辑，通过信号通知UI更新
"""

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from core.translations import Translations as T


class AppController(QObject):
    """
    AppController 是 UI 信号和业务逻辑之间的唯一中转站。

    职责：
    1. 接收所有 UI 信号（来自 ControlPanel、MenuBar 等）
    2. 调用 Manager 执行业务逻辑
    3. 接收 Manager 的结果，发射信号通知 UI 更新

    设计原则：
    - AppController 不持有业务状态（状态在 AppState 中）
    - AppController 不直接操作 UI 组件（通过信号通知）
    - AppController 是 UI 信号 → Manager 方法 的唯一映射层
    """

    # ===== 信号：通知 main_window/UI 更新 =====
    status_message = pyqtSignal(str)              # 状态栏消息
    counter_updated = pyqtSignal(int)             # 计数器数值
    phase_updated = pyqtSignal(str)               # 阶段变化
    milestone_reached = pyqtSignal(int)           # 里程碑
    safety_updated = pyqtSignal(dict)             # 安全状态
    safety_stats_updated = pyqtSignal(dict)       # 安全统计
    voice_tip = pyqtSignal(str)                   # 语音提示
    model_ready = pyqtSignal(str)                 # 模型就绪
    exercise_name_updated = pyqtSignal(str)       # 运动名称更新
    gpu_availability = pyqtSignal(bool)           # GPU可用性
    mode_switched = pyqtSignal(str)               # 模式切换
    timer_updated = pyqtSignal(str)               # 计时器更新
    risk_score_updated = pyqtSignal(int)          # 风险评分更新
    training_state_changed = pyqtSignal(str)      # 训练状态变化
    show_report = pyqtSignal(dict)                # 显示训练报告

    def __init__(self, app_state, counter_manager, stats_manager,
                 mode_manager, menu_manager, video_processor, frame_pipeline,
                 video_display, control_panel, safety_panel, stats_panel,
                 sound_manager, workout_tracker, menu_bar=None, main_window=None,
                 training_session=None):
        super().__init__()

        self.state = app_state
        self.counter_manager = counter_manager
        self.stats_manager = stats_manager
        self.mode_manager = mode_manager
        self.menu_manager = menu_manager
        self.video_processor = video_processor
        self.frame_pipeline = frame_pipeline
        self.main_window = main_window  # 用于 video_thread 重建等生命周期回调

        # UI 组件引用（仅用于读取/触发更新，不直接修改状态）
        self.video_display = video_display
        self.control_panel = control_panel
        self.safety_panel = safety_panel
        self.stats_panel = stats_panel
        self.sound_manager = sound_manager
        self.workout_tracker = workout_tracker
        self.menu_bar = menu_bar
        self.training_session = training_session

        # 连接 FramePipeline 信号 → UI 更新
        self._connect_pipeline_signals()
        # 连接 VideoProcessor 信号 → 状态栏 + 生命周期回调
        self._connect_video_processor_signals()
        # 连接 CounterManager / StatsManager 信号 → UI 更新
        self._connect_manager_signals()
        # 连接训练会话信号
        self._connect_session_signals()

    # =====================================================================
    # 连接 FramePipeline 信号到 UI 更新
    # =====================================================================
    def _connect_pipeline_signals(self):
        """将 FramePipeline 的结果信号转发到 UI 组件"""
        pipeline = self.frame_pipeline

        # 渲染后的帧 → VideoDisplay
        pipeline.frame_rendered.connect(self.video_display.update_image)

        # 计数变化 → ControlPanel
        pipeline.counter_updated.connect(self.control_panel.update_counter)
        pipeline.phase_updated.connect(self.control_panel.update_phase)
        pipeline.milestone_reached.connect(self._on_milestone)

        # 安全检测 → SafetyPanel + 语音
        pipeline.safety_updated.connect(self.safety_panel.update_safety_status)
        pipeline.safety_stats_updated.connect(self.safety_panel.update_stats)
        pipeline.voice_tip.connect(self.sound_manager.speak)

        # 安全检测 → 训练会话记录
        pipeline.safety_updated.connect(self._on_safety_update_for_session)

        # 计数变化 → 训练会话记录
        pipeline.counter_updated.connect(self._on_counter_for_session)

        # 模型就绪 → 状态栏
        pipeline.model_ready.connect(self._on_model_ready)

        # 疲劳提醒 → 状态栏
        pipeline.fatigue_warning.connect(self.status_message.emit)

        # 状态栏消息转发
        pipeline.status_message.connect(self.status_message.emit)

    # =====================================================================
    # 连接 VideoProcessor 信号
    # =====================================================================
    def _connect_video_processor_signals(self):
        """将 VideoProcessor 的状态消息和生命周期请求转发到 UI/main_window"""
        vp = self.video_processor
        if hasattr(vp, 'status_message'):
            vp.status_message.connect(self.status_message.emit)
        if hasattr(vp, 'video_thread_recreate_requested'):
            vp.video_thread_recreate_requested.connect(self._recreate_video_thread)

    def _recreate_video_thread(self):
        """重新创建 video_thread（由 video_processor 在设备/模型切换时请求）"""
        if self.main_window is None:
            return
        # 重建 video_thread（main_window.setup_video_thread 内部会同步 video_processor.video_thread）
        self.main_window.setup_video_thread()
        QTimer.singleShot(500, self.main_window.start_video)

    # =====================================================================
    # 连接 CounterManager / StatsManager 信号
    # =====================================================================
    def _connect_manager_signals(self):
        """连接各 Manager 的信号到 UI 组件"""
        # CounterManager 信号
        cm = self.counter_manager
        if hasattr(cm, 'status_message'):
            cm.status_message.connect(self.status_message.emit)
        if hasattr(cm, 'counter_updated'):
            cm.counter_updated.connect(self.control_panel.update_counter)
        if hasattr(cm, 'stats_refresh_requested'):
            cm.stats_refresh_requested.connect(self._refresh_stats)

        # StatsManager 信号
        sm = self.stats_manager
        if hasattr(sm, 'status_message'):
            sm.status_message.connect(self.status_message.emit)

    def _connect_session_signals(self):
        """连接训练会话信号"""
        if self.training_session is None:
            return

        ts = self.training_session

        ts.timer_updated.connect(self.control_panel.update_timer)
        ts.risk_score_updated.connect(self.control_panel.update_risk_score)
        ts.session_ended.connect(self._on_session_ended)

    # =====================================================================
    # 训练会话处理
    # =====================================================================
    def on_training_started(self):
        """开始训练"""
        if self.training_session is None:
            return
        self.training_session.start()
        self.state.session_state = 'training'
        self.control_panel.set_training_state('training')
        self.training_state_changed.emit('training')
        self.status_message.emit("训练已开始")

    def on_training_ended(self):
        """结束训练"""
        if self.training_session is None:
            return
        report = self.training_session.end()
        self.state.session_state = 'ended'
        self.control_panel.set_training_ended()
        self.training_state_changed.emit('ended')
        if report:
            self.show_report.emit(report)

    def on_training_paused(self):
        """暂停训练"""
        if self.training_session is None:
            return
        self.training_session.pause()
        self.state.session_state = 'paused'
        self.control_panel.set_training_state('paused')
        self.training_state_changed.emit('paused')
        self.status_message.emit("训练已暂停")

    def on_training_resumed(self):
        """继续训练"""
        if self.training_session is None:
            return
        self.training_session.resume()
        self.state.session_state = 'training'
        self.control_panel.set_training_state('training')
        self.training_state_changed.emit('training')
        self.status_message.emit("训练继续")

    def _on_safety_update_for_session(self, safety_result):
        """安全检测结果 → 训练会话记录"""
        if self.training_session is None:
            return
        self.training_session.record_safety_event(safety_result)

        fatigue_msg = self.training_session.check_fatigue()
        if fatigue_msg:
            self.status_message.emit(fatigue_msg)

    def _on_session_ended(self, report):
        """训练会话结束，生成报告"""
        self.state.session_duration = report.get('duration_sec', 0)
        self.state.session_rep_count = report.get('rep_count', 0)
        self.state.session_risk_score = report.get('risk_score', 100)

    def on_report_saved(self, report_data):
        """用户在报告弹窗中点击"保存记录" """
        exercise_type = report_data.get('exercise_type', self.state.exercise_type)
        count = report_data.get('rep_count', 0)
        if count > 0:
            self.counter_manager.state.current_count = count
            self.counter_manager.confirm_record(exercise_type)

        if self.training_session:
            self.training_session.reset()
        self.state.session_state = 'idle'
        self.control_panel.set_training_state('idle')
        self.training_state_changed.emit('idle')
        self.status_message.emit("训练记录已保存")

    def on_report_discarded(self):
        """用户在报告弹窗中点击"不保存" """
        if self.training_session:
            self.training_session.reset()
        self.state.session_state = 'idle'
        self.control_panel.set_training_state('idle')
        self.training_state_changed.emit('idle')
        self.status_message.emit("训练记录已丢弃")

    def _on_counter_for_session(self, count):
        """计数变化 → 通知训练会话"""
        if self.training_session and self.training_session.session_state == 'training':
            if count > self.state.current_count:
                self.training_session.record_rep()
        self.state.current_count = count

    def _refresh_stats(self):
        """刷新统计面板（记录确认后调用）"""
        try:
            self.stats_manager.update_today_stats()
            self.stats_manager.update_stats_overview()
        except Exception as e:
            print(f"Error refreshing stats: {e}")

    # =====================================================================
    # UI 信号处理：运动类型
    # =====================================================================
    def on_exercise_changed(self, exercise_type):
        """运动类型切换"""
        self.counter_manager.change_exercise(exercise_type)
        self.exercise_name_updated.emit(T.get_exercise_display_name(exercise_type))

    # =====================================================================
    # UI 信号处理：计数器
    # =====================================================================
    def on_counter_reset(self):
        """重置计数器"""
        self.counter_manager.reset_counter()

    def on_counter_increase(self, new_count):
        """手动增加计数"""
        self.counter_manager.increase_counter(new_count)

    def on_counter_decrease(self, new_count):
        """手动减少计数"""
        self.counter_manager.decrease_counter(new_count)

    def on_record_confirmed(self, exercise_type):
        """确认记录"""
        self.counter_manager.confirm_record(exercise_type)

    # =====================================================================
    # UI 信号处理：摄像头/视频
    # =====================================================================
    def on_camera_changed(self, camera_id):
        """切换摄像头"""
        self.video_processor.change_camera(camera_id)

    def on_rotation_toggled(self, rotate):
        """切换视频旋转"""
        self.video_processor.toggle_rotation(rotate)

    def on_skeleton_toggled(self, show):
        """切换骨架显示"""
        self.state.show_skeleton = show
        # 通过 frame_pipeline 访问 pose_processor（AppController 不直接持有 pose_processor）
        self.frame_pipeline.pose_processor.show_skeleton = show

    def on_mirror_toggled(self, mirror):
        """切换镜像模式（关键：同时更新VideoThread和AppState）"""
        # video_processor.toggle_mirror 内部会同时更新 AppState 和 VideoThread
        self.video_processor.toggle_mirror(mirror)

    # =====================================================================
    # UI 信号处理：模型/设备
    # =====================================================================
    def on_model_changed(self, model_mode):
        """切换RTMPose模型模式"""
        self.video_processor.change_model(model_mode)

    def on_device_changed(self, device):
        """切换推理设备（CPU/GPU）"""
        self.video_processor.change_device(device)

    # =====================================================================
    # UI 信号处理：模式切换
    # =====================================================================
    def on_switch_to_workout_mode(self):
        """切换到运动模式"""
        self.mode_manager.switch_to_workout_mode()
        self.mode_switched.emit('workout')

    def on_switch_to_stats_mode(self):
        """切换到统计模式"""
        self.mode_manager.switch_to_stats_mode()
        # 模式切换后刷新统计数据（原 mode_manager 中的 update_today/update_stats_overview 调用）
        try:
            self.stats_manager.update_today_stats()
            self.stats_manager.update_stats_overview()
        except Exception as e:
            print(f"Error refreshing stats after mode switch: {e}")
        self.mode_switched.emit('stats')

    # =====================================================================
    # UI 信号处理：菜单
    # =====================================================================
    def on_open_video_file(self):
        """打开视频文件"""
        self.video_processor.open_video_file()

    def on_switch_to_camera_mode(self):
        """切换回摄像头模式"""
        self.video_processor.switch_to_camera_mode()

    def on_show_about(self):
        """显示关于对话框"""
        self.menu_manager.show_about()

    def on_change_language(self, language):
        """切换语言"""
        self.menu_manager.change_language(language)

    # =====================================================================
    # UI 信号处理：统计面板
    # =====================================================================
    def on_goal_updated(self, exercise_type, count):
        """更新运动目标"""
        self.stats_manager.update_goal(exercise_type, count)

    def on_weekly_goal_updated(self, count):
        """更新周目标"""
        self.stats_manager.update_weekly_goal(count)

    def on_month_changed(self, year, month):
        """加载指定月份统计"""
        self.stats_manager.load_month_stats(year, month)

    # =====================================================================
    # 帧处理入口
    # =====================================================================
    def on_frame_received(self, frame, fps):
        """
        接收 VideoThread 传来的帧，交给 FramePipeline 处理。
        这是视频数据流的唯一入口。
        """
        rendered_frame = self.frame_pipeline.process_frame(frame, fps)
        # 渲染后的帧已通过 FramePipeline.frame_rendered 信号发给 VideoDisplay

    # =====================================================================
    # 内部辅助方法
    # =====================================================================
    def _on_milestone(self, count):
        """达到里程碑时的处理"""
        # ControlPanel 没有专门的 update_milestone 方法，触发成功动画即可
        if hasattr(self.control_panel, 'update_milestone'):
            self.control_panel.update_milestone(count)
        else:
            self.control_panel.show_success_animation()
        # 里程碑状态栏提示
        ex_name = T.get_exercise_display_name(self.state.exercise_type)
        self.status_message.emit(T.get("milestone_congrats").format(count=count, exercise=ex_name))

    def _on_model_ready(self, message):
        """模型加载完成时的处理"""
        self.status_message.emit(T.get("model_ready_msg").format(msg=message, mode=self.state.model_mode, device=self.state.device))

    # =====================================================================
    # 生命周期
    # =====================================================================
    def shutdown(self):
        """应用关闭时的清理"""
        # 停止视频线程
        if hasattr(self.video_processor, 'video_thread') and self.video_processor.video_thread:
            if self.video_processor.video_thread.isRunning():
                self.video_processor.video_thread.stop()
