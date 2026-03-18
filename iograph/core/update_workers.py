from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile
from urllib.request import Request, urlopen

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from .update_service import UpdateService


class UpdateCheckWorker(QObject):
    finished = pyqtSignal(object)  # dict result

    def __init__(self, current_version: str, include_prerelease: bool) -> None:
        super().__init__()
        self._current_version = current_version
        self._include_prerelease = include_prerelease

    @pyqtSlot()
    def run(self) -> None:
        result = UpdateService.check_for_updates(self._current_version, self._include_prerelease)
        self.finished.emit(result)


class UpdateDownloadWorker(QObject):
    finished = pyqtSignal(bool, str, str)  # ok, path, error

    def __init__(self, asset_url: str, target_path: str) -> None:
        super().__init__()
        self._asset_url = asset_url
        self._target_path = Path(target_path)

    def _validate_download(self, path: Path) -> None:
        if path.suffix.lower() != ".zip":
            return
        with zipfile.ZipFile(path, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                raise ValueError(f"corrupt zip entry: {bad}")
            names = [name.lower() for name in zf.namelist()]
            if not any(".app/" in name for name in names):
                raise ValueError("downloaded zip does not contain .app bundle")

    @pyqtSlot()
    def run(self) -> None:
        tmp_path = self._target_path.with_suffix(self._target_path.suffix + ".part")
        attempts = 2
        last_error = ""
        for _attempt in range(attempts):
            try:
                req = Request(
                    self._asset_url,
                    headers={
                        "Accept": "application/octet-stream",
                        "User-Agent": "IOGraph-Updater",
                    },
                )
                with urlopen(req, timeout=30) as response, tmp_path.open("wb") as out:
                    shutil.copyfileobj(response, out)
                self._validate_download(tmp_path)
                tmp_path.replace(self._target_path)
                self.finished.emit(True, str(self._target_path), "")
                return
            except Exception as exc:
                last_error = str(exc)
                try:
                    if tmp_path.exists():
                        tmp_path.unlink()
                except Exception:
                    pass
        self.finished.emit(False, str(self._target_path), last_error)


class MacZipInstallWorker(QObject):
    finished = pyqtSignal(bool, str)  # ok, error

    def __init__(self, zip_path: str, target_app: str, current_team: str, current_pid: int) -> None:
        super().__init__()
        self._zip_path = Path(zip_path)
        self._target_app = Path(target_app)
        self._current_team = current_team
        self._current_pid = int(current_pid)

    @staticmethod
    def _codesign_team_identifier(app_path: Path) -> str:
        try:
            result = subprocess.run(
                ["codesign", "-dv", "--verbose=4", str(app_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            output = f"{result.stdout}\n{result.stderr}"
            match = re.search(r"TeamIdentifier=([A-Z0-9]+)", output)
            if match:
                return match.group(1)
        except Exception:
            return ""
        return ""

    def _verify_update_app(self, app_path: Path) -> tuple[bool, str]:
        try:
            subprocess.run(
                ["codesign", "--verify", "--deep", "--verbose=2", str(app_path)],
                capture_output=True,
                text=True,
                check=True,
            )
        except Exception as exc:
            stderr = ""
            if isinstance(exc, subprocess.CalledProcessError):
                stderr = (exc.stderr or "").strip()
            message = stderr.splitlines()[-1] if stderr else str(exc)
            return (False, f"signature verification failed ({message})")
        candidate_team = self._codesign_team_identifier(app_path)
        if not candidate_team:
            return (False, "TeamIdentifier not found in downloaded app signature")
        if self._current_team and candidate_team != self._current_team:
            return (False, f"team mismatch (downloaded {candidate_team}, current {self._current_team})")
        return (True, "")

    @pyqtSlot()
    def run(self) -> None:
        try:
            staging_dir = Path(tempfile.mkdtemp(prefix="iograph-update-"))
            subprocess.run(
                ["ditto", "-x", "-k", str(self._zip_path), str(staging_dir)],
                capture_output=True,
                text=True,
                check=True,
            )
            app_candidates = sorted(staging_dir.rglob("*.app"))
            if not app_candidates:
                self.finished.emit(False, "no .app bundle found in update package")
                return
            new_app = app_candidates[0]
            verified, error = self._verify_update_app(new_app)
            if not verified:
                self.finished.emit(False, error or "downloaded app failed signature/team verification")
                return
            helper_path = staging_dir / "install_update.sh"
            helper_path.write_text(
                "\n".join(
                    [
                        "#!/bin/bash",
                        "set -euo pipefail",
                        'SRC_APP=\"$1\"',
                        'DST_APP=\"$2\"',
                        'PID_TO_WAIT=\"$3\"',
                        'BACKUP_APP=\"${DST_APP}.old\"',
                        'TMP_APP=\"${DST_APP}.new\"',
                        "restore_on_error() {",
                        "  if [[ ! -e \"$DST_APP\" && -e \"$BACKUP_APP\" ]]; then",
                        "    mv \"$BACKUP_APP\" \"$DST_APP\" || true",
                        "  fi",
                        "  open -a \"$DST_APP\" >/dev/null 2>&1 || true",
                        "}",
                        "trap restore_on_error ERR",
                        "for _ in $(seq 1 240); do",
                        '  if ! kill -0 \"$PID_TO_WAIT\" >/dev/null 2>&1; then',
                        "    break",
                        "  fi",
                        "  sleep 0.25",
                        "done",
                        "rm -rf \"$BACKUP_APP\"",
                        "rm -rf \"$TMP_APP\"",
                        "ditto \"$SRC_APP\" \"$TMP_APP\"",
                        "xattr -dr com.apple.quarantine \"$TMP_APP\" >/dev/null 2>&1 || true",
                        "if [[ -e \"$DST_APP\" ]]; then mv \"$DST_APP\" \"$BACKUP_APP\"; fi",
                        "mv \"$TMP_APP\" \"$DST_APP\"",
                        "rm -rf \"$BACKUP_APP\"",
                        "open -a \"$DST_APP\" >/dev/null 2>&1 || true",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            helper_path.chmod(0o755)
            subprocess.Popen(
                ["/bin/bash", str(helper_path), str(new_app), str(self._target_app), str(self._current_pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            self.finished.emit(True, "")
        except Exception as exc:
            self.finished.emit(False, str(exc))
