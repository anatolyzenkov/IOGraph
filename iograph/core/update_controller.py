from __future__ import annotations

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from .update_workers import UpdateCheckWorker, UpdateDownloadWorker


class UpdateController(QObject):
    check_started = pyqtSignal(bool)  # manual
    check_finished = pyqtSignal(bool, object)  # manual, result
    download_started = pyqtSignal(str, bool)  # latest_version, manual
    download_finished = pyqtSignal(bool, str, str, str, bool)  # ok, path, error, latest_version, manual
    state_changed = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._check_thread: QThread | None = None
        self._check_worker: UpdateCheckWorker | None = None
        self._download_thread: QThread | None = None
        self._download_worker: UpdateDownloadWorker | None = None

    def is_checking(self) -> bool:
        return self._check_thread is not None

    def is_downloading(self) -> bool:
        return self._download_thread is not None

    def start_check(self, current_version: str, manual: bool) -> bool:
        if self._check_thread is not None or self._download_thread is not None:
            return False
        include_prerelease = "-" in current_version
        thread = QThread(self)
        worker = UpdateCheckWorker(current_version, include_prerelease)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(lambda result, is_manual=manual: self.check_finished.emit(is_manual, result))
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_check_thread_closed)
        self._check_thread = thread
        self._check_worker = worker
        self.check_started.emit(manual)
        self.state_changed.emit()
        thread.start()
        return True

    def start_download(self, latest_version: str, asset_url: str, target_path: str, manual: bool) -> bool:
        if self._download_thread is not None:
            return False
        thread = QThread(self)
        worker = UpdateDownloadWorker(asset_url, target_path)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(
            lambda ok, path, err, version=latest_version, is_manual=manual: self.download_finished.emit(
                ok, path, err, version, is_manual
            )
        )
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_download_thread_closed)
        self._download_thread = thread
        self._download_worker = worker
        self.download_started.emit(latest_version, manual)
        self.state_changed.emit()
        thread.start()
        return True

    def _on_check_thread_closed(self) -> None:
        self._check_thread = None
        self._check_worker = None
        self.state_changed.emit()

    def _on_download_thread_closed(self) -> None:
        self._download_thread = None
        self._download_worker = None
        self.state_changed.emit()
