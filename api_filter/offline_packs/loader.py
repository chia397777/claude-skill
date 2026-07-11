"""
離線對話包載入器 & 比對器

架構：
  - PackLoader：載入 JSON 包，執行 trigger 比對
  - 模組層級單例：load_pack() / match_offline()
  - 比對策略：
      1. 全字符合（trigger 完全包含在訊息中）
      2. 比對優先順序：JSON 檔案中 scenario 的排列順序
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_PACKS_DIR = Path(__file__).parent / "packs"


@dataclass
class PackMatch:
    pack_id: str
    scenario_id: str
    category: str        # "airport" | "taxi" | "hotel" | "attraction"
    response: str


class PackLoader:
    def __init__(self) -> None:
        self._packs: list[dict] = []

    def load(self, pack_id: str, lang: str = "zh-TW") -> None:
        """載入指定的對話包（可多次呼叫，累加載入）。"""
        fname = f"{pack_id}_{lang.lower().replace('-', '_')}.json"
        path = _PACKS_DIR / fname
        if not path.exists():
            raise FileNotFoundError(f"找不到對話包：{path}")

        raw = path.read_text(encoding="utf-8")
        # 移除 JSON 中的行內 // 註解（方便維護，原生 JSON 不支援）
        raw = re.sub(r"//.*", "", raw)
        self._packs.append(json.loads(raw))

    def is_loaded(self, pack_id: str) -> bool:
        return any(p.get("pack_id") == pack_id for p in self._packs)

    def match(self, text: str) -> PackMatch | None:
        """
        依序比對所有已載入的包，回傳第一個命中的情境。
        比對不分大小寫。
        """
        text_lower = text.lower()
        for pack in self._packs:
            for scenario in pack["scenarios"]:
                for trigger in scenario["triggers"]:
                    if trigger.lower() in text_lower:
                        return PackMatch(
                            pack_id=pack["pack_id"],
                            scenario_id=scenario["id"],
                            category=scenario["category"],
                            response=scenario["response"],
                        )
        return None

    def clear(self) -> None:
        self._packs.clear()


# ── 模組層級單例 ─────────────────────────────────────────────
_loader = PackLoader()


def load_pack(pack_id: str, lang: str = "zh-TW") -> None:
    """
    載入對話包。建議在 FastAPI startup event 中呼叫：

        @app.on_event("startup")
        def startup():
            load_pack("airport_travel")
    """
    _loader.load(pack_id, lang)


def match_offline(text: str) -> PackMatch | None:
    """比對已載入的所有包，回傳 PackMatch 或 None。"""
    return _loader.match(text)


def is_loaded(pack_id: str) -> bool:
    return _loader.is_loaded(pack_id)
