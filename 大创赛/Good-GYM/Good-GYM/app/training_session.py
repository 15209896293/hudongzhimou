"""
训练会话管理器 - 管理一次完整训练的生命周期
状态机：IDLE → TRAINING → PAUSED → TRAINING → ENDED → IDLE
"""

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QDateTime
from core.translations import Translations as T


class SessionState:
    IDLE = 'idle'          # 待机：未开始训练
    TRAINING = 'training'  # 训练中
    PAUSED = 'paused'      # 暂停
    ENDED = 'ended'        # 已结束，等待查看报告


class TrainingSession(QObject):
    """训练会话管理器"""

    # ===== 信号 =====
    session_started = pyqtSignal()              # 训练开始
    session_paused = pyqtSignal()               # 训练暂停
    session_resumed = pyqtSignal()              # 训练继续
    session_ended = pyqtSignal(dict)            # 训练结束，携带报告数据
    timer_updated = pyqtSignal(str)             # 计时器更新（"05:32" 格式）
    risk_score_updated = pyqtSignal(int)        # 累计风险分更新（0-100）

    def __init__(self, app_state, safety_detector=None):
        super().__init__()
        self.state = app_state
        self.safety_detector = safety_detector
        self._session_state = SessionState.IDLE
        self._start_time = 0           # 训练开始的时间戳（毫秒）
        self._paused_time = 0          # 暂停累计时长（毫秒）
        self._pause_start = 0          # 本次暂停开始时间戳
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.setInterval(1000)  # 每秒更新一次

        # 训练中的安全事件记录（用于生成报告）
        self._safety_events = []       # [{time, joint, angle, level, message}, ...]
        self._risk_score = 100         # 初始满分，每次警告-2，每次危险-5

        # 累计负荷监控
        self._rep_count = 0            # 本次训练计数

    @property
    def session_state(self):
        return self._session_state

    def start(self):
        """开始训练"""
        if self._session_state != SessionState.IDLE:
            return

        self._session_state = SessionState.TRAINING
        self._start_time = QDateTime.currentMSecsSinceEpoch()
        self._paused_time = 0
        self._safety_events = []
        self._risk_score = 100
        self._rep_count = 0
        self.state.start_time = self._start_time

        self._timer.start()
        self.session_started.emit()
        self.timer_updated.emit("00:00")
        self.risk_score_updated.emit(100)

    def pause(self):
        """暂停训练"""
        if self._session_state != SessionState.TRAINING:
            return

        self._session_state = SessionState.PAUSED
        self._pause_start = QDateTime.currentMSecsSinceEpoch()
        self._timer.stop()
        self.session_paused.emit()

    def resume(self):
        """继续训练"""
        if self._session_state != SessionState.PAUSED:
            return

        self._paused_time += QDateTime.currentMSecsSinceEpoch() - self._pause_start
        self._session_state = SessionState.TRAINING
        self._timer.start()
        self.session_resumed.emit()

    def end(self):
        """结束训练，生成报告"""
        if self._session_state not in (SessionState.TRAINING, SessionState.PAUSED):
            return

        self._timer.stop()
        self._session_state = SessionState.ENDED

        # 如果正在暂停，计算暂停时间
        if self._pause_start > 0:
            self._paused_time += QDateTime.currentMSecsSinceEpoch() - self._pause_start
            self._pause_start = 0

        duration_ms = QDateTime.currentMSecsSinceEpoch() - self._start_time - self._paused_time
        duration_sec = int(duration_ms / 1000)

        # 生成报告数据
        report = self._generate_report(duration_sec)
        self.session_ended.emit(report)
        return report

    def reset(self):
        """重置到待机状态（报告处理完后调用）"""
        self._session_state = SessionState.IDLE
        self._start_time = 0
        self._paused_time = 0
        self._safety_events = []
        self._risk_score = 100
        self._rep_count = 0

    def record_safety_event(self, safety_result):
        """记录安全事件（FramePipeline 每次安全检测后调用）"""
        if self._session_state != SessionState.TRAINING:
            return

        level = safety_result.get('level')
        if level is None:
            return

        level_val = level.value if hasattr(level, 'value') else level

        if level_val > 0:
            for msg in safety_result.get('messages', []):
                self._safety_events.append({
                    'time': QDateTime.currentMSecsSinceEpoch() - self._start_time,
                    'message': msg,
                    'level': level_val
                })

            if level_val == 2:
                self._risk_score = max(0, self._risk_score - 5)
            else:
                self._risk_score = max(0, self._risk_score - 2)

            self.risk_score_updated.emit(self._risk_score)

    def apply_user_profile(self, profile_data):
        """将用户档案数据同步到训练会话，供个性化风险评估使用"""
        if not profile_data:
            return
        self._user_profile = profile_data

        # 如果安全检测器存在，也同步过去（与 AngleSafetyDetector.apply_user_profile 对齐）
        if self.safety_detector:
            self.safety_detector.set_user_profile(profile_data)

    def record_rep(self):
        """记录一次计数（FramePipeline 计数变化时调用）"""
        if self._session_state == SessionState.TRAINING:
            self._rep_count += 1

    def check_fatigue(self):
        """检查累计负荷，返回提醒消息或 None"""
        if self._session_state != SessionState.TRAINING:
            return None

        if self._rep_count > 0 and self._rep_count % 50 == 0:
            return f"已完成 {self._rep_count} 次，建议适当休息"
        return None

    def _on_timer_tick(self):
        """每秒更新计时器"""
        if self._session_state != SessionState.TRAINING:
            return

        elapsed = QDateTime.currentMSecsSinceEpoch() - self._start_time - self._paused_time
        seconds = int(elapsed / 1000)
        mins = seconds // 60
        secs = seconds % 60
        self.timer_updated.emit(f"{mins:02d}:{secs:02d}")

    def _generate_report(self, duration_sec):
        """生成训练报告"""
        joint_risks = {}
        for event in self._safety_events:
            msg = event.get('message', '')
            for joint_name in ['膝盖', '肘部', '肩部', '背部', '髋部', '颈部', '下背部', '脊柱']:
                if joint_name in msg:
                    if joint_name not in joint_risks:
                        joint_risks[joint_name] = {'count': 0, 'max_level': 0}
                    joint_risks[joint_name]['count'] += 1
                    joint_risks[joint_name]['max_level'] = max(
                        joint_risks[joint_name]['max_level'],
                        event.get('level', 0)
                    )

        risk_items = []
        for joint, info in joint_risks.items():
            level_text = "危险" if info['max_level'] >= 2 else "注意"
            risk_items.append({
                'joint': joint,
                'count': info['count'],
                'level': info['max_level'],
                'text': f"{joint}角度异常 {info['count']} 次（{level_text}）"
            })

        risk_items.sort(key=lambda x: x['count'], reverse=True)

        if self._risk_score >= 90:
            overall = "动作标准，继续保持"
            suggestion = "你的动作整体规范，注意保持当前的运动习惯。"
        elif self._risk_score >= 70:
            overall = "存在少量风险，需注意调整"
            suggestion = "部分动作角度存在偏差，建议对照提示进行调整。"
        elif self._risk_score >= 50:
            overall = "风险较高，建议降低强度"
            suggestion = "多处关节角度异常，建议降低运动强度，重点纠正动作模式。"
        else:
            overall = "风险很高，建议停止训练"
            suggestion = "本次训练风险较高，建议休息并咨询专业教练指导。"

        return {
            'exercise_type': self.state.exercise_type,
            'duration_sec': duration_sec,
            'rep_count': self._rep_count,
            'risk_score': self._risk_score,
            'warning_count': len([e for e in self._safety_events if e['level'] == 1]),
            'danger_count': len([e for e in self._safety_events if e['level'] == 2]),
            'risk_items': risk_items,
            'overall': overall,
            'suggestion': suggestion,
            'timestamp': QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')
        }