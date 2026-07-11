"""
離線對話包載入器 & 比對器

架構：
  - PackLoader：載入 JSON 包，執行 trigger 比對
  - 模組層級單例：load_pack() / match_offline()
  - 比對策略：
      1. 全字符合（trigger 完全包含在訊息中）
      2. 比對優先順序：JSON 檔案中 scenario 的排列順序

預設包（全域預載，不論 GPS 在哪裡）：
  - legal_taiwan：台灣日常法律，App 啟動即載入，永遠排第一
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_PACKS_DIR = Path(__file__).parent / "packs"

# 全域預載包：不論 GPS 位置，App 啟動即自動載入，且永遠排在最前面
DEFAULT_PACKS: list[str] = ["legal_taiwan"]


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
        """完全清除所有包（測試用）。Production 請用 reset_to_defaults()。"""
        self._packs.clear()

    def reset_to_defaults(self) -> None:
        """清除 GPS 補充包，重載預設包（切換位置時呼叫）。"""
        self._packs.clear()
        for pid in DEFAULT_PACKS:
            if not self.is_loaded(pid):
                try:
                    self.load(pid)
                except FileNotFoundError:
                    pass


# ── 模組層級單例 ─────────────────────────────────────────────
_loader = PackLoader()

# App 啟動時自動載入預設包（legal_taiwan 永遠排第一）
for _pid in DEFAULT_PACKS:
    try:
        _loader.load(_pid)
    except FileNotFoundError:
        pass


def load_pack(pack_id: str, lang: str = "zh-TW") -> None:
    """
    補充載入 GPS 對應包（排在預設包之後）。
    若已載入則跳過（冪等）。
    """
    if not _loader.is_loaded(pack_id):
        _loader.load(pack_id, lang)


def reset_to_defaults() -> None:
    """切換位置時重設：清除 GPS 補充包，保留預設包。"""
    _loader.reset_to_defaults()


def match_offline(text: str) -> PackMatch | None:
    """比對已載入的所有包，回傳 PackMatch 或 None。"""
    return _loader.match(text)


def is_loaded(pack_id: str) -> bool:
    return _loader.is_loaded(pack_id)
