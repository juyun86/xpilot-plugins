"""Simplified Chinese language pack. UI only; no control hooks or processes."""
import json
from pathlib import Path
from openpilot.tesla.plugin import Plugin


class ChineseUI(Plugin):
  @classmethod
  def ui_language(cls):
    root = Path(__file__).resolve().parent
    return {"code": "zh-CHS", "font": str(root / "NotoSansCJKsc-Regular.otf"),
            "translations": json.loads((root / "translations.json").read_text(encoding="utf-8"))}
