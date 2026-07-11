"""
紅單模板引擎：填空帶入，純本地渲染，成本 $0
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .messages import next_morning_msg

WEEKDAYS = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]


@dataclass
class ScheduleItem:
    time: str   # "09:00"
    title: str  # "週會"


@dataclass
class RedSlipData:
    name: str
    weather: str = ""
    schedule: list[ScheduleItem] = field(default_factory=list)
    todos: list[str] = field(default_factory=list)
    reminder: str = ""

    @property
    def date_str(self) -> str:
        today = date.today()
        return f"{today.month}月{today.day}日"

    @property
    def weekday_str(self) -> str:
        return WEEKDAYS[date.today().weekday()]


def render_red_slip(data: RedSlipData, morning_msg: str | None = None) -> str:
    """
    將 RedSlipData 渲染成純文字紅單。
    morning_msg 若不傳入則自動從輪替庫取下一句。
    """
    msg = morning_msg if morning_msg is not None else next_morning_msg()
    lines: list[str] = []

    # ── 標頭 ──────────────────────────────────────────────
    weather_part = f"，{data.weather}" if data.weather else ""
    lines.append(f"早安，{data.name}！")
    lines.append(f"今天是 {data.date_str} {data.weekday_str}{weather_part}。")
    lines.append(f"\n{msg}")

    # ── 行程 ──────────────────────────────────────────────
    if data.schedule:
        lines.append("\n📋 今日行程")
        for item in data.schedule:
            lines.append(f"  {item.time}　{item.title}")

    # ── 待辦 ──────────────────────────────────────────────
    if data.todos:
        lines.append("\n✅ 待辦事項")
        for todo in data.todos:
            lines.append(f"  • {todo}")

    # ── 固定提醒 ──────────────────────────────────────────
    if data.reminder:
        lines.append(f"\n💊 提醒：{data.reminder}")

    lines.append("\n有什麼需要我幫忙的嗎？")

    return "\n".join(lines)
