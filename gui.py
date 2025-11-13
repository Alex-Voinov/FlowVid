from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QFileDialog, QFrame
)


class VideoUploaderGUI(QWidget):
    def __init__(self):
        super().__init__()
        # --- Настройки окна ---
        self.setWindowTitle("FlowVid Uploader")
        self.setMinimumSize(600, 600)

        # --- Главный вертикальный layout ---
        layout = QVBoxLayout(self)

        # --- Выбор видео ---
        self.video_label = QLabel("Выберите видео (mp4)")   # Отображение выбранного файла
        self.video_button = QPushButton("Открыть видео")    # Кнопка выбора файла
        self.video_button.clicked.connect(self.select_video)  # Подключаем метод
        layout.addWidget(self.video_label)
        layout.addWidget(self.video_button)

        # --- Соцсети ---
        layout.addWidget(QLabel("Выберите платформы:"))
        self.network_buttons = {}  # Словарь для кнопок соцсетей
        network_layout = QHBoxLayout()  # Горизонтальное расположение кнопок
        for network in [
            "Rutube Reels",
            "Pinterest Reels",
            "TikTok Reels",
            "Instagram Reels",
            "VK",
            "Telegram",
            "YouTube Shorts",
            "YouTube Video"
        ]:
            btn = QPushButton(network)
            btn.setCheckable(True)          # Можно выбирать/снимать выбор
            self.network_buttons[network] = btn
            network_layout.addWidget(btn)
        layout.addLayout(network_layout)

        # --- Заголовок ---
        layout.addWidget(QLabel("Заголовок:"))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)

        # --- Описание ---
        layout.addWidget(QLabel("Описание:"))
        self.desc_input = QTextEdit()
        layout.addWidget(self.desc_input)

        # --- Теги ---
        layout.addWidget(QLabel("Теги:"))
        self.tag_layout = QVBoxLayout()  # Вертикальный layout для динамических тегов
        self.add_tag_button = QPushButton("+ Добавить тег")
        self.add_tag_button.clicked.connect(self.add_tag)  # Добавляем новый тег при клике
        self.tag_layout.addWidget(self.add_tag_button)
        layout.addLayout(self.tag_layout)

        # --- Выбор картинки (миниатюры) ---
        self.thumb_label = QLabel("Выберите изображение (миниатюру)")
        self.thumb_button = QPushButton("Открыть картинку")
        self.thumb_button.clicked.connect(self.select_image)
        layout.addWidget(self.thumb_label)
        layout.addWidget(self.thumb_button)

        self.upload_button = QPushButton("Загрузить")
        self.upload_button.clicked.connect(self.upload_video)
        layout.addWidget(self.upload_button)

    # --- Методы ---

    def select_video(self):
        """Открывает диалог выбора видео и обновляет QLabel"""
        file, _ = QFileDialog.getOpenFileName(self, "Выберите видео", "", "Video Files (*.mp4 *.mov *.avi)")
        if file:
            self.video_label.setText(f"Видео: {file}")

    def select_image(self):
        """Открывает диалог выбора картинки и обновляет QLabel"""
        file, _ = QFileDialog.getOpenFileName(self, "Выберите картинку", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.thumb_label.setText(f"Картинка: {file}")

    def add_tag(self):
        """Добавляет новый тег с QLineEdit и кнопкой удаления"""
        tag_frame = QFrame()
        tag_layout = QHBoxLayout(tag_frame)  # Горизонтальный layout для тега + крестик

        tag_input = QLineEdit()
        remove_btn = QPushButton("✖")
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_tag(tag_frame))

        tag_layout.addWidget(tag_input)
        tag_layout.addWidget(remove_btn)
        self.tag_layout.addWidget(tag_frame)

    def remove_tag(self, tag_frame):
        """Удаляет тег из layout и уничтожает виджет"""
        self.tag_layout.removeWidget(tag_frame)
        tag_frame.deleteLater()


    def upload_video(self):
        # Здесь будет логика загрузки на соцсети
        selected_networks = [net for net, btn in self.network_buttons.items() if btn.isChecked()]
        video_file = getattr(self, "video_file_path", None)
        print("Загружаем видео:", video_file, "на:", selected_networks)
