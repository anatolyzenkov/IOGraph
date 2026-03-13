from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

from PyQt6.QtCore import QThread


@dataclass(frozen=True)
class ExportUiState:
    can_save_image: bool


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
    def ui_state(export_in_progress: bool) -> ExportUiState:
        return ExportUiState(can_save_image=not export_in_progress)

    @staticmethod
    def export_start_status() -> str:
        return "Exporting image..."

    @staticmethod
    def export_finished_status(ok: bool) -> str:
        return "Image saved" if ok else "Failed to save image"

    @staticmethod
    def preview_rendering_status() -> str:
        return "Rendering preview..."

    @staticmethod
    def preview_rendered_status() -> str:
        return "Preview rendered"

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

    @staticmethod
    def create_preview_worker(
        parent,
        *,
        request_id: int,
        snapshot_state: dict,
        worker_cls,
        on_progress,
        on_finished,
        on_failed,
        on_thread_closed,
    ) -> tuple[QThread, object]:
        thread = QThread(parent)
        worker = worker_cls(request_id, snapshot_state)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(on_progress)
        worker.finished.connect(on_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(on_failed)
        worker.failed.connect(thread.quit)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(on_thread_closed)
        return (thread, worker)
