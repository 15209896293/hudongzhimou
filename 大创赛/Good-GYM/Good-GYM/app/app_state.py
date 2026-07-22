"""
AppState - 集中状态管理
将散落在 main_window 上的所有业务状态统一管理，消除 Manager 之间的隐式耦合
"""


class AppState:
    """
    应用运行时状态集中仓库。
    所有 Manager 通过 AppState 读写状态，不再直接互相访问。
    """

    def __init__(self):
        # ========== 推理/模型相关 ==========
        self.device = 'cpu'                 # 推理设备: 'cpu' / 'cuda'
        self.model_mode = 'lightweight'     # 模型模式
        self.model_initialized = False      # 模型是否已加载
        self.init_error_message = None      # 初始化错误信息

        # ========== 运动类型相关 ==========
        self.exercise_type = 'squat'        # 当前运动类型
        self.show_skeleton = True           # 是否显示骨架
        self.mirror_mode = True             # 是否镜像
        self.rotate_video = True            # 是否旋转视频

        # ========== 计数相关 ==========
        self.current_count = 0              # 当前自动计数值
        self.manual_count = 0               # 手动调整计数
        self.is_resetting = False           # 是否正在重置
        self.target_count = None            # 目标次数

        # ========== 帧数据（推理结果） ==========
        self.current_keypoints = None       # 当前骨架关键点
        self.current_fps = 0                # 当前帧率
        self.current_angle = None           # 当前关节角度
        self.current_angle_point = None     # 角度线连接点
        self.current_inference_frame = None # 当前推理帧

        # ========== 训练统计 ==========
        self.start_time = None              # 训练开始时间戳
        self.current_mode = 'workout'       # 当前模式: 'workout' / 'stats'

        # ========== 安全检测结果 ==========
        self.safety_result = None           # 最近一次安全检测结果
        self.is_voice_enabled = True        # 语音提醒是否开启

        # ========== 界面语言 ==========
        self.current_language = 'zh'        # 当前界面语言: 'zh' / 'en'

        # ========== 用户档案 ==========
        self.user_profile = None            # 用户档案数据（dict 或 None）

        # ========== 训练会话 ==========
        self.session_state = 'idle'         # 会话状态: idle/training/paused/ended
        self.session_start_time = None      # 会话开始时间戳
        self.session_duration = 0           # 会话时长（秒）
        self.session_rep_count = 0          # 会话内计数
        self.session_risk_score = 100       # 会话风险评分（0-100）

    def reset_training_state(self):
        """重置训练状态（切换运动或重置计数时调用）"""
        self.current_count = 0
        self.manual_count = 0
        self.is_resetting = False
        self.start_time = None
        self.safety_result = None
