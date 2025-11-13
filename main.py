from PyQt6.QtWidgets import QApplication
from gui import VideoUploaderGUI

if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet("""
    /* Фоновый цвет для всего окна */
    QWidget {
        background-color: #282828;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
    }

    /* Кнопки */
    QPushButton {
        background-color: #303030;                 
        padding: 10px;
        outline: 1px solid #404040;
    }
""")
    window = VideoUploaderGUI()
    window.show()
    app.exec()
