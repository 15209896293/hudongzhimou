import sys
import cv2
import numpy as np
import time
import os
from PyQt5.QtCore import Qt, QThread, pyqtSignal


def scan_available_cameras(max_index=10):
    """扫描电脑上所有可用摄像头，返回 [(设备ID, 名称), ...]

    遍历索引 0~max_index，尝试打开每个摄像头，成功读取一帧的视为可用。
    iVCam、DroidCam 等虚拟摄像头会被自动发现。
    """
    import sys as _sys
    available = []
    _devnull = open(os.devnull, 'w')
    _old_stderr = _sys.stderr
    _sys.stderr = _devnull
    try:
        for idx in range(max_index):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    name = f"摄像头 {idx}"
                    try:
                        backend_name = cap.getBackendName()
                        if backend_name:
                            name = f"{backend_name} #{idx}"
                    except Exception:
                        pass
                    available.append((idx, name))
                else:
                    print(f"[scan] Camera {idx} opened but read() returned False")
                cap.release()
            else:
                cap.release()
    finally:
        _sys.stderr = _old_stderr
        _devnull.close()
    print(f"[scan] Found {len(available)} cameras: {available}")
    return available


class VideoThread(QThread):
    """Video stream processing thread to avoid UI freezing"""
    change_pixmap_signal = pyqtSignal(np.ndarray, float)  # Add FPS parameter
    camera_error_signal = pyqtSignal(str)  # 摄像头错误信号
    
    def __init__(self, camera_id=0, rotate=True, display_width=1280, display_height=720, inference_width=640, inference_height=360):
        super().__init__()
        self.camera_id = camera_id
        self.rotate = rotate
        self._run_flag = True
        self.buffer_size = 1  # Buffer size, set to 1 to avoid delay
        self.video_file = None  # Local video file path
        self.is_camera = True  # Whether to use camera
        self.fps = 30  # Default frame rate
        self.loop_video = False  # Control whether to loop video playback
        self.video_ended = False  # Mark if video has ended
        self.mirror = False  # Added for mirror mode
        self.display_width = display_width
        self.display_height = display_height
        self.inference_width = inference_width
        self.inference_height = inference_height
        # 关键约束 #6：current_inference_frame 写入目标改为 AppState
        self.app_state = None

    def set_camera(self, camera_id):
        """Switch camera"""
        if self.isRunning():
            self._run_flag = False
            self.wait()
        self.camera_id = camera_id
        self.video_file = None  # Clear video file path
        self.is_camera = True  # Switch back to camera mode
        self._run_flag = True
        self.start()
    
    def set_rotation(self, rotate):
        """Set whether to rotate video"""
        self.rotate = rotate
        
    def set_mirror(self, mirror):
        """Set whether to mirror video"""
        self.mirror = mirror
        
    def set_video_file(self, file_path, loop=False):
        """Set video file path
        
        Args:
            file_path (str): Video file path
            loop (bool): Whether to loop video playback, default is False
        """
        if self.isRunning():
            self._run_flag = False
            self.wait()
        self.video_file = file_path
        self.is_camera = False  # Switch to video file mode
        self.loop_video = loop  # Set whether to loop playback
        self.video_ended = False  # Reset video end flag
        
        # Pre-detect video aspect ratio to decide which rotation mode to apply
        self.auto_detect_orientation(file_path)
        
        self._run_flag = True
        self.start()
        
    def auto_detect_orientation(self, file_path):
        """Automatically detect video file aspect ratio and set appropriate rotation mode"""
        try:
            if not os.path.exists(file_path):
                print(f"Error: Video file does not exist {file_path}")
                return
                
            temp_cap = cv2.VideoCapture(file_path)
            if not temp_cap.isOpened():
                print(f"Error: Cannot open video file for aspect ratio detection {file_path}")
                return
                
            # Get original video size information (not dependent on frame reading)
            original_width = int(temp_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            original_height = int(temp_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # If first frame can be obtained, use first frame size information to confirm
            ret, first_frame = temp_cap.read()
            if ret:
                height, width = first_frame.shape[:2]
                # Check if frame size matches video size
                if height != original_height or width != original_width:
                    # If there's a difference, use frame size
                    original_width = width
                    original_height = height
                    print("Frame size differs from video size, using frame size information")
            
            # Release temporary camera
            temp_cap.release()
            
            # Calculate aspect ratio
            aspect_ratio = original_width / original_height
            
            # Determine video orientation
            # Vertical ratio less than 0.8, horizontal ratio greater than 1.3, middle value is square
            is_vertical = aspect_ratio < 0.8
            
            # If it's a vertical video (9:16)
            if is_vertical:
                print(f"Detected vertical video (aspect ratio: {aspect_ratio:.2f}, size: {original_width}x{original_height})")
                self.rotate = False  # No rotation
                # Set display resolution
                self.display_width = max(720, original_width)
                self.display_height = int(self.display_width * original_height / original_width)
                # Set inference resolution
                self.inference_width = max(360, original_width)
                self.inference_height = int(self.inference_width * original_height / original_width)
            # Otherwise it's a horizontal video (16:9)
            else:
                print(f"Detected horizontal video (aspect ratio: {aspect_ratio:.2f}, size: {original_width}x{original_height})")
                self.rotate = False  # Also no rotation
                # Set display resolution
                self.display_height = 720
                self.display_width = int(self.display_height * aspect_ratio)
                # Set inference resolution
                self.inference_height = 480
                self.inference_width = int(self.inference_height * aspect_ratio)
        except Exception as e:
            print(f"Video aspect ratio detection error: {str(e)}")
            # Use default values when error occurs
            self.rotate = False
    
    def run(self):
        """Main thread loop"""
        # Open video source based on mode (camera or file)
        if self.is_camera:
            print(f"[VideoThread] Attempting cv2.VideoCapture({self.camera_id})...")
            print(f"[VideoThread] cv2 version: {cv2.__version__}")
            print(f"[VideoThread] sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
            print(f"[VideoThread] cv2 path: {cv2.__file__}")

            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                msg = f"Error: Cannot open camera {self.camera_id}"
                print(f"[VideoThread] {msg}")
                self.camera_error_signal.emit(msg)
                return

            # Set camera to high resolution for display
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.display_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.display_height)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)

            # Camera mode defaults to rotation (default to portrait mode)
            self.rotate = True

            print(f"Camera opened: ID={self.camera_id}, display_resolution={int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            print(f"Camera backend: {self.cap.getBackendName()}")
        else:
            # Open video file
            if not os.path.exists(self.video_file):
                print(f"Error: Video file does not exist {self.video_file}")
                return
                
            self.cap = cv2.VideoCapture(self.video_file)
            if not self.cap.isOpened():
                print(f"Error: Cannot open video file {self.video_file}")
                return
                
            video_name = os.path.basename(self.video_file)
            print(f"Video file opened: {video_name}, resolution={int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            
            # Get actual frame rate (may differ from requested)
            real_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            if real_fps == 0:
                real_fps = 30  # Default value
            
            # Limit maximum frame rate to 30fps
            self.fps = min(real_fps, 30)
            print(f"Frame rate: original {real_fps}fps, current display {self.fps}fps")
        
        # Initialize FPS calculation
        frame_count = 0
        start_time = time.time()
        fps_display = 0
        update_interval = 10  # Update FPS display every 10 frames
        
        # Run flag
        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                # 推理帧：从原始帧缩放（cv2.resize 创建新数组，不影响 frame）
                inference_frame = cv2.resize(frame, (self.inference_width, self.inference_height))

                # 旋转处理（cv2.rotate 创建新数组，安全）
                if self.rotate:
                    display_frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                    inference_frame = cv2.rotate(inference_frame, cv2.ROTATE_90_CLOCKWISE)
                else:
                    # 不旋转时必须拷贝：frame 可能被 VideoCapture 内部复用
                    display_frame = frame.copy()

                # 镜像统一由 video_processor 在绘制骨架后处理（避免双重镜像导致关键点错位）

                # 关键约束 #6：将推理帧存储在 AppState 中，供模型使用
                if self.app_state is not None:
                    self.app_state.current_inference_frame = inference_frame
                
                # Calculate FPS
                frame_count += 1
                if frame_count % update_interval == 0:
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    fps_display = frame_count / elapsed_time
                    frame_count = 0
                    start_time = time.time()
                
                # Send display frame and FPS information
                self.change_pixmap_signal.emit(display_frame, fps_display)
            else:
                # When reading video file fails, if in video file mode
                if not self.is_camera and self.video_file:
                    # Check if loop playback is needed
                    if self.loop_video:
                        # Loop mode: reset to beginning and continue playback
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = self.cap.read()
                        if ret:
                            # Send frame and FPS information
                            self.change_pixmap_signal.emit(frame, fps_display)
                        else:
                            # If reset still cannot read, output warning
                            print("Warning: Video file playback ended and cannot loop again")
                            self.video_ended = True
                    else:
                        # Non-loop mode: mark video as ended
                        if not self.video_ended:
                            print("Video playback completed, stopped at last frame")
                            self.video_ended = True
                else:
                    print("Warning: Cannot read video frame")
            
            # Read frames at target frame rate and control playback speed
            self.msleep(int(1000 / self.fps))  # 使用 QThread.msleep 避免阻塞线程退出
        
        # Release resources
        self.cap.release()
    
    def stop(self):
        """Stop thread"""
        self._run_flag = False
        self.wait()
