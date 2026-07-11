"""
pytest api_filter/offline_packs/tests/test_airport_pack.py -v
"""
import pytest
from api_filter.offline_packs.loader import PackLoader, PackMatch


@pytest.fixture
def loader() -> PackLoader:
    """每個測試用獨立的 PackLoader，不影響全域單例。"""
    pl = PackLoader()
    pl.load("airport_travel")
    return pl


# ═══════════════════════════════════════════════════════
#  機場篇
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("text,expected_id", [
    ("我要怎麼辦理報到", "airport_checkin"),
    ("請問登機手續在哪裡辦", "airport_checkin"),
    ("登機閘口在哪裡", "airport_gate"),
    ("幾號登機口", "airport_gate"),
    ("行李托運限重多少", "airport_baggage_check"),
    ("我的行李超重怎麼辦", "airport_baggage_check"),
    ("手提行李可以帶多重", "airport_carryon"),
    ("隨身行李的尺寸限制", "airport_carryon"),
    ("安全檢查要把筆電拿出來嗎", "airport_security"),
    ("過安檢需要脫鞋嗎", "airport_security"),
    ("入境要填什麼表", "airport_immigration"),
    ("護照查驗的流程", "airport_immigration"),
    ("海關申報要帶多少現金才需要申報", "airport_customs"),
    ("我要轉機需要出境嗎", "airport_transit"),
    ("layover 需要重新辦登機嗎", "airport_transit"),
    ("班機延誤了怎麼辦", "airport_delay"),
    ("航班取消可以要求退票嗎", "airport_delay"),
    ("行李沒出來在轉盤上", "airport_baggage_claim"),
    ("行李遺失怎麼處理", "airport_baggage_claim"),
    ("免稅店在哪裡", "airport_dutyfree"),
])
def test_airport_scenarios(loader, text, expected_id):
    m = loader.match(text)
    assert m is not None, f"應命中情境但未匹配：{text!r}"
    assert m.scenario_id == expected_id, (
        f"情境 ID 錯誤\n  輸入：{text!r}\n  預期：{expected_id}\n  實際：{m.scenario_id}"
    )
    assert m.category == "airport"
    assert len(m.response) > 20


# ═══════════════════════════════════════════════════════
#  計程車篇
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("text,expected_id", [
    ("請問在哪裡叫計程車", "taxi_hail"),
    ("機場怎麼搭 Uber", "taxi_hail"),
    ("要怎麼告訴司機目的地", "taxi_destination"),
    ("我去這個飯店地址", "taxi_destination"),
    ("計程車車資大概多少", "taxi_fare"),
    ("機場到台北市區要多久", "taxi_fare"),
    ("行李很多可以放後車廂嗎", "taxi_luggage"),
    ("計程車可以刷卡嗎", "taxi_payment"),
    ("司機停車了我怎麼付錢", "taxi_payment"),
    ("快到飯店了", "taxi_arrive_hotel"),
])
def test_taxi_scenarios(loader, text, expected_id):
    m = loader.match(text)
    assert m is not None, f"應命中情境但未匹配：{text!r}"
    assert m.scenario_id == expected_id
    assert m.category == "taxi"


# ═══════════════════════════════════════════════════════
#  飯店篇
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("text,expected_id", [
    ("飯店辦理入住需要帶什麼", "hotel_checkin"),
    ("訂房後飯店怎麼辦理入住", "hotel_checkin"),
    ("冷氣壞了怎麼辦", "hotel_room_issue"),
    ("門卡失效了", "hotel_room_issue"),
    ("飯店早餐幾點", "hotel_breakfast"),
    ("早餐有沒有包含在裡面", "hotel_breakfast"),
    ("飯店 wifi 密碼是什麼", "hotel_wifi"),
    ("網路連不上怎麼辦", "hotel_wifi"),
    ("退房後行李可以寄放嗎", "hotel_luggage_storage"),
    ("行李寄存要收費嗎", "hotel_luggage_storage"),
    ("可以幫我設定叫醒服務嗎", "hotel_wakeup"),
    ("morning call 怎麼預約", "hotel_wakeup"),
    ("退房時間幾點", "hotel_checkout"),
    ("可以 late check out 嗎", "hotel_checkout"),
])
def test_hotel_scenarios(loader, text, expected_id):
    m = loader.match(text)
    assert m is not None, f"應命中情境但未匹配：{text!r}"
    assert m.scenario_id == expected_id
    assert m.category == "hotel"


# ═══════════════════════════════════════════════════════
#  景點篇
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("text,expected_id", [
    ("台灣有什麼推薦景點", "attraction_recommend"),
    ("必去的觀光地點", "attraction_recommend"),
    ("景點怎麼搭捷運去", "attraction_transport"),
    ("高鐵買票怎麼買", "attraction_transport"),
    ("故宮今天有開嗎", "attraction_hours"),
    ("夜市幾點開始", "attraction_hours"),
    ("台北 101 的門票多少錢", "attraction_ticket"),
    ("故宮博物院學生票有優惠嗎", "attraction_ticket"),
    ("裡面可以拍照嗎", "attraction_photo"),
    ("無人機可以在景點飛嗎", "attraction_photo"),
    ("附近有什麼好吃的", "attraction_nearby_food"),
    ("推薦一下夜市小吃", "attraction_nearby_food"),
])
def test_attraction_scenarios(loader, text, expected_id):
    m = loader.match(text)
    assert m is not None, f"應命中情境但未匹配：{text!r}"
    assert m.scenario_id == expected_id
    assert m.category == "attraction"


# ═══════════════════════════════════════════════════════
#  無關問題不應命中
# ═══════════════════════════════════════════════════════

@pytest.mark.parametrize("text", [
    "我的合約被違約了怎麼辦",
    "民法第184條是什麼",
    "今天天氣真好",
    "你好",
    "謝謝",
])
def test_non_travel_no_match(loader, text):
    m = loader.match(text)
    assert m is None, f"非旅遊問題不應命中：{text!r}（命中了 {m.scenario_id if m else None}）"


# ═══════════════════════════════════════════════════════
#  整合：pre_filter 含離線包
# ═══════════════════════════════════════════════════════

def test_pre_filter_with_pack():
    from api_filter.offline_packs.loader import load_pack, _loader
    from api_filter.filter import pre_filter

    # 確保包已載入（若先前測試已載入則跳過）
    if not _loader.is_loaded("airport_travel"):
        load_pack("airport_travel")

    r = pre_filter("請問登機閘口在哪裡")
    assert r.blocked
    assert r.layer == "layer1_5_offline_pack"
    assert "閘口" in r.reply or "Gate" in r.reply or "登機" in r.reply
