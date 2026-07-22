"""
全局配置常量 - 集中管理所有业务参数，避免魔法数字散落在各处
"""


class AppConfig:
    """应用全局配置"""

    # ========== 推理相关 ==========
    INFERENCE_SKIP_INTERVAL = 2         # 推理跳帧间隔（每N帧推理一次）
    DEFAULT_CONF_THRESHOLD = 0.35       # 关键点置信度阈值
    MODEL_DELAYED_LOAD = True           # 是否延迟加载模型
    DEFAULT_MODEL_MODE = 'lightweight'  # 默认模型模式

    # ========== 安全检测相关 ==========
    SAFETY_SKIP_INTERVAL = 3            # 安全检测节流间隔（每N帧检测一次）
    DANGER_REPEAT_INTERVAL = 10000      # DANGER重复提醒间隔（毫秒）

    # ========== 骨架绘制相关 ==========
    SHOW_SKELETON = True
    SKELETON_COLOR = (0, 255, 0)        # 骨架线颜色 (BGR)
    SKELETON_THICKNESS = 3              # 骨架线粗细
    ANGLE_LINE_COLOR = (255, 165, 0)    # 角度线颜色 (BGR)
    ANGLE_LINE_THICKNESS = 2            # 角度线粗细
    ANGLE_TEXT_COLOR = (255, 165, 0)    # 角度文字颜色 (BGR)
    ANGLE_TEXT_SCALE = 0.6              # 角度文字大小
    ANGLE_TEXT_THICKNESS = 2            # 角度文字粗细

    # ========== 设备相关 ==========
    DEFAULT_DEVICE = 'cpu'
    DEFAULT_CAMERA_ID = 0
    DEFAULT_DISPLAY_WIDTH = 1920        # 显示分辨率
    DEFAULT_DISPLAY_HEIGHT = 1080
    DEFAULT_INFERENCE_WIDTH = 640       # 推理分辨率
    DEFAULT_INFERENCE_HEIGHT = 360

    # ========== UI相关 ==========
    ANIMATION_DURATION = 1000           # 计数动画时长（毫秒）
    MILESTONE_INTERVAL = 5              # 里程碑间隔
