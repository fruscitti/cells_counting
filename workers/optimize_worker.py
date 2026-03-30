from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class OptimizeSignals(QObject):
    result = Signal(int, int, int, int)  # brightness, min_area, blur, count
    error = Signal(str)
    finished = Signal()


class OptimizeWorker(QRunnable):
    """Runs optimize_parameters() in background thread."""

    def __init__(self, img_bgr, use_cleaning: bool):
        super().__init__()
        self.img_bgr = img_bgr
        self.use_cleaning = use_cleaning
        self.signals = OptimizeSignals()

    @Slot()
    def run(self):
        from analysis_core import optimize_parameters  # NOT from main
        try:
            b, a, bl, count = optimize_parameters(self.img_bgr, self.use_cleaning)
            self.signals.result.emit(b, a, bl, count)
        except Exception as e:
            self.signals.error.emit(str(e))
        self.signals.finished.emit()
