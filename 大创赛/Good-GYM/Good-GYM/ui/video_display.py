from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap


class VideoDisplay(QWidget):
    """Video display component with overlay badges"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 20px;
            border: none;
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: none;")
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.image_label, 0, Qt.AlignCenter)

        self._last_widget_size = (0, 0)

        self.is_portrait = True
        self.aspect_ratio = 9 / 16
        self.set_orientation(self.is_portrait)

        self._setup_overlays()

    def _setup_overlays(self):
        self.overlay_container = QWidget(self)
        self.overlay_container.setStyleSheet("background-color: transparent;")
        self.overlay_container.setFixedHeight(30)

        overlay_layout = QHBoxLayout(self.overlay_container)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(8)

        self.rtmpose_label = QLabel("RTMPose · 实时检测")
        self.rtmpose_label.setStyleSheet("""
            background: rgba(52,199,89,0.9);
            color: #FFFFFF;
            font-size: 10px;
            padding: 4px 10px;
            border-radius: 100px;
        """)
        overlay_layout.addWidget(self.rtmpose_label)

        self.fps_label = QLabel("30 FPS")
        self.fps_label.setStyleSheet("""
            background: rgba(255,255,255,0.8);
            color: #1D1D1F;
            font-size: 10px;
            padding: 4px 10px;
            border-radius: 100px;
        """)
        overlay_layout.addWidget(self.fps_label)

        self.safety_bar = QWidget(self)
        self.safety_bar.setFixedHeight(4)
        self.safety_bar.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #34C759,
                stop:0.5 #FF9F0A,
                stop:1 #FF453A
            );
        """)

        self.score_badge = QWidget(self)
        self.score_badge.setFixedSize(72, 72)
        self.score_badge.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.9);
            border: 2px solid #34C759;
            border-radius: 36px;
        """)

        self.score_label = QLabel("85", self.score_badge)
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 600;
            color: #34C759;
        """)
        self.score_label.move(0, 14)
        self.score_label.resize(72, 32)

        self.score_text = QLabel("动作评分", self.score_badge)
        self.score_text.setAlignment(Qt.AlignCenter)
        self.score_text.setStyleSheet("""
            font-size: 9px;
            color: #86868B;
        """)
        self.score_text.move(0, 48)
        self.score_text.resize(72, 16)

    def update_image(self, frame):
        try:
            frame = frame.copy()
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
            self._last_frame = frame

            cur_size = (self.width(), self.height())
            if cur_size != self._last_widget_size and cur_size[0] > 0:
                self._last_widget_size = cur_size
                self.update_aspect_ratio(w / h)
                self.adjust_size()

            label_width, label_height = self.width(), self.height()

            if label_width > 0 and label_height > 0:
                qt_img = qt_img.scaled(
                    label_width, label_height,
                    Qt.KeepAspectRatio,
                    Qt.FastTransformation
                )

            self.image_label.setPixmap(QPixmap.fromImage(qt_img))
            self.image_label.setScaledContents(False)

        except Exception as e:
            print(f"Error updating image: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_size()
        margins = self.layout.contentsMargins()
        self.overlay_container.move(12 + margins.left(), 12 + margins.top())
        self.overlay_container.raise_()

        self.safety_bar.move(0, self.height() - 4)
        self.safety_bar.setFixedWidth(self.width())
        self.safety_bar.raise_()

        self.score_badge.move(self.width() - 84, 12)
        self.score_badge.raise_()

    def adjust_size(self):
        width = self.width()
        height = self.height()

        target_height = width / self.aspect_ratio
        target_width = height * self.aspect_ratio

        if target_height <= height:
            new_size = (width, int(target_height))
            margin_h = 0
            margin_v = (height - int(target_height)) // 2
        else:
            new_size = (int(target_width), height)
            margin_h = (width - int(target_width)) // 2
            margin_v = 0

        self.layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)

    def update_aspect_ratio(self, frame_aspect_ratio):
        is_vertical = frame_aspect_ratio < 1
        self.aspect_ratio = frame_aspect_ratio
        self.is_portrait = is_vertical

    def set_orientation(self, portrait_mode=True):
        self.is_portrait = portrait_mode

        if portrait_mode:
            self.aspect_ratio = 9/16
            self.image_label.setMinimumSize(360, 640)
        else:
            self.aspect_ratio = 16/9
            self.image_label.setMinimumSize(640, 360)

        self.adjust_size()

    def update_fps(self, fps):
        self.fps_label.setText(f"{int(fps)} FPS")

    def update_score(self, score):
        self.score_label.setText(str(score))