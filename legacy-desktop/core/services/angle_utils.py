"""
角度计算工具 - 统一的三点夹角计算逻辑
"""
import numpy as np


class AngleUtils:
    """统一封装所有角度计算逻辑，替代分散在各模块中的重复实现"""

    @staticmethod
    def calculate_angle(point1, point2, point3):
        """
        计算三个关键点之间的夹角（以 point2 为顶点）
        
        Args:
            point1: (x, y) 第一个点
            point2: (x, y) 顶点
            point3: (x, y) 第二个点
            
        Returns:
            float: 角度值（度），计算失败返回 None
        """
        if point1 is None or point2 is None or point3 is None:
            return None

        # 过滤无效点（置信度为0）
        if (point1[0] == 0 and point1[1] == 0) or \
           (point2[0] == 0 and point2[1] == 0) or \
           (point3[0] == 0 and point3[1] == 0):
            return None

        v1 = np.array([point1[0] - point2[0], point1[1] - point2[1]])
        v2 = np.array([point3[0] - point2[0], point3[1] - point2[1]])

        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if n1 == 0 or n2 == 0:
            return None

        cos = np.dot(v1, v2) / (n1 * n2)
        cos = np.clip(cos, -1.0, 1.0)

        return float(np.arccos(cos) * (180.0 / np.pi))

    @staticmethod
    def calculate_3d_angle(point1, point2, point3):
        """
        计算三个3D关键点之间的夹角（使用z坐标）
        
        Args:
            point1: (x, y, z) 第一个点
            point2: (x, y, z) 顶点
            point3: (x, y, z) 第二个点
            
        Returns:
            float: 角度值（度），计算失败返回 None
        """
        if point1 is None or point2 is None or point3 is None:
            return None

        v1 = np.array([point1[0] - point2[0], point1[1] - point2[1], point1[2] - point2[2]])
        v2 = np.array([point3[0] - point2[0], point3[1] - point2[1], point3[2] - point2[2]])

        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if n1 == 0 or n2 == 0:
            return None

        cos = np.dot(v1, v2) / (n1 * n2)
        cos = np.clip(cos, -1.0, 1.0)

        return float(np.arccos(cos) * (180.0 / np.pi))
