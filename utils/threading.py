from PyQt6.QtCore import QThread, pyqtSignal

class WorkerThread(QThread):
    finished = pyqtSignal(object)   # эмитирует результат (напр. dict or True)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            # ожидание: функция должна вернуть что-то информативное
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
