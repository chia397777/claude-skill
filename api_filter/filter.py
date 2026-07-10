"""
三層過濾主入口
使用方式：
    result = pre_filter(user_message)
    if result.blocked:
        return result.reply   # 直接回，不呼叫 API
    else:
        # 正常呼叫 Claude API
        call_claude(user_message)
"""
import logging
import time
from dataclasses import dataclass

from .rules import check_greeting
from .intent import classify_intent, NON_LEGAL_REPLY

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    blocked: bool
    reply: str | None
    layer: str         # "layer1_greeting" / "layer2_intent" / "pass"
    latency_ms: float


def pre_filter(text: str) -> FilterResult:
    t0 = time.perf_counter()

    # ── 第一層：問候語快速攔截 ──────────────────────────────
    greeting_reply = check_greeting(text)
    if greeting_reply:
        ms = (time.perf_counter() - t0) * 1000
        logger.info("layer1_block | %.1fms | text=%r", ms, text[:40])
        return FilterResult(
            blocked=True,
            reply=greeting_reply,
            layer="layer1_greeting",
            latency_ms=ms,
        )

    # ── 第二層：意圖分類 ────────────────────────────────────
    intent = classify_intent(text)
    ms = (time.perf_counter() - t0) * 1000

    if not intent.is_legal:
        logger.info(
            "layer2_block | %.1fms | score=%.1f | reason=%s | text=%r",
            ms, intent.score, intent.reason, text[:40],
        )
        return FilterResult(
            blocked=True,
            reply=NON_LEGAL_REPLY,
            layer="layer2_intent",
            latency_ms=ms,
        )

    # ── 第三層：放行，交給 Claude API ───────────────────────
    logger.info(
        "layer3_pass | %.1fms | score=%.1f | reason=%s | text=%r",
        ms, intent.score, intent.reason, text[:40],
    )
    return FilterResult(
        blocked=False,
        reply=None,
        layer="pass",
        latency_ms=ms,
    )
