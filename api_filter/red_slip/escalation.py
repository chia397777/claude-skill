"""
升級判斷：偵測重複訴說 + 情緒升溫，決定是否從離線模式切換到雲端 API。

兩個觸發條件（任一成立即升級）：
  1. 語意重複：當前訊息與近期使用者訊息 bigram Jaccard 相似度 ≥ 0.45
  2. 情緒升溫：訊息含有明確求助 / 焦慮 / 緊迫詞
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 情緒升溫 / 求助訊號詞
EMOTION_SIGNALS: list[str] = [
    # 時間急迫
    "一直", "好幾天", "已經很久", "持續", "反覆", "每次都",
    # 求助
    "怎麼辦", "幫幫我", "救我", "不知道怎麼", "沒辦法了",
    # 情緒崩潰
    "崩潰", "好煩", "受不了", "很痛苦", "快撐不住", "很絕望",
    "很害怕", "好擔心", "壓力很大", "心好累", "身心俱疲",
    # 嚴重程度
    "很嚴重", "非常嚴重", "緊急", "很急", "馬上", "立刻",
    # 法律情境特有
    "被告了", "收到傳票", "被抓走", "要坐牢", "要被強制執行",
]

# 常見功能詞（比對時濾掉）
_FUNC_CHARS: frozenset[str] = frozenset(
    "的了嗎我你他她它是在有也都就很不吧呢啊哦嗯好喔唉哈呵"
    "，。？！、…～—「」『』【】《》：；（）"
    " \t\n\r"
)

REPETITION_THRESHOLD = 0.45  # Jaccard 相似度門檻
HISTORY_LOOKBACK = 4          # 往回看幾條使用者訊息


@dataclass
class EscalationResult:
    should_escalate: bool
    reason: str    # "emotion" | "repetition" | "none"
    score: float   # 相似度或 1.0（emotion）


def _extract_bigrams(text: str) -> set[str]:
    """去除功能字後取 2-gram，用於語意相似度比對。"""
    clean = "".join(c for c in text if c not in _FUNC_CHARS)
    return {clean[i:i+2] for i in range(len(clean) - 1)} if len(clean) >= 2 else set()


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


KEYWORD_OVERLAP_MIN = 3  # 至少共同幾個實詞字就算重複


def _extract_content_chars(text: str) -> set[str]:
    """提取所有非功能字的單字，用於關鍵詞重疊比對。"""
    return {c for c in text if c not in _FUNC_CHARS and not c.isascii()}


def check_escalation(
    current_msg: str,
    history: list[dict],  # [{"role": "user"|"assistant", "content": str}, ...]
) -> EscalationResult:
    """
    呼叫時機：pre_filter 放行之後、送 Claude API 之前。

    Parameters
    ----------
    current_msg : 使用者這一輪的輸入
    history     : 完整對話歷史（middleware 的 _get_history 回傳值）
    """
    # ── 1. 情緒升溫偵測（優先，立刻升級）───────────────────
    for signal in EMOTION_SIGNALS:
        if signal in current_msg:
            return EscalationResult(
                should_escalate=True,
                reason="emotion",
                score=1.0,
            )

    # ── 2. 語意重複偵測 ───────────────────────────────────
    current_bigrams = _extract_bigrams(current_msg)
    current_chars = _extract_content_chars(current_msg)
    past_user_msgs = [
        m["content"] for m in history if m["role"] == "user"
    ][-HISTORY_LOOKBACK:]

    max_sim = 0.0
    max_overlap = 0
    for past in past_user_msgs:
        # bigram Jaccard
        sim = _jaccard(current_bigrams, _extract_bigrams(past))
        if sim > max_sim:
            max_sim = sim
        # 關鍵詞字元重疊（應對換句話說的情況）
        overlap = len(current_chars & _extract_content_chars(past))
        if overlap > max_overlap:
            max_overlap = overlap

    if max_sim >= REPETITION_THRESHOLD or max_overlap >= KEYWORD_OVERLAP_MIN:
        score = max(max_sim, max_overlap / 10)
        return EscalationResult(
            should_escalate=True,
            reason="repetition",
            score=round(score, 3),
        )

    return EscalationResult(should_escalate=False, reason="none", score=0.0)


# 升級時插入對話前的過渡提示（讓使用者感受到 AI 在認真處理）
ESCALATION_BRIDGE = "您說的這件事聽起來需要我仔細想想，讓我深入幫您分析一下..."
