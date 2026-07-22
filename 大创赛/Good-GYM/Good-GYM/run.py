import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _preload_onnxruntime():
    """Python 3.14 兼容性修复：必须在 PyQt5 之前加载 onnxruntime。

    PyQt5 加载的 Qt5 DLL 会与 onnxruntime 的原生库产生 DLL 搜索路径冲突，
    导致 onnxruntime_pybind11_state 初始化失败。提前加载可避免此问题。
    """
    # 限制 ONNX Runtime 线程数，防止吃满所有 CPU 核心导致系统卡顿
    os.environ.setdefault('OMP_NUM_THREADS', '2')
    os.environ.setdefault('OMP_WAIT_POLICY', 'PASSIVE')
    os.environ.setdefault('KMP_BLOCKTIME', '0')

    try:
        import onnxruntime  # noqa: F401
    except ImportError as e:
        print(f"WARNING: Failed to preload onnxruntime: {e}")
        print("Skeleton detection may not work. Try: pip install onnxruntime")


def _setup_exception_hook():
    """安装全局异常钩子，捕获 PyQt5 事件循环中未处理的异常（防止静默闪退）"""
    import traceback

    def _qt_exception_hook(exc_type, exc_value, exc_tb):
        """Qt 事件循环中的异常拦截"""
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(f"[FATAL] Unhandled exception in Qt event loop:\n{tb_str}", file=sys.stderr)
        # 写入 crash log 文件便于排查
        try:
            log_dir = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(log_dir, 'crash.log'), 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*60}\n{tb_str}")
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _qt_exception_hook


def main():
    try:
        # 必须在 PyQt5 之前导入 onnxruntime，避免 DLL 冲突
        _preload_onnxruntime()

        from PyQt5.QtWidgets import QApplication
        from app.main_window import WorkoutTrackerApp

        app = QApplication(sys.argv)
        app.setApplicationName("护动智眸")
        app.setApplicationVersion("1.2.0")

        # 安装异常钩子（必须在 QApplication 创建之后）
        _setup_exception_hook()

        # 设置应用图标
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, 'assets', 'Logo.ico')
        if os.path.exists(logo_path):
            from PyQt5.QtGui import QIcon
            app.setWindowIcon(QIcon(logo_path))

        window = WorkoutTrackerApp()
        window.show()

        sys.exit(app.exec_())

    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed correctly")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"Startup failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 