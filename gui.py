from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QFileDialog, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from utils.threading import WorkerThread
from core.uploader_manager import UploaderManager
from utils.logger import log
import os
from config.networks import NETWORKS


class VideoUploaderGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlowVid Uploader")
        self.setMinimumSize(700, 600)

        layout = QVBoxLayout(self)

        # video
        self.video_label = QLabel("Выберите видео (mp4)")
        self.video_button = QPushButton("Открыть видео")
        self.video_button.clicked.connect(self.select_video)
        layout.addWidget(self.video_label)
        layout.addWidget(self.video_button)

        # networks
        layout.addWidget(QLabel("Выберите платформы:"))
        self.network_buttons = {}
        network_layout = QHBoxLayout()
        for net in NETWORKS:
            if not net.enabled:
                continue  # сеть выключена в конфиге — не показываем кнопку

            btn = QPushButton(net.title)
            btn.setCheckable(True)

            self.network_buttons[net.key] = btn
            network_layout.addWidget(btn)

        layout.addLayout(network_layout)

        # title
        layout.addWidget(QLabel("Заголовок:"))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)

        # description
        layout.addWidget(QLabel("Описание:"))
        self.desc_input = QTextEdit()
        layout.addWidget(self.desc_input)

        # tags
        layout.addWidget(QLabel("Теги:"))
        self.tag_layout = QVBoxLayout()
        self.add_tag_button = QPushButton("+ Добавить тег")
        self.add_tag_button.clicked.connect(self.add_tag)
        self.tag_layout.addWidget(self.add_tag_button)
        layout.addLayout(self.tag_layout)

        # thumbnail
        self.thumb_label = QLabel("Выберите изображение (миниатюра)")
        self.thumb_button = QPushButton("Открыть картинку")
        self.thumb_button.clicked.connect(self.select_image)
        layout.addWidget(self.thumb_label)
        layout.addWidget(self.thumb_button)

        # upload
        self.upload_button = QPushButton("Загрузить")
        self.upload_button.clicked.connect(self.upload_video)
        layout.addWidget(self.upload_button)

        # status label
        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status)

        # Thread placeholder
        self._worker = None

    def select_video(self):
        file, _ = QFileDialog.getOpenFileName(self, "Выберите видео", "", "Video Files (*.mp4 *.mov *.avi)")
        if file:
            self.video_label.setText(f"Видео: {file}")
            self.video_file_path = file

    def select_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Выберите картинку", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.thumb_label.setText(f"Картинка: {file}")
            self.thumbnail_path = file

    def add_tag(self):
        tag_frame = QFrame()
        tag_layout = QHBoxLayout(tag_frame)

        tag_input = QLineEdit()
        remove_btn = QPushButton("✖")
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_tag(tag_frame))

        tag_layout.addWidget(tag_input)
        tag_layout.addWidget(remove_btn)
        self.tag_layout.addWidget(tag_frame)

    def remove_tag(self, tag_frame):
        self.tag_layout.removeWidget(tag_frame)
        tag_frame.deleteLater()

    def _gather_tags(self):
        tags = []
        # индекс 0 — кнопка "+ Добавить тег"
        for i in range(1, self.tag_layout.count()):
            widget = self.tag_layout.itemAt(i).widget()
            if widget:
                line = widget.layout().itemAt(0).widget()
                if isinstance(line, QLineEdit):
                    text = line.text().strip()
                    if text:
                        tags.append(text)
        return tags

    def _on_upload_finished(self, result):
        self.upload_button.setEnabled(True)
        self.status.setText("")
        if isinstance(result, dict) and result.get("errors"):
            QMessageBox.critical(self, "Ошибка", f"Ошибки при загрузке:\n{result['errors']}")
            log(f"Upload errors: {result['errors']}")
        else:
            QMessageBox.information(self, "Готово", "Загрузка завершена.")
            log("Upload finished successfully.")

    def _on_upload_error(self, error_str):
        self.upload_button.setEnabled(True)
        self.status.setText("")
        QMessageBox.critical(self, "Ошибка выполнения", error_str)
        log(f"Upload thread error: {error_str}", level="error")

    def upload_video(self):
        selected_networks = [net for net, btn in self.network_buttons.items() if btn.isChecked()]
        video_file = getattr(self, "video_file_path", None)
        title = self.title_input.text()
        description = self.desc_input.toPlainText()
        tags = self._gather_tags()
        thumbnail = getattr(self, "thumbnail_path", None)

        if not video_file or not os.path.exists(video_file):
            QMessageBox.warning(self, "Нет файла", "Пожалуйста, выберите видео для загрузки.")
            return

        if not selected_networks:
            QMessageBox.warning(self, "Ничего не выбрано", "Выберите хотя бы одну платформу.")
            return

        # disable UI while running
        self.upload_button.setEnabled(False)
        self.status.setText("Запущена задача загрузки...")

        # запускаем в фоне
        self._worker = WorkerThread(
            UploaderManager.upload,
            video_file, selected_networks, title, description, tags, thumbnail
        )
        self._worker.finished.connect(self._on_upload_finished)
        self._worker.error.connect(self._on_upload_error)
        self._worker.start()
