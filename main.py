from PyQt6.QtWidgets import QApplication
from gui import VideoUploaderGUI
import sys
from utils.paths import ensure_dirs
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()
    ensure_dirs()
    app = QApplication(sys.argv)
    # optional: load styles.qss if exists
    try:
        with open("styles.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass
    window = VideoUploaderGUI()
    window.show()
    app.exec()
