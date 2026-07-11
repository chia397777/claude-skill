"""
pytest api_filter/red_slip/tests/test_template.py -v
"""
from api_filter.red_slip.template import (
    TemplateData, ScheduleItem, render_template,
    RedSlipData, render_red_slip,  # backward-compat aliases
    to_context_block,
)
from api_filter.red_slip.messages import next_morning_msg, MORNING_MSGS


# ── 表格化模版渲染 ────────────────────────────────────────────

def test_basic_render_contains_name():
    data = TemplateData(name="小明")
    result = render_template(data, morning_msg="今天加油！")
    assert "小明" in result

def test_render_with_schedule():
    data = TemplateData(
        name="小華",
        schedule=[ScheduleItem("09:00", "週會"), ScheduleItem("14:00", "客戶電話")],
    )
    result = render_template(data, morning_msg="加油！")
    assert "週會" in result
    assert "客戶電話" in result
    assert "📋" in result

def test_render_with_todos():
    data = TemplateData(name="阿明", todos=["繳健保", "回信"])
    result = render_template(data, morning_msg="加油！")
    assert "繳健保" in result
    assert "回信" in result
    assert "✅" in result

def test_render_with_reminder():
    data = TemplateData(name="阿花", reminder="記得吃藥")
    result = render_template(data, morning_msg="加油！")
    assert "記得吃藥" in result
    assert "💊" in result

def test_render_empty_schedule_no_section():
    data = TemplateData(name="小明")
    result = render_template(data, morning_msg="加油！")
    assert "📋" not in result
    assert "✅" not in result
    assert "💊" not in result

def test_render_with_weather():
    data = TemplateData(name="小明", weather="晴天 28°C")
    result = render_template(data, morning_msg="加油！")
    assert "晴天 28°C" in result

def test_render_always_ends_with_prompt():
    data = TemplateData(name="小明")
    result = render_template(data, morning_msg="加油！")
    assert "有什麼需要我幫忙的嗎" in result

def test_table_borders_present():
    data = TemplateData(name="小明")
    result = render_template(data, morning_msg="加油！")
    assert "╔" in result
    assert "╚" in result
    assert "║" in result


# ── 雙語輸出 ──────────────────────────────────────────────────

def test_bilingual_name():
    data = TemplateData(name="小雅", name_en="Xiaoya", bilingual=True)
    result = render_template(data, morning_msg="加油！")
    assert "Xiaoya" in result

def test_bilingual_weather():
    data = TemplateData(name="小雅", weather="多雲 30°C", weather_en="Cloudy 30°C", bilingual=True)
    result = render_template(data, morning_msg="加油！")
    assert "Cloudy 30°C" in result

def test_bilingual_schedule():
    data = TemplateData(
        name="小雅",
        schedule=[ScheduleItem("10:00", "赤崁樓導覽", title_en="Chihkan Tower Tour")],
        bilingual=True,
    )
    result = render_template(data, morning_msg="加油！")
    assert "Chihkan Tower Tour" in result
    assert "Today's Schedule" in result

def test_bilingual_todos():
    data = TemplateData(
        name="小雅",
        todos=["買棺材板"],
        todos_en=["Buy Coffin Bread"],
        bilingual=True,
    )
    result = render_template(data, morning_msg="加油！")
    assert "Buy Coffin Bread" in result
    assert "To-Do List" in result

def test_bilingual_reminder():
    data = TemplateData(
        name="小雅", reminder="防曬乳帶好", reminder_en="Bring sunscreen", bilingual=True,
    )
    result = render_template(data, morning_msg="加油！")
    assert "Bring sunscreen" in result
    assert "Reminder" in result

def test_bilingual_false_no_english():
    data = TemplateData(
        name="小雅", name_en="Xiaoya",
        todos=["買票"], todos_en=["Buy tickets"],
        bilingual=False,
    )
    result = render_template(data, morning_msg="加油！")
    assert "Xiaoya" not in result
    assert "Buy tickets" not in result

def test_todos_en_shorter_than_todos():
    """todos_en 少於 todos 時，缺少的項目不應 crash"""
    data = TemplateData(
        name="小雅",
        todos=["A", "B", "C"],
        todos_en=["a"],
        bilingual=True,
    )
    result = render_template(data, morning_msg="加油！")
    assert "A" in result and "B" in result and "C" in result


# ── to_context_block ──────────────────────────────────────────

def test_context_block_contains_name():
    data = TemplateData(name="阿明")
    block = to_context_block(data)
    assert "阿明" in block

def test_context_block_contains_schedule():
    data = TemplateData(
        name="阿明",
        schedule=[ScheduleItem("09:00", "法院開庭", title_en="Court Hearing")],
    )
    block = to_context_block(data)
    assert "法院開庭" in block
    assert "09:00" in block

def test_context_block_bilingual_schedule():
    data = TemplateData(
        name="阿明",
        schedule=[ScheduleItem("09:00", "法院開庭", title_en="Court Hearing")],
    )
    block = to_context_block(data)
    assert "Court Hearing" in block

def test_context_block_todos():
    data = TemplateData(name="阿明", todos=["準備起訴狀"], todos_en=["Prepare indictment"])
    block = to_context_block(data)
    assert "準備起訴狀" in block
    assert "Prepare indictment" in block

def test_context_block_reminder():
    data = TemplateData(name="阿明", reminder="記得帶印章", reminder_en="Bring seal")
    block = to_context_block(data)
    assert "記得帶印章" in block
    assert "Bring seal" in block

def test_context_block_empty_fields_no_crash():
    data = TemplateData(name="小明")
    block = to_context_block(data)
    assert "小明" in block
    assert "行程" not in block
    assert "待辦" not in block


# ── backward-compat aliases ───────────────────────────────────

def test_backward_compat_alias():
    data = RedSlipData(name="舊名測試")
    result = render_red_slip(data, morning_msg="加油！")
    assert "舊名測試" in result


# ── 早晨訊息輪替 ─────────────────────────────────────────────

def test_morning_msgs_rotate():
    seen = set()
    for _ in range(len(MORNING_MSGS)):
        seen.add(next_morning_msg())
    assert len(seen) == len(MORNING_MSGS), "輪替庫應覆蓋所有句子"

def test_morning_msgs_cycle():
    first = next_morning_msg()
    for _ in range(len(MORNING_MSGS) - 1):
        next_morning_msg()
    cycled = next_morning_msg()
    assert first == cycled, "應循環回第一句"
