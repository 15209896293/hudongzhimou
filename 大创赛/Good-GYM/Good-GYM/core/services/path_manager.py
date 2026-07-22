"""
路径管理 - 统一处理打包环境与开发环境的路径差异
"""
import os
import sys


class PathManager:
    """统一管理所有文件路径，封装打包环境(sys.frozen)与开发环境的差异"""

    @staticmethod
    def is_frozen():
        """判断是否运行在 PyInstaller 打包环境中"""
        return getattr(sys, 'frozen', False)

    @staticmethod
    def get_executable_dir():
        """获取可执行文件所在目录（打包环境）或项目根目录（开发环境）"""
        if PathManager.is_frozen():
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    @staticmethod
    def get_project_root():
        """获取项目根目录"""
        if PathManager.is_frozen():
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    @staticmethod
    def get_models_dir():
        """获取模型文件目录"""
        if PathManager.is_frozen():
            base_path = sys._MEIPASS
            models_dir = os.path.join(base_path, 'models')
        else:
            models_dir = os.path.join(PathManager.get_project_root(), 'models')
        return models_dir

    @staticmethod
    def get_data_dir():
        """获取数据文件目录
        打包环境优先使用外部 data 目录，不存在则使用内部目录
        """
        if PathManager.is_frozen():
            exe_dir = PathManager.get_executable_dir()
            external_dir = os.path.join(exe_dir, 'data')
            if os.path.exists(external_dir):
                return external_dir
            return os.path.join(sys._MEIPASS, 'data')
        return os.path.join(PathManager.get_project_root(), 'data')

    @staticmethod
    def get_exercises_file_path():
        """获取 exercises.json 文件路径"""
        return os.path.join(PathManager.get_data_dir(), 'exercises.json')

    @staticmethod
    def get_workout_history_file_path():
        """获取 workout_history.json 文件路径"""
        return os.path.join(PathManager.get_data_dir(), 'workout_history.json')

    @staticmethod
    def get_workout_goals_file_path():
        """获取 workout_goals.json 文件路径"""
        return os.path.join(PathManager.get_data_dir(), 'workout_goals.json')

    @staticmethod
    def get_model_path(filename):
        """获取指定模型文件的完整路径"""
        return os.path.join(PathManager.get_models_dir(), filename)
