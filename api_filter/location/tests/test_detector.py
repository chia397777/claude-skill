"""
pytest api_filter/location/tests/test_detector.py -v
"""
import pytest
from api_filter.location.detector import detect_from_coordinates, _match_rules


# ═══════════════════════════════════════════════════════
#  bbox 規則比對
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("lat,lng,expected_label,expected_packs", [
    # 桃園機場
    (25.077, 121.232, "桃園國際機場", ["airport_travel"]),
    # 高雄小港機場
    (22.577, 120.350, "高雄小港機場", ["airport_travel", "southern_taiwan"]),
    # 高雄市中心（非機場）
    (22.630, 120.300, "高雄市", ["southern_taiwan"]),
    # 台南市
    (23.000, 120.200, "台南市", ["southern_taiwan"]),
    # 墾丁（屏東縣）
    (21.950, 120.800, "屏東縣（含墾丁）", ["southern_taiwan"]),
    # 台東市
    (22.750, 121.150, "台東縣", ["southern_taiwan"]),
])
def test_known_locations(lat, lng, expected_label, expected_packs):
    ctx = detect_from_coordinates(lat, lng)
    assert ctx.matched_label == expected_label, (
        f"({lat},{lng}) 預期地點 {expected_label!r}，實際 {ctx.matched_label!r}"
    )
    assert ctx.suggested_packs == expected_packs, (
        f"({lat},{lng}) 預期包 {expected_packs}，實際 {ctx.suggested_packs}"
    )


def test_unknown_location_returns_empty():
    # 台北市中心（無規則覆蓋）
    ctx = detect_from_coordinates(25.047, 121.517)
    assert ctx.suggested_packs == []
    assert ctx.matched_label == ""


def test_coordinates_stored_in_context():
    ctx = detect_from_coordinates(22.630, 120.300)
    assert ctx.lat == 22.630
    assert ctx.lng == 120.300


# ═══════════════════════════════════════════════════════
#  多包重疊（機場在市區邊緣，兩條規則同時命中）
# ═══════════════════════════════════════════════════════

def test_airport_inside_city_deduplicates_packs():
    """高雄小港機場同時命中「機場」和「高雄市」規則，airport_travel 只出現一次。"""
    ctx = detect_from_coordinates(22.577, 120.350)
    assert ctx.suggested_packs.count("airport_travel") == 1
    assert ctx.suggested_packs.count("southern_taiwan") == 1


# ═══════════════════════════════════════════════════════
#  不呼叫 Google API（無金鑰）
# ═══════════════════════════════════════════════════════

def test_no_google_key_still_works(monkeypatch):
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    ctx = detect_from_coordinates(22.630, 120.300, google_api_key=None)
    assert ctx.suggested_packs == ["southern_taiwan"]
    assert ctx.geocoded_address == ""  # 無 API key，地址欄位為空


# ═══════════════════════════════════════════════════════
#  _match_rules 直接測試
# ═══════════════════════════════════════════════════════

def test_match_rules_returns_all_overlapping():
    """小港機場座標應同時命中機場規則和高雄市規則。"""
    matched = _match_rules(22.577, 120.350)
    labels = [r["label"] for r in matched]
    assert "高雄小港機場" in labels
    assert "高雄市" in labels


def test_match_rules_empty_for_unknown():
    assert _match_rules(25.047, 121.517) == []
