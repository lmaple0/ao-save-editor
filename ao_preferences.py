"""UI language selection and per-user preferences, separate from game saves."""

import ctypes
import json
import locale
import os
from pathlib import Path

LANGUAGES = ("zh_cn", "en", "ja")


def preferences_path():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".config"))
    return base / "AoSaveEditor" / "settings.json"


def system_ui_locale():
    if os.name == "nt":
        language_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return locale.windows_locale.get(language_id, "en_US")
    return locale.getlocale()[0] or "en_US"


def language_for_locale(value):
    language = value.lower().replace("-", "_").split("_", 1)[0]
    return {"zh": "zh_cn", "ja": "ja"}.get(language, "en")


def load_language(path, system_locale=None):
    path = Path(path)
    if path.is_file():
        language = json.loads(path.read_text(encoding="utf-8")).get("language")
        if language in LANGUAGES:
            return language
    return language_for_locale(system_locale if system_locale is not None else system_ui_locale())


def save_language(path, language):
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported UI language: {language}")
    path = Path(path)
    settings = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    settings["language"] = language
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
