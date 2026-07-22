class Translations:
    """Translation module, provides Chinese-English text support"""
    
    # Current language (default Chinese)
    current_language = "zh"
    
    # Chinese-English translation dictionary
    translations = {
        # Application title and general
        "app_title": {
            "zh": "护动智眸 - AI运动防伤评估系统",
            "en": "HuDongZhiMou - AI Sports Injury Prevention System",
        },
        "ready": {
            "zh": "准备就绪",
            "en": "Ready",
        },
        
        # Menu items
        "tools_menu": {
            "zh": "工具",
            "en": "Tools",
        },
        "mode_menu": {
            "zh": "模式",
            "en": "Mode",
        },
        "help_menu": {
            "zh": "帮助",
            "en": "Help",
        },
        "language_menu": {
            "zh": "语言",
            "en": "Language",
        },
        "chinese": {
            "zh": "中文",
            "en": "Chinese",
        },
        "english": {
            "zh": "英文",
            "en": "English",
        },
        "skeleton_display": {
            "zh": "显示骨架",
            "en": "Show Skeleton",
        },
        "video_file": {
            "zh": "打开视频文件",
            "en": "Open Video File",
        },
        "camera_mode": {
            "zh": "切换到摄像头模式",
            "en": "Switch to Camera Mode",
        },
        "rotation_mode": {
            "zh": "竖屏模式",
            "en": "Vertical Mode",
        },
        "workout_mode": {
            "zh": "健身运动模式",
            "en": "Workout Mode",
        },
        "stats_mode": {
            "zh": "统计管理模式",
            "en": "Statistics Mode",
        },
        "about": {
            "zh": "关于",
            "en": "About",
        },
        
        # Control panel
        "exercise_data": {
            "zh": "运动数据",
            "en": "Exercise Data",
        },
        "count_completed": {
            "zh": "完成次数:",
            "en": "Count:",
        },
        "current_angle": {
            "zh": "当前角度:",
            "en": "Current Angle:",
        },
        "control_options": {
            "zh": "控制选项",
            "en": "Control Options",
        },
        "exercise_type": {
            "zh": "运动类型:",
            "en": "Exercise Type:",
        },
        "counter_controls": {
            "zh": "计数控制:",
            "en": "Counter Controls:",
        },
        "camera": {
            "zh": "摄像头:",
            "en": "Camera:",
        },
        "increase": {
            "zh": "增加",
            "en": "Increase",
        },
        "decrease": {
            "zh": "减少",
            "en": "Decrease",
        },
        "reset": {
            "zh": "重置",
            "en": "Reset",
        },
        "confirm": {
            "zh": "确认记录",
            "en": "Confirm",
        },
        "phase_display": {
            "zh": "阶段显示",
            "en": "Phase Display",
        },
        "current_phase": {
            "zh": "当前阶段:",
            "en": "Current Phase:",
        },
        "up": {
            "zh": "上升",
            "en": "Up",
        },
        "down": {
            "zh": "下降",
            "en": "Down",
        },
        "rest": {
            "zh": "休息",
            "en": "Rest",
        },
        "prepare": {
            "zh": "准备",
            "en": "Prepare",
        },
        
        # Exercise types
        "squat": {
            "zh": "深蹲",
            "en": "Squat",
        },
        "pushup": {
            "zh": "俯卧撑",
            "en": "Push-up",
        },
        "situp": {
            "zh": "仰卧起坐",
            "en": "Sit-up",
        },
        "bicep_curl": {
            "zh": "弯举",
            "en": "Bicep Curl",
        },
        "lateral_raise": {
            "zh": "侧平举",
            "en": "Lateral Raise",
        },
        "overhead_press": {
            "zh": "推举",
            "en": "Overhead Press",
        },
        "leg_raise": {
            "zh": "抬腿",
            "en": "Leg Raise",
        },
        "knee_raise": {
            "zh": "抬膝",
            "en": "Knee Raise",
        },
        "knee_press": {
            "zh": "压膝",
            "en": "Knee Press",
        },
        "crunch": {
            "zh": "卷腹",
            "en": "Crunch",
        },
        
        # Status bar messages
        "welcome": {
            "zh": "欢迎使用护动智眸",
            "en": "Welcome to HuDongZhiMou",
        },
        "language_changed": {
            "zh": "语言已更改",
            "en": "Language changed",
        },
        "switched_to_workout": {
            "zh": "已切换到健身运动模式",
            "en": "Switched to workout mode",
        },
        "switched_to_stats": {
            "zh": "已切换到统计管理模式",
            "en": "Switched to statistics mode",
        },
        "counter_reset": {
            "zh": "计数器已重置",
            "en": "Counter reset",
        },
        "goal_reached": {
            "zh": "目标达成！",
            "en": "Goal reached!",
        },
        "goal_updated": {
            "zh": "目标已更新",
            "en": "Goal updated",
        },
        
        # Statistics panel
        "fitness_statistics": {
            "zh": "健身统计",
            "en": "Fitness Statistics",
        },
        "today_tab": {
            "zh": "今日进度",
            "en": "Today",
        },
        "week_tab": {
            "zh": "本周统计",
            "en": "Week",
        },
        "month_tab": {
            "zh": "本月统计",
            "en": "Month",
        },
        "goals_tab": {
            "zh": "目标设置",
            "en": "Goals",
        },
        
        # Content for each tab
        "today_exercise_progress": {
            "zh": "今日运动进度",
            "en": "Today's Exercise Progress",
        },
        "no_goals_message": {
            "zh": "未设置任何运动目标",
            "en": "No exercise goals set",
        },
        "today_total": {
            "zh": "今日总计完成",
            "en": "Today's Total",
        },
        "total_completion": {
            "zh": "今日总计完成: {count} 次",
            "en": "Today's Total: {count} reps",
        },
        "weekly_progress": {
            "zh": "本周运动进度",
            "en": "Weekly Exercise Progress",
        },
        "weekly_workout_days": {
            "zh": "本周运动天数",
            "en": "Weekly Workout Days",
        },
        "monthly_progress": {
            "zh": "本月运动进度",
            "en": "Monthly Exercise Progress",
        },
        "monthly_stats": {
            "zh": "本月运动统计",
            "en": "Monthly Workout Stats",
        },
        "workout_goals": {
            "zh": "运动目标设置",
            "en": "Workout Goal Settings",
        },
        "daily_goals": {
            "zh": "每日运动目标",
            "en": "Daily Workout Goals",
        },
        "weekly_goals": {
            "zh": "每周运动目标",
            "en": "Weekly Workout Goals",
        },
        "days_per_week": {
            "zh": "每周运动天数",
            "en": "Workout Days Per Week",
        },
        "save_goals": {
            "zh": "保存目标",
            "en": "Save Goals",
        },
        "workout_stats_panel": {
            "zh": "运动统计",
            "en": "Workout Stats",
        },
        "today_progress": {
            "zh": "今日进度",
            "en": "Today",
        },
        "week_stats": {
            "zh": "本周统计",
            "en": "Week",
        },
        "month_stats": {
            "zh": "本月统计",
            "en": "Month",
        },
        "fitness_goals": {
            "zh": "目标设置",
            "en": "Goals",
        },
        
        # About dialog
        "about_title": {
            "zh": "关于护动智眸",
            "en": "About HuDongZhiMou",
        },
        "about_content": {
            "zh": "护动智眸 v1.0\n\n基于AI姿态识别的运动防伤评估系统\n\n支持多种健身动作的自动计数和姿态安全分析",
            "en": "HuDongZhiMou v1.0\n\nAI-based pose recognition sports injury prevention system\n\nSupports automatic counting and pose safety analysis for various exercises",
        },
        "about_text": {
            "zh": "护动智眸\n\n版本1.2\n\n基于PyQt5和RTMpose开发的运动防伤评估系统，支持多种运动姿态识别、安全监测和自动计数。\n\n特点：\n\n·实时姿态检测和角度计算\n\n·运动安全监测与语音提醒\n\n·健身统计~跟踪您的健身进度\n\n·实时帧显示和状态反馈\n\n·支持自定义多种运动类型\n\n·美观的用户界面和多语言支持\n\n作者：Spike Don\n\nGitHub: Good-GYM\nhttps://github.com/yo-WASSUP/Good-GYM\n\n小红书：想吃好果计\nhttps://www.xiaohongshu.com/user/profile/5fdf34b50000000001008057",
            "en": "HuDongZhiMou\n\nVersion 1.2\n\nA sports injury prevention evaluation system developed based on PyQt5 and RTMPose, supporting multiple exercise pose recognition, safety monitoring and automatic counting.\n\nFeatures:\n\n·Real-time pose detection and angle calculation\n\n·Sports safety monitoring with voice alerts\n\n·Fitness Statistics - Track your fitness progress\n\n·Real-time frame display and status feedback\n\n·Support for custom multiple exercise types\n\n·Beautiful user interface and multi-language support\n\nAuthor: Spike Don\n\nGitHub: Good-GYM\nhttps://github.com/yo-WASSUP/Good-GYM\n\nXiaohongshu: 想吃好果计\nhttps://www.xiaohongshu.com/user/profile/5fdf34b50000000001008057",
        },
        
        # Video related
        "open_video": {
            "zh": "打开视频文件",
            "en": "Open Video File",
        },
        "video_files": {
            "zh": "视频文件 (*.mp4 *.avi *.mov *.wmv *.mkv)",
            "en": "Video Files (*.mp4 *.avi *.mov *.wmv *.mkv)",
        },
        "error_opening_video": {
            "zh": "无法打开视频文件",
            "en": "Failed to open video file",
        },
        "video_loaded": {
            "zh": "视频已加载: ",
            "en": "Video loaded: ",
        },
        
        # Model related
        "model_type": {
            "zh": "模型选择:",
            "en": "Model:",
        },
        "lightweight": {
            "zh": "轻量级模型",
            "en": "Lightweight",
        },
        "balanced": {
            "zh": "平衡模型",
            "en": "Balanced",
        },
        "performance": {
            "zh": "高性能模型",
            "en": "Performance",
        },
        "changing_model": {
            "zh": "正在切换模型到",
            "en": "Changing model to",
        },
        "model_changed_to": {
            "zh": "模型已切换为",
            "en": "Model changed to",
        },
        "model_change_failed": {
            "zh": "模型切换失败",
            "en": "Model change failed",
        },
        "severe_error": {
            "zh": "发生严重错误，请重启应用",
            "en": "Severe error occurred, please restart application",
        },
        "mirror_mode": {
            "zh": "镜像模式",
            "en": "Mirror Mode",
        },
        "gpu_acceleration": {
            "zh": "GPU加速",
            "en": "GPU Acceleration",
        },
        "gpu_enabled": {
            "zh": "已启用GPU加速",
            "en": "GPU acceleration enabled",
        },
        "gpu_disabled": {
            "zh": "已切换到CPU模式",
            "en": "Switched to CPU mode",
        },
        "gpu_not_available": {
            "zh": "未检测到GPU，仅支持CPU模式",
            "en": "No GPU detected, CPU mode only",
        },
        "user_profile": {
            "zh": "用户档案",
            "en": "User Profile",
        },
        "save_profile": {
            "zh": "保存档案",
            "en": "Save Profile",
        },
        "reset_form": {
            "zh": "重置",
            "en": "Reset",
        },
        "name": {
            "zh": "姓名",
            "en": "Name",
        },
        "gender": {
            "zh": "性别",
            "en": "Gender",
        },
        "age": {
            "zh": "年龄",
            "en": "Age",
        },
        "height": {
            "zh": "身高(cm)",
            "en": "Height(cm)",
        },
        "weight": {
            "zh": "体重(kg)",
            "en": "Weight(kg)",
        },
        "injury_history": {
            "zh": "损伤史",
            "en": "Injury History",
        },
        "no_injury": {
            "zh": "无损伤史",
            "en": "No injuries",
        },
        "left_knee": {
            "zh": "左膝关节损伤",
            "en": "Left knee injury",
        },
        "right_knee": {
            "zh": "右膝关节损伤",
            "en": "Right knee injury",
        },
        "lower_back": {
            "zh": "腰椎/下背部损伤",
            "en": "Lower back injury",
        },
        "left_shoulder": {
            "zh": "左肩关节损伤",
            "en": "Left shoulder injury",
        },
        "right_shoulder": {
            "zh": "右肩关节损伤",
            "en": "Right shoulder injury",
        },
        "neck": {
            "zh": "颈椎损伤",
            "en": "Neck injury",
        },
        "profile_saved": {
            "zh": "档案已保存",
            "en": "Profile saved",
        },
        "height_weight_required": {
            "zh": "请至少填写身高和体重",
            "en": "Please enter height and weight",
        },
        "male": {
            "zh": "男",
            "en": "Male",
        },
        "female": {
            "zh": "女",
            "en": "Female",
        },

        "voice_reminder": {"zh": "语音提醒", "en": "Voice Reminder"},
        "safety_monitor": {"zh": "安全监测", "en": "Safety Monitor"},
        "safe": {"zh": "安全", "en": "Safe"},
        "warning": {"zh": "注意", "en": "Warning"},
        "danger": {"zh": "危险", "en": "Danger"},
        "action_standard": {"zh": "动作标准，继续保持！", "en": "Good form, keep it up!"},
        "switched_to_exercise": {"zh": "已切换到{exercise}", "en": "Switched to {exercise}"},
        "counter_has_been_reset": {"zh": "计数器已重置", "en": "Counter has been reset"},
        "count_increased_to": {"zh": "计数增加到 {count}", "en": "Count increased to {count}"},
        "count_decreased_to": {"zh": "计数减少到 {count}", "en": "Count decreased to {count}"},
        "recorded_count": {"zh": "已记录 {count} 次{exercise}，完成目标的{pct}%", "en": "Recorded {count} {exercise}, {pct}% of goal completed"},
        "no_count_to_record": {"zh": "没有需要记录的计数", "en": "No count to record"},
        "switched_to_camera": {"zh": "已切换到摄像头 {index}", "en": "Switched to camera {index}"},
        "portrait_mode": {"zh": "已切换到竖屏模式 (9:16)", "en": "Switched to portrait mode (9:16)"},
        "landscape_mode": {"zh": "已切换到横屏模式 (16:9)", "en": "Switched to landscape mode (16:9)"},
        "mirror_on": {"zh": "镜像模式：开启", "en": "Mirror mode: ON"},
        "mirror_off": {"zh": "镜像模式：关闭", "en": "Mirror mode: OFF"},
        "switching_device": {"zh": "正在切换设备到：{device}...", "en": "Switching device to: {device}..."},
        "device_switch_failed": {"zh": "设备切换失败：{error}", "en": "Device switching failed: {error}"},
        "rolled_back_to": {"zh": "已回滚到 {device}", "en": "Rolled back to {device}"},
        "camera_error": {"zh": "摄像头错误", "en": "Camera Error"},
        "current_video": {"zh": "当前视频：{name}", "en": "Current video: {name}"},
        "failed_open_video": {"zh": "无法打开视频文件：{error}", "en": "Failed to open video file: {error}"},
        "camera_mode_active": {"zh": "摄像头模式", "en": "Camera mode active"},
        "milestone_congrats": {"zh": "恭喜完成 {count} 次{exercise}！", "en": "Congratulations on completing {count} {exercise}!"},
        "model_ready_msg": {"zh": "{msg} - RTMPose ({mode}) on {device}", "en": "{msg} - RTMPose ({mode}) on {device}"},
        "updated_goal": {"zh": "已更新{exercise}目标为 {count}", "en": "Updated {exercise} goal to {count}"},
        "updated_weekly_goal": {"zh": "已更新每周运动目标为 {count} 天", "en": "Updated weekly fitness goal to {count} days"},
        "welcome_loading": {"zh": "欢迎使用护动智眸 - 模型加载中...", "en": "Welcome to HuDongZhiMou - Loading model..."},
        "angle_display": {"zh": "{angle}°", "en": "{angle}°"},
        "device_active_msg": {"zh": "RTMPose ({mode}) on {device}", "en": "RTMPose ({mode}) on {device}"},
        "critical_device_error": {"zh": "设备切换出现严重错误", "en": "Critical error in device switching"},
        "switching_model": {"zh": "正在切换RTMPose模式到：{mode}...", "en": "Switching RTMPose mode to: {mode}..."},
        "switched_to_model": {"zh": "已切换到 RTMPose {mode} 模式", "en": "Switched to RTMPose {mode} mode"},
        "model_switch_failed": {"zh": "RTMPose模式切换失败：{error}", "en": "RTMPose mode switching failed: {error}"},
        "rolled_back_to_model": {"zh": "已回滚到 RTMPose {mode} 模式", "en": "Rolled back to RTMPose {mode} mode"},
        "critical_model_error": {"zh": "RTMPose模式切换出现严重错误", "en": "Critical error in RTMPose mode switching"},
        "failed_load_monthly": {"zh": "加载月度数据失败：{error}", "en": "Failed to load monthly data: {error}"},
        "safety_stats_format": {"zh": "检测: {total} | 警告: {warning} | 危险: {danger}", "en": "Checks: {total} | Warnings: {warning} | Danger: {danger}"},

        "training_started": {"zh": "训练已开始", "en": "Training started"},
        "training_ended": {"zh": "训练已结束", "en": "Training ended"},
        "training_paused": {"zh": "训练已暂停", "en": "Training paused"},
        "training_resumed": {"zh": "训练继续", "en": "Training resumed"},
        "start_training": {"zh": "开始训练", "en": "Start Training"},
        "end_training": {"zh": "结束训练", "en": "End Training"},
        "pause": {"zh": "暂停", "en": "Pause"},
        "resume": {"zh": "继续", "en": "Resume"},
        "training_report": {"zh": "训练报告", "en": "Training Report"},
        "save_record": {"zh": "保存记录", "en": "Save Record"},
        "discard": {"zh": "不保存", "en": "Discard"},
        "safety_score": {"zh": "安全评分", "en": "Safety Score"},
        "risk_warning": {"zh": "风险提示", "en": "Risk Warning"},
        "training_suggestion": {"zh": "训练建议", "en": "Training Suggestion"},
        "record_saved": {"zh": "训练记录已保存", "en": "Training record saved"},
        "record_discarded": {"zh": "训练记录已丢弃", "en": "Training record discarded"},
        "suggest_rest": {"zh": "已完成 {count} 次，建议适当休息", "en": "Completed {count} reps, suggest resting"},
        "exercise_label": {"zh": "运动", "en": "Exercise"},
        "duration_label": {"zh": "时长", "en": "Duration"},
        "count_label": {"zh": "次数", "en": "Reps"},

    }
    
    @classmethod
    def get(cls, key):
        """Get translation text for current language"""
        if key in cls.translations:
            return cls.translations[key][cls.current_language]
        return key
    
    @classmethod
    def get_language(cls):
        """Get current language setting"""
        return cls.current_language
    
    @classmethod
    def set_language(cls, language):
        """Set current language"""
        if language in ["zh", "en"]:
            cls.current_language = language
            return True
        return False

    @classmethod
    def get_exercise_display_name(cls, exercise_type):
        """获取运动类型的显示名称（根据当前语言）"""
        try:
            from core.rtmpose_processor import _load_exercises_json
            exercises_data = _load_exercises_json()
            exercise_info = exercises_data.get('exercises', {}).get(exercise_type, {})
            if cls.current_language == 'zh':
                return exercise_info.get('name_zh', exercise_type)
            else:
                return exercise_info.get('name_en', exercise_type)
        except Exception:
            return exercise_type
