"""
PyInstaller 运行时钩子：必须在 PyQt5 之前预加载 onnxruntime。
否则 Qt5 DLL 会与 onnxruntime 的原生库产生冲突，
导致 onnxruntime_pybind11_state 初始化失败（DLL 初始化例程失败）。
"""
import os
import sys


def _preload_onnxruntime():
    # 设置 CPU 线程数限制
    os.environ.setdefault('OMP_NUM_THREADS', '2')
    os.environ.setdefault('OMP_WAIT_POLICY', 'PASSIVE')
    os.environ.setdefault('KMP_BLOCKTIME', '0')

    # 确保 onnxruntime 的 DLL 目录在 PATH 中
    onnx_dll_dir = os.path.join(sys._MEIPASS, 'onnxruntime', 'capi')
    if os.path.isdir(onnx_dll_dir):
        os.environ['PATH'] = onnx_dll_dir + ';' + os.environ.get('PATH', '')

    try:
        import onnxruntime  # noqa: F401
    except ImportError:
        pass  # 静默失败，主脚本会再次尝试并报告错误


_preload_onnxruntime()
