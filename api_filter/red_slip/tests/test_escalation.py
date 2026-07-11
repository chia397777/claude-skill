"""
pytest api_filter/red_slip/tests/test_escalation.py -v
"""
import pytest
from api_filter.red_slip.escalation import check_escalation


def _hist(*user_msgs: str) -> list[dict]:
    """快速建立只有 user 訊息的歷史。"""
    return [{"role": "user", "content": m} for m in user_msgs]


# ── 情緒升溫應升級 ────────────────────────────────────────────
@pytest.mark.parametrize("msg", [
    "我肚子一直在痛",
    "好幾天了怎麼辦",
    "崩潰了不知道怎麼辦",
    "很嚴重，緊急",
    "幫幫我，我受不了了",
    "心好累，快撐不住了",
    "收到傳票被告了",
])
def test_emotion_triggers_escalation(msg):
    r = check_escalation(msg, [])
    assert r.should_escalate, f"情緒訊號應觸發升級：{msg!r}"
    assert r.reason == "emotion"
    assert r.score == 1.0


# ── 語意重複應升級 ────────────────────────────────────────────
@pytest.mark.parametrize("history_msg,current_msg", [
    ("我的房東不退押金", "房東一直不退押金"),
    ("合約被違約了怎麼辦", "合約違約我該怎麼辦"),
    ("被詐欺了要怎麼報案", "詐欺的報案流程是什麼"),
])
def test_repetition_triggers_escalation(history_msg, current_msg):
    r = check_escalation(current_msg, _hist(history_msg))
    assert r.should_escalate, f"語意重複應觸發升級\n  歷史：{history_msg!r}\n  當前：{current_msg!r}"
    assert r.reason in ("repetition", "emotion"), f"應為 repetition 或 emotion，實際：{r.reason}"


# ── 無關訊息不應升級 ──────────────────────────────────────────
@pytest.mark.parametrize("msg", [
    "我想了解勞基法的規定",
    "合約上的違約金條款合法嗎",
    "離婚後子女監護權如何爭取",
])
def test_normal_legal_no_escalation(msg):
    r = check_escalation(msg, [])
    assert not r.should_escalate, f"普通法律問題不應升級：{msg!r}"
    assert r.reason == "none"


# ── 不同主題不視為重複 ────────────────────────────────────────
def test_different_topics_no_repetition():
    r = check_escalation(
        "離婚監護權怎麼爭取",
        _hist("我想申請公司登記"),
    )
    assert not r.should_escalate or r.reason == "emotion"


# ── 重複偵測回看範圍（只看最近 4 條）──────────────────────────
def test_repetition_lookback_limit():
    old_msgs = ["房東不退押金"] * 10   # 超過 lookback 的舊訊息
    recent_msgs = ["今天天氣真好"] * 4  # 最近 4 條不相關
    history = _hist(*old_msgs, *recent_msgs)
    r = check_escalation("房東不退押金", history)
    # 最近 4 條不相關，即使更早有相同訊息也不應升級
    assert not r.should_escalate, "應只看最近 4 條，不應被更早的歷史觸發"
