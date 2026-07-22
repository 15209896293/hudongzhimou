import os
import numpy as np
from enum import Enum

# 复用共享缓存，避免重复读盘
try:
    from core.rtmpose_processor import _load_exercises_json as _load_cached_json
except ImportError:
    _load_cached_json = None

# 使用统一的 AngleUtils 替代本类内的 calculate_angle
from core.services.angle_utils import AngleUtils


class SafetyLevel(Enum):
    SAFE = 0
    WARNING = 1
    DANGER = 2


class AngleSafetyDetector:
    """实时角度安全检测模块"""

    def __init__(self, exercises_path=None):
        self.exercises_data = self._load_exercises(exercises_path)
        self.current_exercise = None
        self.last_voice_time = {}       # DANGER: 每个 issue_desc 的上次语音时间戳
        self.warned_issues = set()      # WARNING: 已提醒过的关节（仅一次）
        from core.services import AppConfig
        self.danger_repeat_interval = AppConfig.DANGER_REPEAT_INTERVAL
        self.safety_stats = {
            'total_checks': 0,
            'warning_count': 0,
            'danger_count': 0,
            'issues': {}
        }

    def _load_exercises(self, exercises_path=None):
        if _load_cached_json is not None:
            data = _load_cached_json()
            return data.get('exercises', {})

        # 降级：使用 PathManager 加载
        import json
        from core.services import PathManager
        if exercises_path is None:
            exercises_path = PathManager.get_exercises_file_path()

        if os.path.exists(exercises_path):
            with open(exercises_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('exercises', {})
        return {}

    def set_exercise(self, exercise_type):
        self.current_exercise = exercise_type
        self.safety_stats = {
            'total_checks': 0,
            'warning_count': 0,
            'danger_count': 0,
            'issues': {}
        }
        self.last_voice_time = {}
        self.warned_issues = set()

        if hasattr(self, '_user_profile') and self._user_profile:
            self.apply_user_profile(self._user_profile)

    def set_user_profile(self, user_profile):
        """设置用户档案，后续切换运动时会自动应用个性化阈值"""
        self._user_profile = user_profile
        if self.current_exercise:
            self.apply_user_profile(user_profile)

    def apply_user_profile(self, user_profile):
        """根据用户档案调整安全阈值"""
        if not user_profile or not self.current_exercise:
            return

        if self.current_exercise not in self.exercises_data:
            return

        exercise_config = self.exercises_data[self.current_exercise]
        thresholds = exercise_config.get('safety_thresholds', {})
        if not thresholds:
            return

        height = user_profile.get('height', 170)
        weight = user_profile.get('weight', 65)
        age = user_profile.get('age', 25)
        injury_history = user_profile.get('injury_history', [])

        height_factor = (height - 170) / 10
        knee_adjust = height_factor * 2

        if age > 40:
            age_adjust = (age - 40) * 0.5
        else:
            age_adjust = 0

        injury_adjust = 0
        if isinstance(injury_history, list):
            for injury in injury_history:
                injury_str = str(injury).lower()
                if '膝' in injury_str or 'knee' in injury_str:
                    injury_adjust += 5
                if '腰' in injury_str or 'back' in injury_str or '腰背' in injury_str:
                    if 'back' in thresholds:
                        thresholds['back']['warning_min'] = max(
                            thresholds['back'].get('warning_min', 150) + 3,
                            thresholds['back']['min']
                        )

        if 'knee' in thresholds:
            adjusted_min = thresholds['knee']['min'] + knee_adjust + age_adjust + injury_adjust
            adjusted_warning_min = adjusted_min + 10
            if adjusted_min < thresholds['knee']['max']:
                thresholds['knee']['min'] = int(adjusted_min)
                thresholds['knee']['warning_min'] = int(adjusted_warning_min)

        exercise_config['safety_thresholds'] = thresholds

    def calculate_angle(self, point1, point2, point3):
        """计算三点之间的角度（委托给 AngleUtils，保留接口以兼容外部调用）"""
        return AngleUtils.calculate_angle(point1, point2, point3)

    def extract_joint_angles(self, keypoints):
        """从关键点中提取所有关键关节角度"""
        angles = {}
        if keypoints is None or len(keypoints) < 17:
            return angles

        NOSE, L_EYE, R_EYE, L_EAR, R_EAR = 0, 1, 2, 3, 4
        L_SHOULDER, R_SHOULDER = 5, 6
        L_ELBOW, R_ELBOW = 7, 8
        L_WRIST, R_WRIST = 9, 10
        L_HIP, R_HIP = 11, 12
        L_KNEE, R_KNEE = 13, 14
        L_ANKLE, R_ANKLE = 15, 16

        # 膝盖
        lk = AngleUtils.calculate_angle(keypoints[L_HIP], keypoints[L_KNEE], keypoints[L_ANKLE])
        rk = AngleUtils.calculate_angle(keypoints[R_HIP], keypoints[R_KNEE], keypoints[R_ANKLE])
        if lk is not None and rk is not None:
            angles['knee'] = (lk + rk) / 2

        # 肘部
        le = AngleUtils.calculate_angle(keypoints[L_SHOULDER], keypoints[L_ELBOW], keypoints[L_WRIST])
        re = AngleUtils.calculate_angle(keypoints[R_SHOULDER], keypoints[R_ELBOW], keypoints[R_WRIST])
        if le is not None and re is not None:
            angles['elbow'] = (le + re) / 2

        # 肩部
        ls = AngleUtils.calculate_angle(keypoints[L_HIP], keypoints[L_SHOULDER], keypoints[L_ELBOW])
        rs = AngleUtils.calculate_angle(keypoints[R_HIP], keypoints[R_SHOULDER], keypoints[R_ELBOW])
        if ls is not None and rs is not None:
            angles['shoulder'] = (ls + rs) / 2

        # 背部/髋部
        lb = AngleUtils.calculate_angle(keypoints[L_SHOULDER], keypoints[L_HIP], keypoints[L_KNEE])
        rb = AngleUtils.calculate_angle(keypoints[R_SHOULDER], keypoints[R_HIP], keypoints[R_KNEE])
        if lb is not None and rb is not None:
            avg = (lb + rb) / 2
            angles['back'] = avg
            angles['hip'] = avg
            angles['lower_back'] = avg

        # 颈部
        neck = AngleUtils.calculate_angle(keypoints[L_EAR], keypoints[NOSE], keypoints[L_SHOULDER])
        if neck is not None:
            angles['neck'] = neck

        return angles

    def check_safety(self, keypoints, current_time_ms):
        """检查安全性并返回检测结果"""
        result = {
            'level': SafetyLevel.SAFE,
            'messages': [],
            'voice_tips': [],
            'angles': {},
            'issues': []
        }

        if self.current_exercise not in self.exercises_data:
            return result

        exercise_config = self.exercises_data[self.current_exercise]
        thresholds = exercise_config.get('safety_thresholds', {})
        voice_tips = exercise_config.get('voice_tips', {})

        if not thresholds:
            return result

        # 无有效关键点时不检测（避免无人时误报"安全"）
        if keypoints is None or not np.any(keypoints):
            return result

        angles = self.extract_joint_angles(keypoints)
        result['angles'] = angles

        self.safety_stats['total_checks'] += 1

        for joint, threshold in thresholds.items():
            if joint not in angles:
                continue

            angle = angles[joint]
            level = SafetyLevel.SAFE
            issue_desc = None

            # 正确逻辑：先判断绝对危险区 (< min 或 > max)，再判断警告区
            if angle < threshold['min']:
                level = SafetyLevel.DANGER
                issue_desc = f"{joint}_min"
            elif angle < threshold.get('warning_min', threshold['min']):
                level = SafetyLevel.WARNING
                issue_desc = f"{joint}_min"
            elif angle > threshold['max']:
                level = SafetyLevel.DANGER
                issue_desc = f"{joint}_max"
            elif angle > threshold.get('warning_max', threshold['max']):
                level = SafetyLevel.WARNING
                issue_desc = f"{joint}_max"

            if level != SafetyLevel.SAFE:
                if level == SafetyLevel.DANGER:
                    self.safety_stats['danger_count'] += 1
                else:
                    self.safety_stats['warning_count'] += 1

                if issue_desc not in self.safety_stats['issues']:
                    self.safety_stats['issues'][issue_desc] = 0
                self.safety_stats['issues'][issue_desc] += 1

                if level.value > result['level'].value:
                    result['level'] = level

                color = "🔴" if level == SafetyLevel.DANGER else "🟡"
                joint_names = {
                    'knee': '膝盖', 'elbow': '肘部', 'shoulder': '肩部',
                    'back': '背部', 'hip': '髋部', 'neck': '颈部',
                    'lower_back': '下背部', 'spine': '脊柱'
                }
                jn = joint_names.get(joint, joint)
                result['messages'].append(
                    f"{color} {jn}角度: {int(angle)}° (安全范围: {threshold['min']}°-{threshold['max']}°)"
                )
                result['issues'].append({
                    'joint': joint, 'angle': angle, 'level': level,
                    'threshold': threshold
                })

                if issue_desc in voice_tips:
                    if level == SafetyLevel.DANGER:
                        # DANGER: 即时播报 + 每10秒重复（独立计时，不受 WARNING 干扰）
                        last_time = self.last_voice_time.get(issue_desc, 0)
                        if current_time_ms - last_time >= self.danger_repeat_interval:
                            result['voice_tips'].append(voice_tips[issue_desc])
                            self.last_voice_time[issue_desc] = current_time_ms
                    else:
                        # WARNING: 仅提醒一次，不写入 last_voice_time（避免阻挡后续 DANGER）
                        if issue_desc not in self.warned_issues:
                            result['voice_tips'].append(voice_tips[issue_desc])
                            self.warned_issues.add(issue_desc)

        return result

    def get_safety_stats(self):
        return self.safety_stats.copy()
