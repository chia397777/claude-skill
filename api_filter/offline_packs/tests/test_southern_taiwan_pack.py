"""
pytest api_filter/offline_packs/tests/test_southern_taiwan_pack.py -v
"""
import pytest
from api_filter.offline_packs.loader import PackLoader, PackMatch


@pytest.fixture
def loader() -> PackLoader:
    pl = PackLoader()
    pl.load("southern_taiwan")
    return pl


# ═══════════════════════════════════════════════════════
#  城市概覽
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("text,expected_id", [
    ("我想去高雄玩", "city_kaohsiung"),
    ("高雄有什麼好玩的", "city_kaohsiung"),
    ("台南旅遊", "city_tainan"),
    ("府城有哪些景點", "city_tainan"),
    ("屏東有什麼玩", "city_pingtung"),
    ("屏東縣旅遊推薦", "city_pingtung"),
    ("想去台東", "city_taitung"),
    ("台東縣推薦景點", "city_taitung"),
])
def test_city_scenarios(loader, text, expected_id):
    m = loader.match(text)
    assert m is not None, f"應命中情境但未匹配：{text!r}"
    assert m.scenario_id == expected_id, (
        f"情境 ID 錯誤\n  輸入：{text!r}\n  預期：{expected_id}\n  實際：{m.scenario_id}"
    )
    assert m.category == "city"
    assert len(m.response) > 30


# ═══════════════════════════════════════════════════════
#  熱門景點
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("text,expected_id", [
    ("駁二藝術特區怎麼去", "spot_pier2"),
    ("Pier-2 在哪裡", "spot_pier2"),
    ("蓮池潭怎麼玩", "spot_lotus_pond"),
    ("龍虎塔門票多少", "spot_lotus_pond"),
    ("旗津渡輪怎麼搭", "spot_cijin"),
    ("旗津老街怎麼去", "spot_cijin"),
    ("美麗島站在哪裡", "spot_formosa_blvd"),
    ("光之穹頂怎麼看", "spot_formosa_blvd"),
    ("安平古堡幾點開", "spot_anping_fort"),
    ("荷蘭城堡在台南嗎", "spot_anping_fort"),
    ("赤崁樓門票多少", "spot_chihkan_tower"),
    ("台南古蹟有哪些", "spot_chihkan_tower"),
    ("墾丁南灣可以游泳嗎", "spot_kenting"),
    ("後壁湖浮潛怎麼去", "spot_kenting"),
    ("墾丁怎麼去", "spot_kenting"),
    ("台東熱氣球怎麼預約", "spot_hot_air_balloon"),
    ("鹿野高台怎麼去", "spot_hot_air_balloon"),
    ("知本溫泉怎麼去", "spot_zhiben"),
    ("台東泡湯推薦", "spot_zhiben"),
    ("伯朗大道在哪裡", "spot_brown_blvd"),
    ("金城武樹在哪", "spot_brown_blvd"),
])
def test_attraction_scenarios(loader, text, expected_id):
    m = loader.match(text)
    assert m is not None, f"應命中情境但未匹配：{text!r}"
    assert m.scenario_id == expected_id, (
        f"情境 ID 錯誤\n  輸入：{text!r}\n  預期：{expected_id}\n  實際：{m.scenario_id}"
    )
    assert m.category == "attraction"


# ═══════════════════════════════════════════════════════
#  路程時間
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("text,expected_id", [
    ("台北到高雄要多久", "route_taipei_kaohsiung"),
    ("高雄到台北怎麼去", "route_taipei_kaohsiung"),
    ("台北到台南多久", "route_taipei_tainan"),
    ("高雄到墾丁怎麼去", "route_kaohsiung_kenting"),
    ("多久到墾丁", "route_kaohsiung_kenting"),
    ("高雄台南怎麼去", "route_kaohsiung_tainan"),
    ("高雄台南多久", "route_kaohsiung_tainan"),
    ("高雄到台東多久", "route_kaohsiung_taitung"),
    ("南迴公路景點", "route_kaohsiung_taitung"),
])
def test_route_scenarios(loader, text, expected_id):
    m = loader.match(text)
    assert m is not None, f"應命中情境但未匹配：{text!r}"
    assert m.scenario_id == expected_id, (
        f"情境 ID 錯誤\n  輸入：{text!r}\n  預期：{expected_id}\n  實際：{m.scenario_id}"
    )
    assert m.category == "route"


# ═══════════════════════════════════════════════════════
#  司乘雙語對話
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("text,expected_id", [
    ("您要去哪裡", "driver_destination_confirm"),
    ("乘客要去哪裡", "driver_destination_confirm"),
    ("外國人乘客怎麼溝通", "driver_foreign_passenger"),
    ("語言不通怎麼辦", "driver_foreign_passenger"),
    ("走哪條路比較快", "driver_route_explain"),
    ("走國道嗎", "driver_route_explain"),
    ("台灣計程車要給小費嗎", "driver_tips"),
    ("tip 要給多少", "driver_tips"),
])
def test_driver_passenger_scenarios(loader, text, expected_id):
    m = loader.match(text)
    assert m is not None, f"應命中情境但未匹配：{text!r}"
    assert m.scenario_id == expected_id, (
        f"情境 ID 錯誤\n  輸入：{text!r}\n  預期：{expected_id}\n  實際：{m.scenario_id}"
    )
    assert m.category == "driver_passenger"


# ═══════════════════════════════════════════════════════
#  注意事項
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("text,expected_id", [
    ("颱風來了怎麼辦", "notice_typhoon"),
    ("颱風警報停班停課嗎", "notice_typhoon"),
    ("海灘紅旗代表什麼", "notice_beach_safety"),
    ("海灘可以游泳嗎", "notice_beach_safety"),
    ("廟裡有什麼規矩", "notice_temple_etiquette"),
    ("temple 參觀注意事項", "notice_temple_etiquette"),
    ("南台灣很熱要怎麼防中暑", "notice_weather_heatstroke"),
    ("夏天台灣要防曬嗎", "notice_weather_heatstroke"),
    ("夜市收信用卡嗎", "notice_cash_payment"),
    ("要帶現金嗎", "notice_cash_payment"),
    ("緊急電話幾號", "notice_emergency"),
    ("叫救護車怎麼打", "notice_emergency"),
])
def test_notice_scenarios(loader, text, expected_id):
    m = loader.match(text)
    assert m is not None, f"應命中情境但未匹配：{text!r}"
    assert m.scenario_id == expected_id, (
        f"情境 ID 錯誤\n  輸入：{text!r}\n  預期：{expected_id}\n  實際：{m.scenario_id}"
    )
    assert m.category == "notice"


# ═══════════════════════════════════════════════════════
#  非南台灣問題不應命中
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("text", [
    "民法第184條是什麼",
    "我的合約被違約了",
    "今天天氣怎樣",
    "你好",
    "謝謝",
    "台北101多高",
])
def test_non_southern_taiwan_no_match(loader, text):
    m = loader.match(text)
    assert m is None, f"非南台灣問題不應命中：{text!r}（命中了 {m.scenario_id if m else None}）"


# ═══════════════════════════════════════════════════════
#  回應品質驗證
# ═══════════════════════════════════════════════════════

def test_response_quality(loader):
    """每個 scenario 的回應都應該超過 50 字。"""
    for pack in loader._packs:
        for scenario in pack["scenarios"]:
            assert len(scenario["response"]) > 50, (
                f"情境 {scenario['id']} 的回應太短：{scenario['response'][:30]!r}"
            )
