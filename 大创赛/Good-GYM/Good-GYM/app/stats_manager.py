"""
统计管理模块 - 负责运动统计和面板管理

重构后职责：
1. 创建统计面板（WorkoutStatsPanel）
2. 更新今日/本周/本月统计
3. 更新运动目标

不再持有 main_window，通过 AppState 和 workout_tracker 操作数据。
状态栏消息通过信号通知 AppController。
"""

from PyQt5.QtCore import QObject, pyqtSignal
from ui.workout_stats_panel import WorkoutStatsPanel
from core.translations import Translations as T


class StatsManager(QObject):
    """统计管理器类"""

    # ===== 信号 =====
    status_message = pyqtSignal(str)  # 状态栏消息

    def __init__(self, app_state, workout_tracker):
        """
        Args:
            app_state: AppState 实例
            workout_tracker: WorkoutTracker 实例
        """
        super().__init__()
        self.state = app_state
        self.workout_tracker = workout_tracker
        self.stats_panel = None  # init_workout_stats() 后创建

    def init_workout_stats(self):
        """初始化运动统计面板（创建面板实例，设置目标）"""
        # 创建运动统计面板
        self.stats_panel = WorkoutStatsPanel()
        self.stats_panel.setVisible(False)  # 初始不可见

        # 设置目标
        self.stats_panel.set_goals(self.workout_tracker.get_goals())
        # 注意：stats_panel 信号连接由 main_window.connect_signals() 负责，
        # 目标是 AppController（不再连接到 main_window 中转方法）

    def update_today_stats(self):
        """更新今日运动统计"""
        if self.stats_panel is None:
            return
        # 获取原始数据
        today_stats_raw = self.workout_tracker.get_today_stats()
        goals = self.workout_tracker.get_goals()

        # 转换数据结构为UI组件期望的格式
        today_stats = {"exercises": {}}
        for exercise, count in today_stats_raw.items():
            today_stats["exercises"][exercise] = {"count": count}

        # 更新UI
        self.stats_panel.update_today_stats(today_stats, goals)

    def update_stats_overview(self):
        """更新所有统计概览"""
        if self.stats_panel is None:
            return
        # 获取数据
        weekly_stats = self.workout_tracker.get_weekly_stats()
        monthly_stats = self.workout_tracker.get_monthly_stats()
        goals = self.workout_tracker.get_goals()

        # 更新到UI
        self.stats_panel.update_week_stats(weekly_stats, goals)
        self.stats_panel.update_month_stats(monthly_stats, goals)

    def load_month_stats(self, year, month):
        """加载指定月份的统计数据

        Args:
            year: 年份
            month: 月份
        """
        if self.stats_panel is None:
            return
        try:
            monthly_stats = self.workout_tracker.get_monthly_stats(year, month)
            goals = self.workout_tracker.get_goals()
            self.stats_panel.update_month_stats(monthly_stats, goals)
        except Exception as e:
            print(f"Error loading monthly data: {e}")
            self.status_message.emit(T.get("failed_load_monthly").format(error=str(e)))

    def update_goal(self, exercise_type, count):
        """更新运动目标"""
        self.workout_tracker.update_goal(exercise_type, count)
        self.update_today_stats()
        exercise_name = T.get_exercise_display_name(exercise_type)
        self.status_message.emit(T.get("updated_goal").format(exercise=exercise_name, count=count))

    def update_weekly_goal(self, count):
        """更新周目标"""
        self.workout_tracker.update_weekly_goal(count)
        self.update_stats_overview()
        self.status_message.emit(T.get("updated_weekly_goal").format(count=count))
