from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread

class ExportController:
    @staticmethod
    def ensure_image_path(path: str) -> Path:
        image_path = Path(path)
        if image_path.suffix.lower() != ".png":
            image_path = image_path.with_suffix(".png")
        return image_path

    @staticmethod
    def ensure_csv_path(path: str) -> Path:
        csv_path = Path(path)
        if csv_path.suffix.lower() != ".csv":
            csv_path = csv_path.with_suffix(".csv")
        return csv_path

    @staticmethod
    def create_export_worker(
        parent,
        *,
        snapshot_state: dict,
        target_path: str,
        worker_cls,
        on_finished,
        on_thread_closed,
    ) -> tuple[QThread, object]:
        thread = QThread(parent)
        worker = worker_cls(snapshot_state, target_path)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(on_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(on_thread_closed)
        return (thread, worker)
