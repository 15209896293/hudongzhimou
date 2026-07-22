import numpy as np
from collections import deque
import time
import json
import os
import sys

# 模块级缓存：从 core.rtmpose_processor 复用共享缓存（全项目只读一次磁盘）
try:
    from core.rtmpose_processor import _load_exercises_json as _load_cached_json
except ImportError:
    # 降级：如果导入失败（打包环境），使用本地加载
    _load_cached_json = None


class ExerciseCounter:
    """Basic exercise counter with angle-based detection"""
    
    def __init__(self, smoothing_window=5):
        from core.services.angle_utils import AngleUtils
        self.angle_utils = AngleUtils
        # Core counting variables
        self.counter = 0
        self.stage = None
        
        # Basic features
        self.smoothing_window = smoothing_window
        self.angle_history = deque(maxlen=smoothing_window)
        self.last_count_time = 0
        self.min_rep_time = 0.5  # Minimum time between reps (seconds)
        
        # Exercise configurations
        self.exercise_configs = self.get_exercise_configs()
        
        # Independent counting for leg exercises - load from config
        self.leg_exercises = [
            exercise_type for exercise_type, config in self.exercise_configs.items()
            if config.get('is_leg_exercise', False)
        ]
        self.leg_stages = {'left': None, 'right': None}  # Track each leg's stage
    
    def get_exercises_file_path(self):
        """Get exercises.json file path, compatible with development and packaged environments"""
        from core.services.path_manager import PathManager
        return PathManager.get_exercises_file_path()
    
    def get_exercise_configs(self):
        """从缓存加载运动动作配置（与 rtmpose_processor 共享，只读一次磁盘）"""
        if _load_cached_json is not None:
            data = _load_cached_json()
        else:
            # 降级：打包环境下单独加载
            exercises_file = self.get_exercises_file_path()
            try:
                if os.path.exists(exercises_file):
                    with open(exercises_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    print(f"ERROR: Exercises file not found at {exercises_file}")
                    return {}
            except Exception as e:
                print(f"ERROR loading exercises from JSON: {e}")
                return {}

        exercises = data.get('exercises', {})
        configs = {}
        for exercise_type, config in exercises.items():
            configs[exercise_type] = {
                'down_angle': config.get('down_angle'),
                'up_angle': config.get('up_angle'),
                'keypoints': config.get('keypoints', {}),
                'is_leg_exercise': config.get('is_leg_exercise', False)
            }
        return configs
    
    def reset_counter(self):
        """Reset counter to initial state"""
        self.counter = 0
        self.stage = None
        self.angle_history.clear()
        self.leg_stages = {'left': None, 'right': None}
    
    def calculate_angle(self, a, b, c):
        """Calculate angle between three points"""
        return self.angle_utils.calculate_angle(a, b, c)
    
    def smooth_angle(self, angle):
        """移动平均滤波降噪（小窗口，轻量实现）"""
        if angle is None:
            return None

        self.angle_history.append(angle)

        if len(self.angle_history) < 3:
            return angle

        # 对 5 帧窗口做均值滤波，比 median+std 过滤更轻量
        return float(np.mean(list(self.angle_history)))
    
    def check_rep_timing(self):
        """Prevent counting reps too quickly"""
        current_time = time.time()
        if current_time - self.last_count_time < self.min_rep_time:
            return False
        return True
    
    def count_exercise(self, keypoints, exercise_type):
        """Generic exercise counting function"""
        try:
            if exercise_type not in self.exercise_configs:
                print(f"Unknown exercise type: {exercise_type}")
                return None
                
            config = self.exercise_configs[exercise_type]
            kp = config['keypoints']
            
            # Calculate angles for both sides
            left_angle = self.calculate_angle(
                keypoints[kp['left'][0]],  # first point
                keypoints[kp['left'][1]],  # middle point
                keypoints[kp['left'][2]]   # last point
            )
            
            right_angle = self.calculate_angle(
                keypoints[kp['right'][0]],  # first point
                keypoints[kp['right'][1]],  # middle point
                keypoints[kp['right'][2]]   # last point
            )
            
            if left_angle is None or right_angle is None:
                return None
            
            # Handle leg exercises differently
            if exercise_type in self.leg_exercises:
                return self.count_leg_exercise(left_angle, right_angle, config)
            
            # For other exercises, use average angle
            avg_angle = (left_angle + right_angle) / 2
            smoothed_angle = self.smooth_angle(avg_angle)
            
            if smoothed_angle is None:
                return None
            
            # Get thresholds
            up_threshold = config['up_angle']
            down_threshold = config['down_angle']
            
            # Counting logic with timing check
            if smoothed_angle > up_threshold:
                self.stage = "up"
            elif (smoothed_angle < down_threshold and 
                  self.stage == "up" and 
                  self.check_rep_timing()):
                
                self.stage = "down"
                self.counter += 1
                self.last_count_time = time.time()
                
            return smoothed_angle
            
        except Exception as e:
            print(f"Exercise counting error: {e}")
            return None
    
    def count_leg_exercise(self, left_angle, right_angle, config):
        """Count leg exercises with complete up-down cycles"""
        up_threshold = config['up_angle']
        down_threshold = config['down_angle']
        
        # Check if either leg meets the criteria
        if self.check_rep_timing():
            # Left leg
            if left_angle > up_threshold:
                self.leg_stages['left'] = "up"
            elif (left_angle < down_threshold and 
                  self.leg_stages['left'] == "up"):
                self.counter += 1
                self.last_count_time = time.time()
                self.leg_stages['left'] = "down"
            
            # Right leg
            if right_angle > up_threshold:
                self.leg_stages['right'] = "up"
            elif (right_angle < down_threshold and 
                  self.leg_stages['right'] == "up"):
                self.counter += 1
                self.last_count_time = time.time()
                self.leg_stages['right'] = "down"
        
        # Return average angle for display purposes
        return (left_angle + right_angle) / 2
    
    # Wrapper functions for different exercises
    def count_squat(self, keypoints):
        """Count squat repetitions"""
        return self.count_exercise(keypoints, 'squat')
    
    def count_pushup(self, keypoints):
        """Count pushup repetitions"""
        return self.count_exercise(keypoints, 'pushup')
    
    def count_situp(self, keypoints):
        """Count situp repetitions"""
        return self.count_exercise(keypoints, 'situp')
    
    def count_bicep_curl(self, keypoints):
        """Count bicep curl repetitions"""
        return self.count_exercise(keypoints, 'bicep_curl')
    
    def count_lateral_raise(self, keypoints):
        """Count lateral raise repetitions"""
        return self.count_exercise(keypoints, 'lateral_raise')
    
    def count_overhead_press(self, keypoints):
        """Count overhead press repetitions"""
        return self.count_exercise(keypoints, 'overhead_press')
    
    def count_leg_raise(self, keypoints):
        """Count leg raise repetitions"""
        return self.count_exercise(keypoints, 'leg_raise')
    
    def count_knee_raise(self, keypoints):
        """Count knee raise repetitions"""
        return self.count_exercise(keypoints, 'knee_raise')
    
    def count_knee_press(self, keypoints):
        """Count knee press repetitions"""
        return self.count_exercise(keypoints, 'knee_press')
    
    def count_crunch(self, keypoints):
        """Count crunch repetitions"""
        return self.count_exercise(keypoints, 'crunch')
    
    def count_pullup(self, keypoints):
        """Count pullup repetitions"""
        return self.count_exercise(keypoints, 'pullup')
