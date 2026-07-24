"""
视频处理模块 - 负责设备/模型切换、摄像头/视频文件管理

重构后职责：
1. 摄像头切换、视频文件打开、摄像头模式恢复
2. 旋转/镜像/骨架开关（镜像需同步 AppState 与 VideoThread）
3. 设备/模型切换（含回滚逻辑，通过信号请求 main_window 重建 video_thread）

已移除（移入 FramePipeline）：
- update_image / draw_skeleton_on_frame / draw_angle_lines / update_ui_components
"""

import os
import cv2
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog
from core.translations import Translations as T


class VideoProcessor(QObject):
    """视频处理器类（重构后仅保留设备/模型/摄像头切换逻辑）"""

    # ===== 信号 =====
    status_message = pyqtSignal(str)                  # 状态栏消息
    video_thread_recreate_requested = pyqtSignal()    # 请求 main_window 重建 video_thread

    def __init__(self, app_state, video_thread, pose_processor, video_display, counter_manager=None):
        """
        Args:
            app_state: AppState 实例（状态读写）
            video_thread: VideoThread 实例
            pose_processor: RTMPoseProcessor 实例
            video_display: VideoDisplay 实例
            counter_manager: CounterManager 实例（用于 reset_exercise_state）
        """
        super().__init__()
        self.app_state = app_state
        self.video_thread = video_thread
        self.pose_processor = pose_processor
        self.video_display = video_display
        self.counter_manager = counter_manager

    # =====================================================================
    # 摄像头/视频文件
    # =====================================================================
    def change_camera(self, index):
        """切换摄像头"""
        self.video_thread.set_camera(index)
        self.status_message.emit(T.get("switched_to_camera").format(index=index))

    def open_video_file(self):
        """打开视频文件"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            None, T.get("open_video"), "", T.get("video_files"), options=options
        )

        if file_name:
            try:
                # 清除当前计数状态
                if self.counter_manager is not None:
                    self.counter_manager.reset_counter()

                video_name = os.path.basename(file_name)
                self.status_message.emit(T.get("current_video").format(name=video_name))

                # 将文件路径传递给视频线程，设置为非循环播放模式
                self.video_thread.set_video_file(file_name, loop=False)
            except Exception as e:
                print(f"Error opening video file: {e}")
                self.status_message.emit(T.get("failed_open_video").format(error=str(e)))

    def switch_to_camera_mode(self):
        """切换回摄像头模式"""
        try:
            # 清除当前计数状态
            if self.counter_manager is not None:
                self.counter_manager.reset_counter()

            self.status_message.emit(T.get("camera_mode_active"))
            self.video_thread.set_camera(0)  # 使用默认摄像头
        except Exception as e:
            print(f"Error switching to camera mode: {e}")
            self.status_message.emit(T.get("failed_open_video").format(error=str(e)))

    # =====================================================================
    # 显示开关
    # =====================================================================
    def toggle_rotation(self, rotate):
        """切换视频旋转模式"""
        self.video_thread.set_rotation(rotate)
        self.video_display.set_orientation(portrait_mode=rotate)
        if rotate:
            self.status_message.emit(T.get("portrait_mode"))
        else:
            self.status_message.emit(T.get("landscape_mode"))

    def toggle_mirror(self, mirror):
        """
        切换镜像模式
        关键约束：mirror_mode 变更时必须同时更新 VideoThread
        """
        # 1. 更新 AppState
        self.app_state.mirror_mode = mirror
        # 2. 同步更新 VideoThread（关键：避免双重镜像导致关键点错位）
        if self.video_thread is not None:
                self.video_thread.set_mirror(mirror)
        self.status_message.emit(T.get("mirror_on" if mirror else "mirror_off"))

    # =====================================================================
    # 设备/模型切换（含回滚逻辑）
    # =====================================================================
    def change_device(self, device):
        """切换推理设备 (cpu/cuda)"""
        try:
            if device == self.app_state.device:
                return

            # 停止视频处理
            self.video_thread.stop()
            self.status_message.emit(T.get("switching_device").format(device=device))

            old_device = self.app_state.device
            self.app_state.device = device
            print(f"Switching device: {old_device} -> {device}")

            # 更新RTMPose处理器设备
            self.pose_processor.update_device(device)

            # 请求 main_window 重建 video_thread（AppController 负责实际重建）
            self.video_thread_recreate_requested.emit()

            self.status_message.emit(
                T.get("device_active_msg").format(mode=self.app_state.model_mode, device=device)
            )

        except Exception as e:
            error_msg = T.get("device_switch_failed").format(error=str(e))
            self.status_message.emit(error_msg)
            print(error_msg)

            # 回滚：覆盖所有相关组件（VideoThread / PoseProcessor / AppState.device）
            try:
                self.app_state.device = old_device
                self.pose_processor.update_device(old_device)
                self.video_thread_recreate_requested.emit()
                self.status_message.emit(T.get("rolled_back_to").format(device=old_device))
            except Exception:
                self.status_message.emit(T.get("critical_device_error"))

    def change_model(self, model_mode):
        """切换RTMPose模型模式"""
        try:
            if model_mode == self.app_state.model_mode:
                return

            # 停止视频处理
            self.video_thread.stop()
            self.status_message.emit(T.get("switching_model").format(mode=model_mode))

            old_model_mode = self.app_state.model_mode
            self.app_state.model_mode = model_mode
            print(f"Switching RTMPose mode: {old_model_mode} -> {model_mode}")

            # 更新RTMPose处理器模式
            self.pose_processor.update_model(model_mode)

            # 请求重建 video_thread
            self.video_thread_recreate_requested.emit()

            self.status_message.emit(T.get("switched_to_model").format(mode=model_mode))

        except Exception as e:
            error_msg = T.get("model_switch_failed").format(error=str(e))
            self.status_message.emit(error_msg)
            print(error_msg)

            # 回滚：覆盖所有相关组件
            try:
                self.app_state.model_mode = old_model_mode
                self.pose_processor.update_model(old_model_mode)
                self.video_thread_recreate_requested.emit()
                self.status_message.emit(T.get("rolled_back_to_model").format(mode=old_model_mode))
            except Exception:
                self.status_message.emit(T.get("critical_model_error"))
