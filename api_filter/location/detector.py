"""
地理位置偵測與離線包選擇器

流程：
  1. 前端傳入 GPS 座標（lat, lng）
  2. 呼叫 Google Maps Geocoding API 取得行政區資訊
  3. 依據地點規則對應並自動載入對應的離線對話包
  4. 回傳建議載入的 pack_id 清單與地點描述

設計原則：
  - 純函式，不持有狀態；pack 載入由呼叫方決定
  - Google API 呼叫失敗時 gracefully 回傳空清單
  - 支援多包（機場 + 南台灣同時啟用）
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ── 座標→離線包 對應規則 ──────────────────────────────────────────
# 每條規則包含：
#   bbox        : (min_lat, max_lat, min_lng, max_lng) 矩形邊界
#   pack_ids    : 符合時要載入的 pack_id 清單
#   label       : 人類可讀的地點名稱（用於日誌/回應說明）
#
# 優先順序：越具體（機場）排越前；通用區域（南台灣）排後
_LOCATION_RULES: list[dict] = [
    # ── 機場 ────────────────────────────────────────────────────
    {
        "label": "桃園國際機場",
        "bbox": (25.055, 25.090, 121.215, 121.255),
        "pack_ids": ["airport_travel"],
    },
    {
        "label": "高雄小港機場",
        "bbox": (22.565, 22.600, 120.340, 120.370),
        "pack_ids": ["airport_travel", "southern_taiwan"],
    },
    {
        "label": "台南機場",
        "bbox": (22.945, 22.960, 120.195, 120.220),
        "pack_ids": ["airport_travel", "southern_taiwan"],
    },
    {
        "label": "台東豐年機場",
        "bbox": (22.745, 22.765, 121.095, 121.115),
        "pack_ids": ["airport_travel", "southern_taiwan"],
    },
    # ── 南台灣各縣市 ─────────────────────────────────────────────
    {
        "label": "高雄市",
        "bbox": (22.400, 22.760, 120.200, 120.750),
        "pack_ids": ["southern_taiwan"],
    },
    {
        "label": "台南市",
        "bbox": (22.700, 23.450, 120.050, 120.500),
        "pack_ids": ["southern_taiwan"],
    },
    {
        "label": "屏東縣（含墾丁）",
        "bbox": (21.890, 22.710, 120.420, 120.910),
        "pack_ids": ["southern_taiwan"],
    },
    {
        "label": "台東縣",
        "bbox": (22.210, 23.180, 120.880, 121.380),
        "pack_ids": ["southern_taiwan"],
    },
]

# 所有可用 pack_id → 其所需的 JSON 檔名（lang 預設 zh-TW）
AVAILABLE_PACKS: dict[str, str] = {
    "airport_travel": "airport_travel_zh_tw.json",
    "southern_taiwan": "southern_taiwan_zh_tw.json",
}


@dataclass
class LocationContext:
    lat: float
    lng: float
    matched_label: str = ""          # 第一個命中規則的地點名稱
    suggested_packs: list[str] = field(default_factory=list)   # 建議載入的 pack_id
    geocoded_address: str = ""       # Google API 回傳的完整地址（可選）


def _match_rules(lat: float, lng: float) -> list[dict]:
    """依序比對所有規則，回傳所有命中的規則（可能多條）。"""
    matched = []
    for rule in _LOCATION_RULES:
        min_lat, max_lat, min_lng, max_lng = rule["bbox"]
        if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
            matched.append(rule)
    return matched


def detect_from_coordinates(
    lat: float,
    lng: float,
    google_api_key: Optional[str] = None,
) -> LocationContext:
    """
    從 GPS 座標推斷應載入的離線包。

    Args:
        lat: 緯度
        lng: 經度
        google_api_key: Google Maps Geocoding API 金鑰（選填）
                        有金鑰時額外取得可讀地址；無金鑰仍可用 bbox 規則比對

    Returns:
        LocationContext，包含 suggested_packs 清單
    """
    ctx = LocationContext(lat=lat, lng=lng)

    # Step 1: bbox 規則比對（不需要網路）
    matched_rules = _match_rules(lat, lng)
    if matched_rules:
        ctx.matched_label = matched_rules[0]["label"]
        # 合併所有命中規則的 pack_ids（去重、維持順序）
        seen: set[str] = set()
        for rule in matched_rules:
            for pid in rule["pack_ids"]:
                if pid not in seen:
                    ctx.suggested_packs.append(pid)
                    seen.add(pid)

    # Step 2: 可選 — Google Geocoding API 取得可讀地址
    api_key = google_api_key or os.getenv("GOOGLE_MAPS_API_KEY", "")
    if api_key:
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            resp = httpx.get(
                url,
                params={"latlng": f"{lat},{lng}", "language": "zh-TW", "key": api_key},
                timeout=3.0,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if results:
                ctx.geocoded_address = results[0].get("formatted_address", "")
        except Exception as exc:
            logger.warning("Google Geocoding 失敗 (lat=%s, lng=%s): %s", lat, lng, exc)

    logger.info(
        "location_detect | lat=%.4f lng=%.4f | label=%r | packs=%s",
        lat, lng, ctx.matched_label, ctx.suggested_packs,
    )
    return ctx


def auto_load_packs(
    lat: float,
    lng: float,
    google_api_key: Optional[str] = None,
) -> LocationContext:
    """
    偵測位置並自動呼叫 load_pack() 載入尚未載入的包。

    通常在每個 session 開始時，或收到第一則訊息時呼叫一次。

    Returns:
        LocationContext（同 detect_from_coordinates）
    """
    from api_filter.offline_packs.loader import load_pack, is_loaded

    ctx = detect_from_coordinates(lat, lng, google_api_key)
    for pack_id in ctx.suggested_packs:
        if not is_loaded(pack_id):
            try:
                load_pack(pack_id)
                logger.info("auto_load_packs: loaded %r", pack_id)
            except FileNotFoundError:
                logger.error("auto_load_packs: pack not found — %r", pack_id)
    return ctx
