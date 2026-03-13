from __future__ import annotations

import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class UpdateService:
    RELEASES_URL = "https://api.github.com/repos/anatolyzenkov/IOGraph/releases?per_page=20"
    USER_AGENT = "IOGraph-Updater"

    @classmethod
    def check_for_updates(cls, current_version: str, include_prerelease: bool) -> dict:
        try:
            req = Request(
                cls.RELEASES_URL,
                headers={"Accept": "application/vnd.github+json", "User-Agent": cls.USER_AGENT},
            )
            with urlopen(req, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, list):
                raise ValueError("Invalid updates response")
            release = cls.pick_release(payload, include_prerelease)
            if release is None:
                return {"ok": True, "has_update": False, "latest_tag": "", "latest_version": "", "url": "", "error": ""}
            tag = str(release.get("tag_name", "")).strip()
            latest_version = cls.normalize_version(tag)
            has_update = cls.is_newer(latest_version, cls.normalize_version(current_version))
            return {
                "ok": True,
                "has_update": has_update,
                "latest_tag": tag,
                "latest_version": latest_version,
                "url": str(release.get("html_url", "")),
                "asset_url": cls.asset_value(release, "url"),
                "asset_name": cls.asset_value(release, "name"),
                "error": "",
            }
        except (HTTPError, URLError, ValueError, TimeoutError) as exc:
            return {
                "ok": False,
                "has_update": False,
                "latest_tag": "",
                "latest_version": "",
                "url": "",
                "error": str(exc),
            }

    @classmethod
    def pick_release(cls, releases: list[dict], include_prerelease: bool) -> dict | None:
        best_release: dict | None = None
        best_key = None
        for release in releases:
            if not isinstance(release, dict):
                continue
            if release.get("draft", False):
                continue
            if not include_prerelease and release.get("prerelease", False):
                continue
            if cls.pick_asset(release) is None:
                continue
            tag = str(release.get("tag_name", "")).strip()
            version_key = cls.version_key(cls.normalize_version(tag))
            if version_key is None:
                continue
            if best_key is None or version_key > best_key:
                best_key = version_key
                best_release = release
        return best_release

    @classmethod
    def asset_value(cls, release: dict, key: str) -> str:
        asset = cls.pick_asset(release)
        if asset is None:
            return ""
        return str(asset.get(key, "")).strip()

    @staticmethod
    def pick_asset(release: dict) -> dict | None:
        assets = release.get("assets", [])
        if not isinstance(assets, list):
            return None

        if sys.platform == "darwin":
            for asset in assets:
                if not isinstance(asset, dict):
                    continue
                name = str(asset.get("name", "")).lower()
                if name.endswith(".zip") and any(token in name for token in ("mac", "macos", "osx", "darwin")):
                    return asset
            for asset in assets:
                if not isinstance(asset, dict):
                    continue
                name = str(asset.get("name", "")).lower()
                if name.endswith(".dmg"):
                    return asset
            return None

        if sys.platform.startswith("win"):
            for asset in assets:
                if not isinstance(asset, dict):
                    continue
                name = str(asset.get("name", "")).lower()
                if name.endswith(".exe") or name.endswith(".msi"):
                    return asset
            for asset in assets:
                if not isinstance(asset, dict):
                    continue
                name = str(asset.get("name", "")).lower()
                if name.endswith(".zip") and any(token in name for token in ("windows", "win")):
                    return asset
            return None

        for asset in assets:
            if not isinstance(asset, dict):
                continue
            name = str(asset.get("name", "")).lower()
            if name.endswith(".appimage") or name.endswith(".deb") or name.endswith(".rpm") or name.endswith(".tar.gz"):
                return asset
        return None

    @staticmethod
    def normalize_version(version: str) -> str:
        v = str(version).replace("\ufeff", "").strip()
        if v.lower().startswith("v"):
            return v[1:]
        return v

    @classmethod
    def is_newer(cls, latest: str, current: str) -> bool:
        latest_key = cls.version_key(latest)
        current_key = cls.version_key(current)
        if latest_key is None:
            return False
        if current_key is None:
            return True
        return latest_key > current_key

    @staticmethod
    def version_key(version: str):
        m = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$", version)
        if not m:
            return None
        major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
        prerelease = m.group(4)
        if prerelease is None:
            return (major, minor, patch, 1, ())
        identifiers = []
        for part in prerelease.split("."):
            if part.isdigit():
                identifiers.append((0, int(part)))
            else:
                identifiers.append((1, part))
        return (major, minor, patch, 0, tuple(identifiers))
