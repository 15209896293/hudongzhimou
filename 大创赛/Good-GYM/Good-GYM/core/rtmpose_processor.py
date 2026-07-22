import os
import cv2
import sys
import json
import numpy as np

# Python 3.14 兼容性修复：必须在此处显式导入 onnxruntime，
# 否则 rtmlib 内部延迟导入时会因 DLL 初始化失败而崩溃
import onnxruntime as _ort  # noqa: F401

# ═══════════════════════════════════════════════════════════════
# 关键优化：限制 ONNX Runtime 线程数，防止推理吃满所有 CPU 核心
# rtmlib 创建 InferenceSession 时不传 sess_options，默认用满全部核心
# ═══════════════════════════════════════════════════════════════
_original_inference_session = _ort.InferenceSession

class _ThreadLimitedSession(_original_inference_session):
    """包装 InferenceSession，默认限制线程数防止 CPU 满载"""
    def __init__(self, *args, **kwargs):
        if 'sess_options' not in kwargs:
            opts = _ort.SessionOptions()
            opts.intra_op_num_threads = 2   # 每个算子最多 2 线程
            opts.inter_op_num_threads = 1   # 图执行单线程
            opts.graph_optimization_level = _ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
            kwargs['sess_options'] = opts
        super().__init__(*args, **kwargs)

_ort.InferenceSession = _ThreadLimitedSession

from rtmlib import Wholebody
from core.services import PathManager

# 模块级缓存：exercises.json 全项目共享一份，避免重复读取
_EXERCISES_JSON_CACHE = None


def _load_exercises_json():
    """加载 exercises.json，模块级缓存（全项目只读一次磁盘）"""
    global _EXERCISES_JSON_CACHE
    if _EXERCISES_JSON_CACHE is not None:
        return _EXERCISES_JSON_CACHE

    # 使用 PathManager 统一路径管理（兼容打包/开发环境）
    path = PathManager.get_exercises_file_path()

    try:
        with open(path, 'r', encoding='utf-8') as f:
            _EXERCISES_JSON_CACHE = json.load(f)
    except Exception as e:
        print(f"ERROR loading exercises.json: {e}")
        _EXERCISES_JSON_CACHE = {}
    return _EXERCISES_JSON_CACHE


class RTMPoseProcessor:
    """RTMPose pose detection processor — 模型延迟加载以加速启动"""

    def __init__(self, exercise_counter, mode='balanced', backend='onnxruntime', device='cpu'):
        self.exercise_counter = exercise_counter
        self.show_skeleton = True
        from core.services import AppConfig
        self.conf_threshold = AppConfig.DEFAULT_CONF_THRESHOLD
        self.device = device
        self.backend = backend
        self.current_mode = mode

        # 延迟加载：不在 __init__ 中加载 ONNX 模型，启动速度提升 2-3 秒
        self.wholebody = None
        self._model_loaded = False

        self.keypoint_mapping = self.get_keypoint_mapping()

        # 从缓存加载运动配置（不再重复读磁盘）
        self.exercise_configs = self.load_exercise_configs()

        # 模型初始化状态（延迟加载期间为 None，UI 显示"加载中"而非错误）
        self.model_initialized = False
        self.init_error_message = None

    def _ensure_model_loaded(self):
        """确保模型已加载（延迟加载入口，首次调用时初始化 ONNX 模型）"""
        if self._model_loaded:
            return
        self._model_loaded = True
        self.init_rtmpose(self.current_mode)
        self.model_initialized = self.wholebody is not None
        if not self.model_initialized:
            self.init_error_message = self.init_error_message or "模型初始化失败，请检查 models/ 目录下的 ONNX 文件是否完整"

    def init_rtmpose(self, mode='balanced'):
        """Initialize RTMPose model"""
        self.current_mode = mode
        try:
            print(f"Initializing RTMPose model (mode: {mode}, backend: {self.backend}, device: {self.device})")

            # 使用 PathManager 获取模型目录（兼容打包/开发环境）
            models_dir = PathManager.get_models_dir()
            if os.path.exists(models_dir):
                # Try to use local models
                det_model = PathManager.get_model_path('yolox_nano_8xb8-300e_humanart-40f6f0d0.onnx')

                # Select different pose detection models based on mode
                if mode == 'lightweight':
                    pose_model = PathManager.get_model_path(
                        'rtmpose-t_simcc-body7_pt-body7_420e-256x192-026a1439_20230504.onnx')
                    pose_input_size = (192, 256)
                elif mode == 'performance':
                    pose_model = PathManager.get_model_path(
                        'rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.onnx')
                    pose_input_size = (192, 256)
                else:  # balanced
                    pose_model = PathManager.get_model_path(
                        'rtmpose-s_simcc-body7_pt-body7_420e-256x192-acd4a1ef_20230504.onnx')
                    pose_input_size = (192, 256)

                if os.path.exists(det_model) and os.path.exists(pose_model):
                    print(f"Using local model files ({mode} mode)")
                    self.wholebody = Wholebody(
                        det=det_model,
                        det_input_size=(416, 416),
                        pose=pose_model,
                        pose_input_size=pose_input_size,
                        backend=self.backend,
                        device=self.device
                    )
                    print("RTMPose local model initialization successful")
                    return
                else:
                    print("Local model files incomplete, using online download")
            else:
                print("models directory doesn't exist, using online download")

            # Online fallback initialization
            self.wholebody = Wholebody(
                mode=mode,
                backend=self.backend,
                device=self.device
            )
            print("RTMPose online model initialization successful")

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"RTMPose initialization failed: {e}")
            print(f"Full traceback:\n{error_detail}")
            self.wholebody = None
            self.init_error_message = f"模型初始化失败: {str(e)[:200]}"

    def get_keypoint_mapping(self):
        """Get keypoint mapping (COCO 17 keypoint format)"""
        # RTMPose and YOLO both use COCO 17 keypoint format, same order
        # 0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear
        # 5: left_shoulder, 6: right_shoulder, 7: left_elbow, 8: right_elbow
        # 9: left_wrist, 10: right_wrist, 11: left_hip, 12: right_hip
        # 13: left_knee, 14: right_knee, 15: left_ankle, 16: right_ankle
        return list(range(17))  # 1:1 mapping

    def load_exercise_configs(self):
        """从模块级缓存加载运动配置（不再重复读磁盘）"""
        data = _load_exercises_json()
        exercises = data.get('exercises', {})

        configs = {}
        for exercise_type, config in exercises.items():
            configs[exercise_type] = {
                'angle_point': config.get('angle_point', [])
            }
        return configs

    def update_model(self, mode='balanced'):
        """Update model"""
        print(f"Updating RTMPose model to mode: {mode}")
        self.current_mode = mode
        self._model_loaded = False
        self.init_rtmpose(mode)
        self._model_loaded = True
        self.model_initialized = self.wholebody is not None
        print(f"RTMPose processor updated to mode: {mode}")

    def update_device(self, device):
        """Update inference device (cpu or cuda)"""
        print(f"Updating RTMPose device: {self.device} -> {device}")
        self.device = device
        self._model_loaded = False
        self.init_rtmpose(self.current_mode)
        self._model_loaded = True
        self.model_initialized = self.wholebody is not None
        print(f"RTMPose processor updated to device: {device}")

    def process_frame(self, frame, exercise_type):
        """处理单帧姿态检测和运动计数"""
        # 延迟加载：首次调用时初始化模型
        self._ensure_model_loaded()

        # Check if model is available
        if self.wholebody is None:
            if not hasattr(self, '_init_error_logged'):
                self._init_error_logged = True
                print(f"[ERROR] RTMPose model (wholebody) is None — skeleton detection disabled.")
                if self.init_error_message:
                    print(f"[ERROR] Reason: {self.init_error_message}")
            return None, None, None, None

        # 推理帧在上游已完成缩放到 ≤640，此处不再重复 resize
        h, w = frame.shape[:2]
        scale_factor = 1.0  # 默认不缩放

        # 仅当帧超出 640 限制时才缩放（安全网，正常流程不会触发）
        if w > 640 or h > 640:
            scale = min(640 / w, 640 / h)
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
            scale_factor = scale

        # Initialize results
        current_angle = None
        angle_point = None
        keypoints = None

        try:
            # Use RTMPose for pose detection
            detected_keypoints, scores = self.wholebody(frame)

            # Process results
            if detected_keypoints is not None and len(detected_keypoints) > 0:
                # Get first person's keypoints (highest confidence)
                # rtmlib returns keypoints as (17, 2) [x, y only], scores as (17,)
                kp_raw = detected_keypoints[0]
                confidence_scores = scores[0] if scores is not None else None

                # 合并坐标与置信度为统一 (17, 3) 格式 [x, y, conf]
                if confidence_scores is not None:
                    keypoints = np.column_stack([
                        kp_raw, confidence_scores.reshape(-1, 1)
                    ])
                    valid_mask = confidence_scores > self.conf_threshold
                    valid_count = valid_mask.sum()
                    # 低置信度点清零（还需对坐标做保留为 (0,0)，置信度置 0）
                    keypoints[~valid_mask] = [0, 0, 0]

                    # 一次性的调试输出：帮助诊断置信度问题
                    if not hasattr(self, '_conf_debug_printed'):
                        self._conf_debug_printed = True
                        print(f"[DEBUG] Confidence threshold: {self.conf_threshold}")
                        print(f"[DEBUG] Valid keypoints (first frame): {valid_count}/17")
                        print(f"[DEBUG] Score range: {confidence_scores.min():.3f} ~ {confidence_scores.max():.3f}")
                        print(f"[DEBUG] Per-point scores: {[f'{s:.2f}' for s in confidence_scores]}")
                else:
                    keypoints = kp_raw
                    valid_count = 17  # Assume all valid if no scores available

                # If need to scale back to original size
                if scale_factor != 1.0:
                    keypoints = keypoints / scale_factor

                # Only calculate angles if we have enough valid keypoints
                if valid_count >= 3:
                    # Get corresponding angle and joint points based on exercise type
                    current_angle, angle_point = self.get_exercise_angle(keypoints, exercise_type)

        except Exception as e:
            print(f"RTMPose processing failed: {e}")
            import traceback
            traceback.print_exc()

        # Return None for processed frame, current_angle, angle_point, and keypoints
        return None, current_angle, angle_point, keypoints

    def get_exercise_angle(self, keypoints, exercise_type):
        """Get angle based on exercise type"""
        current_angle = None
        angle_point = None

        try:
            # 优先使用专用包装方法，回退到通用 count_exercise
            dedicated_method = getattr(self.exercise_counter, f"count_{exercise_type}", None)
            if dedicated_method is not None:
                current_angle = dedicated_method(keypoints)
            elif hasattr(self.exercise_counter, 'count_exercise'):
                current_angle = self.exercise_counter.count_exercise(keypoints, exercise_type)
            else:
                current_angle = None

            # Get angle_point from config
            if current_angle is not None and exercise_type in self.exercise_configs:
                angle_point_indices = self.exercise_configs[exercise_type].get('angle_point', [])
                if len(angle_point_indices) == 3:
                    angle_point = [
                        keypoints[angle_point_indices[0]],
                        keypoints[angle_point_indices[1]],
                        keypoints[angle_point_indices[2]]
                    ]
        except Exception as e:
            print(f"Error calculating exercise angle: {e}")

        return current_angle, angle_point

    def set_skeleton_visibility(self, show):
        """Set skeleton display state"""
        self.show_skeleton = show
        print(f"RTMPose skeleton display: {'On' if show else 'Off'}")

    def set_conf_threshold(self, threshold):
        """调整置信度阈值（0.0 ~ 1.0），值越低越容易检测到骨骼，但可能增加误检"""
        self.conf_threshold = max(0.0, min(1.0, threshold))
        print(f"RTMPose confidence threshold set to: {self.conf_threshold}")