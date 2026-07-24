"""
FramePipeline - 帧处理流水线
将 main_window.update_image() 和 video_processor.update_image() 合并为4阶段流水线：
  Stage1: Inference（推理跳帧）
  Stage2: Counter（动作计数）
  Stage3: Safety（安全检测，节流控制）
  Stage4: Render（骨架绘制、镜像、角度线、BGR→RGB）

关键约束：安全检测节流计数器必须在 Pipeline 顶层管理，每帧都递增，不受推理跳帧影响。
"""

import cv2
import numpy as np
import time
from PyQt5.QtCore import QObject, pyqtSignal
from core.services.config import AppConfig
from core.services.angle_utils import AngleUtils
from core.angle_safety_detector import SafetyLevel


class FramePipeline(QObject):
    """帧处理流水线，串联推理→计数→安全检测→渲染4个阶段"""

    # ===== 信号：通知UI更新 =====
    frame_rendered = pyqtSignal(np.ndarray)       # 渲染后的帧（供VideoDisplay显示）
    counter_updated = pyqtSignal(int)             # 计数器数值变化
    phase_updated = pyqtSignal(str)               # 阶段变化（UP/DOWN）
    milestone_reached = pyqtSignal(int)           # 达到里程碑
    safety_updated = pyqtSignal(dict)             # 安全检测结果
    safety_stats_updated = pyqtSignal(dict)       # 安全统计
    voice_tip = pyqtSignal(str)                   # 语音提示
    model_ready = pyqtSignal(str)                 # 模型加载完成
    status_message = pyqtSignal(str)              # 状态栏消息
    fatigue_warning = pyqtSignal(str)             # 疲劳/负荷提醒

    # 骨架连接关系（COCO格式）
    SKELETON_CONNECTIONS = [
        (0, 1), (0, 2), (1, 3), (2, 4),  # 头部
        (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # 上肢
        (5, 11), (6, 12), (11, 12),  # 躯干
        (11, 13), (13, 15), (12, 14), (14, 16),  # 下肢
    ]

    def __init__(self, app_state, pose_processor, exercise_counter, safety_detector, sound_manager):
        super().__init__()
        self.state = app_state
        self.pose_processor = pose_processor
        self.exercise_counter = exercise_counter
        self.safety_detector = safety_detector
        self.sound_manager = sound_manager

        # 推理跳帧计数器（从1开始，确保首帧必推理以触发模型延迟加载）
        self._inference_frame_counter = 1

        # 安全检测节流计数器（必须在顶层管理，每帧都递增，不受跳帧影响）
        self._safety_frame_counter = 0

        # 帧忙锁（防止上一帧未处理完时堆积）
        self._frame_busy = False

        # 上次计数（用于检测计数变化，触发音效和UI更新）
        self._last_count = -1
        self._last_stage = None
        self._last_milestone = -1

        # 置信度阈值
        self.conf_threshold = AppConfig.DEFAULT_CONF_THRESHOLD

        # 累计负荷追踪
        self._consecutive_frames = 0
        self._last_fatigue_warning = 0
        self._fatigue_check_interval = 60  # 每60帧检查一次

    def process_frame(self, frame, fps=0):
        """
        主入口：处理单帧视频

        Args:
            frame: VideoThread传入的显示帧（高清）
            fps: 当前帧率

        Returns:
            np.ndarray: 渲染后的帧（RGB格式），可直接交给VideoDisplay显示
        """
        if self._frame_busy:
            return None

        self._frame_busy = True
        self.state.current_fps = fps

        try:
            is_training = getattr(self.state, 'session_state', 'training') == 'training'

            # ===== Stage 1: Inference（推理）=====
            keypoints = self._stage_inference(frame)

            # ===== Stage 2: Counter（计数）=====
            if is_training:
                self._stage_counter(keypoints)

            # ===== Stage 3: Safety（安全检测）=====
            # 关键：计数器在顶层每帧递增，不受Stage1跳帧影响
            self._safety_frame_counter += 1
            if is_training and self._safety_frame_counter % AppConfig.SAFETY_SKIP_INTERVAL == 0:
                self._stage_safety(keypoints)

            # ===== Stage 3.5: 累计负荷检查 =====
            if is_training:
                self._check_fatigue_load()

            # ===== Stage 4: Render（渲染）=====
            rendered_frame = self._stage_render(frame, keypoints)

            # 模型就绪状态检查（首次推理完成后触发）
            self._check_model_ready()

            return rendered_frame

        finally:
            self._frame_busy = False

    # =========================================================================
    # Stage 1: Inference - 推理跳帧控制
    # =========================================================================
    def _stage_inference(self, display_frame):
        """
        执行姿态推理（含跳帧优化）。
        跳帧时复用上一次的关键点，保证后续阶段始终有数据可用。
        """
        self._inference_frame_counter += 1

        # 获取推理帧（VideoThread已预先缩放到低分辨率并存入AppState）
        inference_frame = self.state.current_inference_frame
        if inference_frame is None:
            inference_frame = display_frame

        keypoints = None
        angle = None
        angle_point = None

        # 跳帧逻辑：每 INFERENCE_SKIP_INTERVAL 帧执行一次推理
        if self._inference_frame_counter % AppConfig.INFERENCE_SKIP_INTERVAL == 0:
            try:
                results = self.pose_processor.process_frame(
                    inference_frame, self.state.exercise_type
                )
                if results:
                    # process_frame 返回 (processed_frame, current_angle, angle_point, keypoints)
                    # 计数已在 process_frame → get_exercise_angle 中完成，此处仅提取结果
                    _, current_angle, angle_point, keypoints = results
                    self.state.current_keypoints = keypoints
                    self.state.current_angle = current_angle
                    self.state.current_angle_point = angle_point
            except Exception as e:
                # 推理失败时保持上一次结果（安全降级）
                keypoints = self.state.current_keypoints
                angle = self.state.current_angle
                angle_point = self.state.current_angle_point
        else:
            # 跳帧：复用上一次推理结果
            keypoints = self.state.current_keypoints
            angle = self.state.current_angle
            angle_point = self.state.current_angle_point

        return keypoints

    # =========================================================================
    # Stage 2: Counter - 动作计数
    # =========================================================================
    def _stage_counter(self, keypoints):
        """
        检测计数器变化并发射信号（触发UI更新和音效）。

        注意：实际计数动作已在 Stage1 的 pose_processor.process_frame() 中完成，
        此处仅负责检测计数/阶段变化并通知 UI。
        """
        # 检测计数变化
        current_count = self.exercise_counter.counter
        if current_count != self._last_count:
            self._last_count = current_count
            self.state.current_count = current_count

            # 发射信号通知UI更新计数器
            self.counter_updated.emit(current_count)

            # 播放计数音效
            self.sound_manager.play_count_sound()

            # 检测里程碑
            if current_count > 0 and current_count % AppConfig.MILESTONE_INTERVAL == 0:
                if current_count != self._last_milestone:
                    self._last_milestone = current_count
                    self.milestone_reached.emit(current_count)
                    self.sound_manager.play_milestone_sound(current_count)

        # 检测阶段变化
        current_stage = self.exercise_counter.stage
        if current_stage != self._last_stage:
            self._last_stage = current_stage
            if current_stage:
                self.phase_updated.emit(current_stage)

    def _get_count_method(self):
        """获取当前运动类型对应的计数方法

        优先使用专用的 count_<exercise_type> 包装方法；
        若不存在（如 plank/lunge/kids_dance_*/posture_1/stretch_1），
        则回退到通用 count_exercise(keypoints, exercise_type)。
        """
        exercise_type = self.state.exercise_type
        dedicated_method_name = f"count_{exercise_type}"
        dedicated_method = getattr(self.exercise_counter, dedicated_method_name, None)
        if dedicated_method is not None:
            return dedicated_method
        # 回退：通用计数方法（需传入 exercise_type 参数）
        if hasattr(self.exercise_counter, 'count_exercise'):
            return lambda keypoints: self.exercise_counter.count_exercise(keypoints, exercise_type)
        return None

    # =========================================================================
    # Stage 3: Safety - 安全检测（节流控制）
    # =========================================================================
    def _stage_safety(self, keypoints):
        """
        执行关节角度安全检测。
        注意：本方法仅在顶层计数器满足节流条件时被调用，
        但计数器本身在 process_frame() 顶层每帧递增。
        """
        if keypoints is None or not np.any(keypoints):
            return

        current_time_ms = time.time() * 1000

        # 执行安全检测
        safety_result = self.safety_detector.check_safety(keypoints, current_time_ms)
        self.state.safety_result = safety_result

        # 发射信号更新安全面板
        self.safety_updated.emit(safety_result)
        self.safety_stats_updated.emit(self.safety_detector.get_safety_stats())

        # 语音播报（基于安全等级和开关状态）
        if not self.state.is_voice_enabled:
            return

        safety_level = safety_result.get('level')

        # WARNING级别：单次播报
        if safety_level == SafetyLevel.WARNING:
            voice_tips = safety_result.get('voice_tips', [])
            if voice_tips:
                for tip in voice_tips:
                    self.voice_tip.emit(tip)

        # DANGER级别：重复播报（间隔10秒）
        elif safety_level == SafetyLevel.DANGER:
            voice_tips = safety_result.get('voice_tips', [])
            if voice_tips:
                for tip in voice_tips:
                    self.voice_tip.emit(tip)

    def _check_fatigue_load(self):
        """累计负荷检查：检测连续运动时长和动作次数，发出休息提醒"""
        self._consecutive_frames += 1

        if self._consecutive_frames % self._fatigue_check_interval != 0:
            return

        current_time = time.time()

        session_state = getattr(self.state, 'session_state', 'idle')
        if session_state != 'training':
            return

        session_start = getattr(self.state, 'session_start_time', None)
        if session_start is None or session_start == 0:
            return

        duration_sec = int(current_time - session_start)

        current_count = self.state.current_count

        fatigue_triggers = []

        if duration_sec >= 300 and duration_sec < 600:
            fatigue_triggers.append("已运动5分钟，注意休息")
        elif duration_sec >= 600 and duration_sec < 900:
            fatigue_triggers.append("已运动10分钟，建议休息1-2分钟")
        elif duration_sec >= 900:
            fatigue_triggers.append("已运动15分钟，强烈建议休息")

        if current_count >= 50 and current_count < 100:
            fatigue_triggers.append(f"已完成{current_count}次动作，注意疲劳")
        elif current_count >= 100 and current_count < 200:
            fatigue_triggers.append(f"已完成{current_count}次动作，建议休息")
        elif current_count >= 200:
            fatigue_triggers.append(f"已完成{current_count}次动作，强烈建议休息")

        if fatigue_triggers:
            msg = fatigue_triggers[-1]
            if current_time - self._last_fatigue_warning > 30:
                self._last_fatigue_warning = current_time
                self.fatigue_warning.emit(msg)
                self.status_message.emit(msg)

    # =========================================================================
    # Stage 4: Render - 渲染（骨架、镜像、角度线、BGR→RGB）
    # =========================================================================
    def _stage_render(self, frame, keypoints):
        """
        将推理结果渲染到视频帧上。
        处理顺序：关键点坐标缩放 → 骨架绘制 → 镜像 → 角度线绘制 → 安全状态显示 → BGR→RGB
        """
        annotated_frame = frame.copy()

        # 0. 关键点坐标从推理帧空间映射到显示帧空间
        if keypoints is not None:
            keypoints = self._scale_keypoints(keypoints, frame)

        # 1. 骨架绘制（在镜像之前，使用缩放后的坐标）
        if keypoints is not None and self.pose_processor.show_skeleton:
            annotated_frame = self._draw_skeleton(annotated_frame, keypoints)

        # 2. 镜像处理（水平翻转）
        if self.state.mirror_mode:
            annotated_frame = cv2.flip(annotated_frame, 1)

        # 3. 角度线绘制（在镜像之后，需调整坐标）
        angle_point = self.state.current_angle_point
        current_angle = self.state.current_angle
        if angle_point is not None and len(angle_point) == 3:
            scaled_angle_point = self._scale_angle_point(angle_point, frame)
            annotated_frame = self._draw_angle_lines(
                annotated_frame, scaled_angle_point, current_angle
            )

        # 4. 安全状态显示（在镜像之后，视频右上角）
        annotated_frame = self._draw_safety_overlay(annotated_frame)

        # 5. BGR → RGB 转换（PyQt5 QImage 需要 RGB 格式）
        rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)

        # 发射渲染完成的帧
        self.frame_rendered.emit(rgb_frame)

        return rgb_frame

    # =========================================================================
    # 关键点坐标缩放
    # =========================================================================
    def _scale_keypoints(self, keypoints, display_frame):
        """
        将关键点坐标从推理帧空间缩放到显示帧空间。
        推理帧（如 640x360）与显示帧（如 1920x1080）尺寸不同，
        如果不缩放，骨架会偏移到画面左上角区域。
        """
        inference_frame = self.state.current_inference_frame
        if inference_frame is None:
            return keypoints

        inf_h, inf_w = inference_frame.shape[:2]
        disp_h, disp_w = display_frame.shape[:2]

        # 尺寸相同则无需缩放
        if inf_w == disp_w and inf_h == disp_h:
            return keypoints

        scale_x = disp_w / inf_w
        scale_y = disp_h / inf_h

        scaled = keypoints.copy()
        scaled[:, 0] = scaled[:, 0] * scale_x  # x 坐标缩放
        scaled[:, 1] = scaled[:, 1] * scale_y  # y 坐标缩放
        return scaled

    # =========================================================================
    # 骨架绘制
    # =========================================================================
    def _draw_skeleton(self, frame, keypoints):
        """
        在帧上绘制人体骨架连线。
        直接复用现有 video_processor.py 中的绘制逻辑。
        """
        annotated_frame = frame.copy()

        # 绘制骨架连线
        for pt1, pt2 in self.SKELETON_CONNECTIONS:
            if (pt1 < len(keypoints) and pt2 < len(keypoints)
                    and len(keypoints[pt1]) >= 3 and len(keypoints[pt2]) >= 3):
                x1, y1, c1 = int(keypoints[pt1][0]), int(keypoints[pt1][1]), keypoints[pt1][2]
                x2, y2, c2 = int(keypoints[pt2][0]), int(keypoints[pt2][1]), keypoints[pt2][2]
                conf = min(c1, c2)
                if conf > self.conf_threshold:
                    cv2.line(
                        annotated_frame,
                        (x1, y1), (x2, y2),
                        AppConfig.SKELETON_COLOR,
                        AppConfig.SKELETON_THICKNESS
                    )

        # 绘制关键点圆圈
        for i, kp in enumerate(keypoints):
            if len(kp) < 3:
                continue
            x, y, c = int(kp[0]), int(kp[1]), kp[2]
            if c > self.conf_threshold:
                cv2.circle(annotated_frame, (x, y), 5, (0, 0, 255), -1)

        return annotated_frame

    # =========================================================================
    # 角度点坐标缩放
    # =========================================================================
    def _scale_angle_point(self, angle_point, display_frame):
        """
        将角度点坐标从推理帧空间缩放到显示帧空间。
        angle_point 是包含 3 个关键点的元组/列表，每个元素是 (3,) 数组 [x, y, conf]。
        """
        inference_frame = self.state.current_inference_frame
        if inference_frame is None:
            return angle_point

        inf_h, inf_w = inference_frame.shape[:2]
        disp_h, disp_w = display_frame.shape[:2]

        if inf_w == disp_w and inf_h == disp_h:
            return angle_point

        scale_x = disp_w / inf_w
        scale_y = disp_h / inf_h

        import numpy as np
        scaled = []
        for kp in angle_point:
            if kp is not None and len(kp) >= 3:
                scaled_kp = np.array([kp[0] * scale_x, kp[1] * scale_y, kp[2]], dtype=kp.dtype)
                scaled.append(scaled_kp)
            else:
                scaled.append(kp)
        return scaled

    # =========================================================================
    # 角度线绘制
    # =========================================================================
    def _draw_angle_lines(self, frame, angle_point, angle_value):
        """
        在帧上绘制角度指示线和角度值。
        直接复用现有 video_processor.py 中的绘制逻辑。
        注意：在镜像之后调用，需根据 mirror_mode 调整坐标。
        """
        if angle_point is None or len(angle_point) != 3:
            return frame

        if angle_value is None:
            return frame

        # angle_point 每个元素是 (3,) 数组 [x, y, conf]，直接提取坐标
        valid_points = []
        for kp in (angle_point[0], angle_point[1], angle_point[2]):
            if kp is not None and len(kp) >= 3:
                x, y, c = int(kp[0]), int(kp[1]), float(kp[2])
                if c > self.conf_threshold:
                    valid_points.append((x, y))
                else:
                    valid_points.append(None)
            else:
                valid_points.append(None)

        if None in valid_points:
            return frame

        # 镜像后坐标调整（因为已经在镜像之后调用）
        if self.state.mirror_mode:
            display_width = frame.shape[1]
            for i in range(len(valid_points)):
                valid_points[i] = (
                    display_width - valid_points[i][0],
                    valid_points[i][1]
                )

        pt1, pt2, pt3 = valid_points

        # 绘制连接线段
        cv2.line(frame, pt1, pt2, AppConfig.ANGLE_LINE_COLOR, AppConfig.ANGLE_LINE_THICKNESS)
        cv2.line(frame, pt2, pt3, AppConfig.ANGLE_LINE_COLOR, AppConfig.ANGLE_LINE_THICKNESS)

        # 绘制顶点圆圈
        cv2.circle(frame, pt2, 8, (0, 0, 255), -1)
        cv2.circle(frame, pt2, 8, (255, 255, 255), 2)

        # 绘制圆弧
        angle_rad = AngleUtils.calculate_angle(pt1, pt2, pt3)
        if angle_rad is not None:
            v1 = np.array([pt1[0] - pt2[0], pt1[1] - pt2[1]])
            v2 = np.array([pt3[0] - pt2[0], pt3[1] - pt2[1]])
            n1 = np.linalg.norm(v1)
            n2 = np.linalg.norm(v2)

            if n1 > 0 and n2 > 0:
                ref1 = (int(pt2[0] + v1[0] / n1 * 30), int(pt2[1] + v1[1] / n1 * 30))
                ref2 = (int(pt2[0] + v2[0] / n2 * 30), int(pt2[1] + v2[1] / n2 * 30))
                cv2.ellipse(frame, pt2, (30, 30), 0, 0, angle_rad, AppConfig.ANGLE_LINE_COLOR, 2)

        # 绘制角度文字
        from core.translations import Translations as T
        angle_text = T.get("angle_display").format(angle=int(angle_value))
        text_size = cv2.getTextSize(
            angle_text, cv2.FONT_HERSHEY_SIMPLEX,
            AppConfig.ANGLE_TEXT_SCALE, AppConfig.ANGLE_TEXT_THICKNESS
        )[0]
        text_x = max(10, pt2[0] - text_size[0] // 2)
        text_y = max(text_size[1] + 5, pt2[1] - 15)
        cv2.putText(
            frame, angle_text, (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX, AppConfig.ANGLE_TEXT_SCALE,
            AppConfig.ANGLE_TEXT_COLOR, AppConfig.ANGLE_TEXT_THICKNESS
        )

        return frame

    # =========================================================================
    # 模型就绪检查
    # =========================================================================
    def _check_model_ready(self):
        """检查模型是否已完成首次加载，触发状态栏更新"""
        if not hasattr(self.pose_processor, 'model_initialized'):
            return

        # 模型加载成功
        if self.pose_processor.model_initialized and not self.state.model_initialized:
            self.state.model_initialized = True
            self.model_ready.emit("Model loaded successfully")
            return

        # 模型加载失败（仅提示一次）
        if (self.pose_processor.init_error_message
                and not self.state.model_initialized
                and not getattr(self, '_init_error_shown', False)):
            self._init_error_shown = True
            self.status_message.emit(f"⚠️ {self.pose_processor.init_error_message}")
            print(f"[FATAL] {self.pose_processor.init_error_message}")

    # =========================================================================
    # 安全状态覆盖层绘制
    # =========================================================================
    def _draw_safety_overlay(self, frame):
        """
        在视频帧右上角绘制安全状态覆盖层。
        包括：安全等级图标、当前安全评分、警告消息
        """
        safety_result = self.state.safety_result
        if safety_result is None:
            return frame

        h, w = frame.shape[:2]
        level = safety_result.get('level')
        messages = safety_result.get('messages', [])
        angles = safety_result.get('angles', {})

        overlay = frame.copy()

        safety_icon = "✅"
        bg_color = (0, 255, 0)
        text_color = (0, 0, 0)

        if level == SafetyLevel.WARNING:
            safety_icon = "⚠️"
            bg_color = (0, 255, 255)
            text_color = (0, 0, 0)
        elif level == SafetyLevel.DANGER:
            safety_icon = "🔴"
            bg_color = (0, 0, 255)
            text_color = (255, 255, 255)

        corner_size = 120
        cv2.rectangle(overlay, (w - corner_size - 10, 10),
                      (w - 10, corner_size + 10), bg_color, -1)

        alpha = 0.7
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        icon_text = safety_icon
        cv2.putText(frame, icon_text, (w - corner_size + 15, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, text_color, 3)

        safety_stats = self.safety_detector.get_safety_stats()
        total_checks = safety_stats.get('total_checks', 0)
        danger_count = safety_stats.get('danger_count', 0)
        warning_count = safety_stats.get('warning_count', 0)

        if total_checks > 0:
            score = max(0, 100 - (danger_count * 10 + warning_count * 5))
            score_text = f"安全分: {score}"
            cv2.putText(frame, score_text, (w - corner_size + 10, 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)

        if messages:
            first_msg = messages[0][:20]
            msg_text = first_msg + "..." if len(messages[0]) > 20 else first_msg
            cv2.putText(frame, msg_text, (w - corner_size + 10, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)

        return frame
