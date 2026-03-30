import cv2
from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class AnalysisSignals(QObject):
    """Signals for the analysis worker. Must be QObject (not on QRunnable directly)."""
    image_done = Signal(str, object, int, object)   # filename, annotated_rgb_ndarray, cell_count, centroids_list
    progress = Signal(int, int)             # current_index (1-based), total
    error = Signal(str, str)                # filename, error_message
    finished = Signal()


class AnalysisWorker(QRunnable):
    """Runs process_image() on a list of file paths in a background thread."""

    def __init__(self, images_dict: dict, params: dict):
        """
        Args:
            images_dict: {filename: {"original_bgr": ndarray, ...}} from MainWindow._images
            params: dict from ParamPanel.get_params()
        """
        super().__init__()
        self.images_dict = images_dict
        self.params = params
        self.signals = AnalysisSignals()

    @Slot()
    def run(self):
        from analysis_core import process_image  # NOT from main — avoids Gradio side effects
        filenames = list(self.images_dict.keys())
        for i, filename in enumerate(filenames):
            try:
                img_bgr = self.images_dict[filename]["original_bgr"]
                ann_bgr, count, centroids = process_image(img_bgr, **self.params)
                ann_rgb = cv2.cvtColor(ann_bgr, cv2.COLOR_BGR2RGB)
                self.signals.image_done.emit(filename, ann_rgb, count, centroids)
            except Exception as e:
                self.signals.error.emit(filename, str(e))
            self.signals.progress.emit(i + 1, len(filenames))
        self.signals.finished.emit()
