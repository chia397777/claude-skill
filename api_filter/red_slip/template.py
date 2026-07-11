"""
表格化模版引擎：填空帶入，純本地渲染，成本 $0
支援雙語輸出（bilingual=True）與 to_context_block() 注入 system prompt
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .messages import next_morning_msg

WEEKDAYS_ZH = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
WEEKDAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

_LINE = "═" * 52


@dataclass
class ScheduleItem:
    time: str
    title: str
    title_en: str = ""


@dataclass
class TemplateData:
    name: str
    name_en: str = ""
    weather: str = ""
    weather_en: str = ""
    schedule: list[ScheduleItem] = field(default_factory=list)
    todos: list[str] = field(default_factory=list)
    todos_en: list[str] = field(default_factory=list)
    reminder: str = ""
    reminder_en: str = ""
    bilingual: bool = False

    @property
    def date_str(self) -> str:
        t = date.today()
        return f"{t.month}月{t.day}日"

    @property
    def weekday_str(self) -> str:
        return WEEKDAYS_ZH[date.today().weekday()]

    @property
    def date_str_en(self) -> str:
        return date.today().strftime("%a, %b %-d")


# ── backward-compat alias ────────────────────────────────────
RedSlipData = TemplateData


def _sec(zh: str, en: str = "") -> str:
    label = f" {zh}" + (f" / {en}" if en else "")
    return f"╠══{label}"


def render_template(data: TemplateData, morning_msg: str | None = None) -> str:
    """渲染表格化模版，bilingual=True 時每個欄位顯示雙語。"""
    msg = morning_msg if morning_msg is not None else next_morning_msg()
    bi = data.bilingual
    rows: list[str] = []

    # ── 頂框 ──────────────────────────────────────────────────
    rows.append(f"╔{_LINE}╗")

    # ── 標頭 ──────────────────────────────────────────────────
    name_line = f"早安，{data.name}！"
    if bi and data.name_en:
        name_line += f"  Good morning, {data.name_en}!"
    rows.append(f"║  {name_line}")

    date_line = f"{data.date_str} {data.weekday_str}"
    if bi:
        date_line += f" · {data.date_str_en}"
    if data.weather:
        date_line += f" · {data.weather}"
        if bi and data.weather_en:
            date_line += f" / {data.weather_en}"
    rows.append(f"║  {date_line}")

    msg_line = msg
    if bi:
        msg_line += "  Have a great day!"
    rows.append(f"║  {msg_line}")

    # ── 行程 ──────────────────────────────────────────────────
    if data.schedule:
        rows.append(_sec("📋 今日行程", "Today's Schedule" if bi else ""))
        for item in data.schedule:
            rows.append(f"║  {item.time}  {item.title}")
            if bi and item.title_en:
                rows.append(f"║        {item.title_en}")

    # ── 待辦 ──────────────────────────────────────────────────
    if data.todos:
        rows.append(_sec("✅ 待辦事項", "To-Do List" if bi else ""))
        for i, todo in enumerate(data.todos):
            en = data.todos_en[i] if i < len(data.todos_en) else ""
            suffix = f" / {en}" if (bi and en) else ""
            rows.append(f"║  • {todo}{suffix}")

    # ── 提醒 ──────────────────────────────────────────────────
    if data.reminder:
        rows.append(_sec("💊 提醒", "Reminder" if bi else ""))
        reminder_line = data.reminder
        if bi and data.reminder_en:
            reminder_line += f" / {data.reminder_en}"
        rows.append(f"║  {reminder_line}")

    # ── 底框 ──────────────────────────────────────────────────
    rows.append(f"╚{_LINE}╝")

    closing = "有什麼需要我幫忙的嗎？"
    if bi:
        closing += "  What can I help you with?"
    rows.append(f"  {closing}")

    return "\n".join(rows)


# backward-compat alias
render_red_slip = render_template


def to_context_block(data: TemplateData) -> str:
    """
    將 TemplateData 序列化為結構化文字區塊，注入 system prompt，
    讓 Claude 知道今天這個用戶的行程與待辦脈絡。
    """
    lines = ["── 今日用戶脈絡 (User Context) ──────────────"]
    name = data.name + (f" ({data.name_en})" if data.name_en else "")
    lines.append(f"用戶: {name}")
    lines.append(f"日期: {data.date_str} {data.weekday_str}")
    if data.weather:
        w = data.weather + (f" / {data.weather_en}" if data.weather_en else "")
        lines.append(f"天氣: {w}")
    if data.schedule:
        lines.append("行程:")
        for item in data.schedule:
            t = item.title + (f" ({item.title_en})" if item.title_en else "")
            lines.append(f"  {item.time}  {t}")
    if data.todos:
        lines.append("待辦:")
        for i, todo in enumerate(data.todos):
            en = data.todos_en[i] if i < len(data.todos_en) else ""
            t = todo + (f" ({en})" if en else "")
            lines.append(f"  • {t}")
    if data.reminder:
        r = data.reminder + (f" ({data.reminder_en})" if data.reminder_en else "")
        lines.append(f"提醒: {r}")
    lines.append("─────────────────────────────────────────────")
    return "\n".join(lines)
