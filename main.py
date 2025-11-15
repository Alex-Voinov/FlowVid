from PyQt6.QtWidgets import QApplication
from gui import VideoUploaderGUI

if __name__ == "__main__":
    app = QApplication([])
    with open("styles.qss", "r") as f:
        app.setStyleSheet(f.read())
    window = VideoUploaderGUI()
    window.show()
    app.exec()
