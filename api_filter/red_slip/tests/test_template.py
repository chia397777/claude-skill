"""
pytest api_filter/red_slip/tests/test_template.py -v
"""
from api_filter.red_slip.template import RedSlipData, ScheduleItem, render_red_slip
from api_filter.red_slip.messages import next_morning_msg, MORNING_MSGS


# ── 紅單渲染 ─────────────────────────────────────────────────

def test_basic_render_contains_name():
    data = RedSlipData(name="小明")
    result = render_red_slip(data, morning_msg="今天加油！")
    assert "小明" in result

def test_render_with_schedule():
    data = RedSlipData(
        name="小華",
        schedule=[ScheduleItem("09:00", "週會"), ScheduleItem("14:00", "客戶電話")],
    )
    result = render_red_slip(data, morning_msg="加油！")
    assert "週會" in result
    assert "客戶電話" in result
    assert "📋" in result

def test_render_with_todos():
    data = RedSlipData(name="阿明", todos=["繳健保", "回信"])
    result = render_red_slip(data, morning_msg="加油！")
    assert "繳健保" in result
    assert "回信" in result
    assert "✅" in result

def test_render_with_reminder():
    data = RedSlipData(name="阿花", reminder="記得吃藥")
    result = render_red_slip(data, morning_msg="加油！")
    assert "記得吃藥" in result
    assert "💊" in result

def test_render_empty_schedule_no_section():
    data = RedSlipData(name="小明")
    result = render_red_slip(data, morning_msg="加油！")
    assert "📋" not in result
    assert "✅" not in result
    assert "💊" not in result

def test_render_with_weather():
    data = RedSlipData(name="小明", weather="晴天 28°C")
    result = render_red_slip(data, morning_msg="加油！")
    assert "晴天 28°C" in result

def test_render_always_ends_with_prompt():
    data = RedSlipData(name="小明")
    result = render_red_slip(data, morning_msg="加油！")
    assert "有什麼需要我幫忙的嗎" in result


# ── 早晨訊息輪替 ─────────────────────────────────────────────

def test_morning_msgs_rotate():
    seen = set()
    for _ in range(len(MORNING_MSGS)):
        seen.add(next_morning_msg())
    assert len(seen) == len(MORNING_MSGS), "輪替庫應覆蓋所有句子"

def test_morning_msgs_cycle():
    """超過一輪後回到開頭"""
    first = next_morning_msg()
    for _ in range(len(MORNING_MSGS) - 1):
        next_morning_msg()
    cycled = next_morning_msg()
    assert first == cycled, "應循環回第一句"
