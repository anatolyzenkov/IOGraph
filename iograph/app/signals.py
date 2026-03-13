from PyQt6.QtCore import QObject, pyqtSignal


class AppSignals(QObject):
    update_check_started = pyqtSignal(bool)  # manual
    update_check_finished = pyqtSignal(bool, object)  # manual, result
    update_download_started = pyqtSignal(str, bool)  # latest_version, manual
    update_download_finished = pyqtSignal(bool, str, str, bool)  # ok, path, error, manual
    session_tracking_started = pyqtSignal()
    session_tracking_stopped = pyqtSignal()
    session_reset = pyqtSignal()
    session_restored = pyqtSignal()
