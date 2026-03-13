from __future__ import annotations

from pathlib import Path


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
