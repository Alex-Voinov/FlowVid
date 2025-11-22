from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QFileDialog, QFrame, QMessageBox,
    QLayout
)
from PyQt6.QtGui import QPixmap

from PyQt6.QtCore import Qt, QPoint, QRect, QSize, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from utils.threading import WorkerThread
from core.uploader_manager import UploaderManager
from config.networks import NETWORKS
import os


# ============================================================
#  FLOW LAYOUT (теги в несколько строк)
# ============================================================
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=6):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self._spacing = spacing
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), test_only=True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return QSize(480, 200)

    def minimumSize(self):
        return QSize(100, 50)

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0

        for item in self._items:
            wid = item.widget()
            space_x = self._spacing
            space_y = self._spacing
            next_x = x + wid.sizeHint().width() + space_x

            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y += line_height + space_y
                next_x = x + wid.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(
                    QRect(QPoint(x, y), wid.sizeHint())
                )

            x = next_x
            line_height = max(line_height, wid.sizeHint().height())

        return y + line_height - rect.y()


# ============================================================
#  MAIN GUI
# ============================================================
class VideoUploaderGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlowVid Uploader")
        self.setWindowState(Qt.WindowState.WindowMaximized)

        layout = QVBoxLayout(self)

        # ------------------- SELECT VIDEO --------------------
        self.video_label = QLabel("Видео не выбрано")
        self.video_btn = QPushButton("Выбрать видео")
        self.video_btn.clicked.connect(self.select_video)

        layout.addWidget(self.video_label)
        layout.addWidget(self.video_btn)

        # PREVIEW VIDEO
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)

        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(200)
        self.player.setVideoOutput(self.video_widget)

        layout.addWidget(self.video_widget)

        # ------------------- NETWORKS -------------------------
        layout.addWidget(QLabel("Платформы:"))
        net_layout = QHBoxLayout()
        self.network_buttons = {}

        for net in NETWORKS:
            if not net.enabled:
                continue
            btn = QPushButton(net.title)
            btn.setCheckable(True)
            self.network_buttons[net.key] = btn
            net_layout.addWidget(btn)

        layout.addLayout(net_layout)

        # ------------------- TITLE -----------------------------
        layout.addWidget(QLabel("Заголовок:"))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)

        # ------------------- DESCRIPTION -----------------------
        layout.addWidget(QLabel("Описание:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        layout.addWidget(self.desc_input)

        # ------------------- TAGS -------------------------------
        layout.addWidget(QLabel("Теги:"))

        self.tags_container = QWidget()
        self.tags_layout = FlowLayout(self.tags_container)

        self.add_tag_btn = QPushButton("+ тег")
        self.add_tag_btn.clicked.connect(self.add_tag)
        self.tags_layout.addWidget(self.add_tag_btn)

        layout.addWidget(self.tags_container)

        # ------------------- THUMBNAIL --------------------------
        self.thumb_label = QLabel("Миниатюра не выбрана")
        self.thumb_btn = QPushButton("Выбрать миниатюру")
        self.thumb_btn.clicked.connect(self.select_image)

        layout.addWidget(self.thumb_label)
        layout.addWidget(self.thumb_btn)

        # PREVIEW THUMB
        self.thumb_preview = QLabel()
        self.thumb_preview.setFixedHeight(180)
        self.thumb_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumb_preview)

        # ------------------- UPLOAD -----------------------------
        self.upload_btn = QPushButton("Загрузить")
        self.upload_btn.clicked.connect(self.upload_video)
        layout.addWidget(self.upload_btn)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status)

        self._worker = None
        self.video_file_path = None
        self.thumbnail_path = None

    # ============================================================
    #  FILE PICKERS
    # ============================================================
    def select_video(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Выберите видео", "", "Video (*.mp4 *.mov *.avi)"
        )
        if not file:
            return

        self.video_file_path = file
        self.video_label.setText(f"Видео: {os.path.basename(file)}")

        self.player.setSource(QUrl.fromLocalFile(file))
        self.player.play()
        self.player.pause()   # показываем первый кадр

    def select_image(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Выберите картинку", "", "Images (*.png *.jpg *.jpeg)"
        )
        if not file:
            return

        self.thumbnail_path = file
        self.thumb_label.setText(f"Картинка: {os.path.basename(file)}")

        pix = QPixmap(file).scaledToHeight(180, Qt.TransformationMode.SmoothTransformation)
        self.thumb_preview.setPixmap(pix)

    # ============================================================
    #  TAGS
    # ============================================================
    def add_tag(self):
        tag_frame = QFrame()
        tag_frame.setObjectName("tagFrame")

        tag_layout = QHBoxLayout(tag_frame)
        tag_layout.setContentsMargins(4, 4, 4, 4)

        tag_input = QLineEdit()
        tag_input.setFixedHeight(24)
        tag_input.setMaximumWidth(150)
        tag_input.setObjectName("tagLabel")

        rm = QPushButton("×")
        rm.setFixedWidth(20)
        rm.setFixedHeight(24)
        rm.setObjectName("tagRemove")
        rm.clicked.connect(lambda: self.remove_tag(tag_frame))

        tag_layout.addWidget(tag_input)
        tag_layout.addWidget(rm)

        self.tags_layout.addWidget(tag_frame)

    def remove_tag(self, frame):
        frame.setParent(None)

    def gather_tags(self):
        tags = []
        for i in range(self.tags_layout.count()):
            item = self.tags_layout.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if isinstance(w, QFrame):
                input_field = w.findChild(QLineEdit)
                if input_field:
                    text = input_field.text().strip()
                    if text:
                        tags.append(text)
        return tags

    # ============================================================
    #  UPLOAD
    # ============================================================
    def upload_video(self):
        if not self.video_file_path:
            QMessageBox.warning(self, "Ошибка", "Выберите видео")
            return

        networks = [
            key for key, btn in self.network_buttons.items()
            if btn.isChecked()
        ]

        if not networks:
            QMessageBox.warning(self, "Ошибка", "Выберите платформы")
            return

        title = self.title_input.text()
        desc = self.desc_input.toPlainText()
        tags = self.gather_tags()
        thumb = self.thumbnail_path

        self.upload_btn.setEnabled(False)
        self.status.setText("Загрузка...")

        self._worker = WorkerThread(
            UploaderManager.upload,
            self.video_file_path, networks, title, desc, tags, thumb
        )
        self._worker.finished.connect(self.on_finish)
        self._worker.error.connect(self.on_error)
        self._worker.start()

    def on_finish(self, result):
        self.upload_btn.setEnabled(True)
        self.status.setText("")
        if isinstance(result, dict) and result.get("errors"):
            QMessageBox.critical(self, "Ошибка", f"Ошибки:\n{result['errors']}")
            return
        QMessageBox.information(self, "Успех", "Видео загружено!")

    def on_error(self, err):
        self.upload_btn.setEnabled(True)
        self.status.setText("")
        QMessageBox.critical(self, "Ошибка", err)
