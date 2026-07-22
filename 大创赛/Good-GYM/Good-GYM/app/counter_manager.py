"""
计数器管理模块 - 负责运动计数和记录功能

重构后职责：
1. 切换运动类型（更新 AppState、重置计数器、同步安全检测器）
2. 重置/增加/减少计数器（更新 AppState 和 exercise_counter）
3. 确认记录（写入 workout_tracker）

不再直接操作 UI（状态栏、control_panel），通过信号通知 AppController。
"""

from PyQt5.QtCore import QObject, pyqtSignal
from core.translations import Translations as T


class CounterManager(QObject):
    """计数器管理器类"""

    # ===== 信号：通知 UI 更新 =====
    status_message = pyqtSignal(str)    # 状态栏消息
    counter_updated = pyqtSignal(int)   # 计数器数值变化（用于 UI 同步）
    stats_refresh_requested = pyqtSignal()  # 请求刷新统计面板

    def __init__(self, app_state, exercise_counter, safety_detector, workout_tracker):
        """
        Args:
            app_state: AppState 实例
            exercise_counter: ExerciseCounter 实例
            safety_detector: AngleSafetyDetector 实例
            workout_tracker: WorkoutTracker 实例
        """
        super().__init__()
        self.state = app_state
        self.exercise_counter = exercise_counter
        self.safety_detector = safety_detector
        self.workout_tracker = workout_tracker

    def change_exercise(self, exercise_type):
        """更改运动类型"""
        self.state.exercise_type = exercise_type
        self.exercise_counter.reset_counter()
        self.state.current_count = 0
        self.state.manual_count = 0
        # 同步更新安全检测器——切换运动类型时应用对应的安全阈值
        self.safety_detector.set_exercise(exercise_type)

        # 通过信号通知 UI
        self.counter_updated.emit(0)
        exercise_name = T.get_exercise_display_name(exercise_type)
        self.status_message.emit(T.get("switched_to_exercise").format(exercise=exercise_name))

    def reset_counter(self):
        """重置计数器"""
        # 设置重置标志为true以避免触发自动记录
        self.state.is_resetting = True

        # 重置计数器
        self.exercise_counter.reset_counter()
        self.state.current_count = 0
        self.state.manual_count = 0  # 同时重置手动计数

        # 重置完成后恢复标志
        self.state.is_resetting = False

        # 通知 UI 更新计数显示
        self.counter_updated.emit(0)
        self.status_message.emit(T.get("counter_has_been_reset"))

    def reset_exercise_state(self):
        """重置运动状态，包括计数器和相关变量"""
        self.reset_counter()

    def increase_counter(self, new_count):
        """手动增加计数器值"""
        self.state.current_count = new_count
        # 直接更新计数器类的内部计数值
        self.exercise_counter.counter = new_count
        # 增加手动计数
        self.state.manual_count += 1
        # 通知 UI（control_panel 已自行更新，此处仅同步状态）
        self.counter_updated.emit(new_count)
        self.status_message.emit(T.get("count_increased_to").format(count=new_count))

    def decrease_counter(self, new_count):
        """手动减少计数器值"""
        self.state.current_count = new_count
        # 直接更新计数器类的内部计数值
        self.exercise_counter.counter = new_count
        # 手动计数不会为负数
        if self.state.manual_count > 0:
            self.state.manual_count -= 1
        self.counter_updated.emit(new_count)
        self.status_message.emit(T.get("count_decreased_to").format(count=new_count))

    def confirm_record(self, exercise_type):
        """确认记录当前计数结果到历史记录"""
        # 获取当前计数值（现在记录所有计数，不仅仅是手动增加的部分）
        count = self.state.current_count

        # 记录到历史记录
        if count > 0:
            # 添加记录到运动追踪器
            completion_percentage = self.workout_tracker.add_workout_record(exercise_type, count)

            # 请求刷新统计面板（AppController 负责调用 stats_manager）
            self.stats_refresh_requested.emit()

            # 获取运动类型的显示名称
            exercise_name = T.get_exercise_display_name(exercise_type)
            self.status_message.emit(
                T.get("recorded_count").format(count=count, exercise=exercise_name, pct=completion_percentage)
            )

            # 重置计数器（也会重置manual_count）
            self.reset_counter()
        else:
            # 如果没有需要记录的计数，显示提示
            self.status_message.emit(T.get("no_count_to_record"))
