"""
四層過濾主入口

  Layer 1   : 問候語快速攔截（離線，成本 $0）
  Layer 1.5 : 離線對話包比對（機場/計程車/飯店/景點，成本 $0）
  Layer 2   : 意圖分類（非法律/閒聊攔截）
  Layer 3   : 放行，呼叫 Claude API

使用方式：
    from api_filter.offline_packs.loader import load_pack
    load_pack("airport_travel")          # 啟動時載入一次

    result = pre_filter(user_message)
    if result.blocked:
        return result.reply
    else:
        call_claude(user_message)
"""
import logging
import time
from dataclasses import dataclass

from .rules import check_greeting
from .intent import classify_intent, NON_LEGAL_REPLY
from .offline_packs.loader import match_offline

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    blocked: bool
    reply: str | None
    layer: str       # layer1_greeting / layer1_5_offline_pack / layer2_intent / pass
    latency_ms: float


def pre_filter(text: str) -> FilterResult:
    t0 = time.perf_counter()

    # ── Layer 1：問候語快速攔截 ──────────────────────────────
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

    # ── Layer 1.5：離線對話包比對 ─────────────────────────────
    pack_match = match_offline(text)
    if pack_match:
        ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "layer1_5_block | %.1fms | pack=%s | scenario=%s | text=%r",
            ms, pack_match.pack_id, pack_match.scenario_id, text[:40],
        )
        return FilterResult(
            blocked=True,
            reply=pack_match.response,
            layer="layer1_5_offline_pack",
            latency_ms=ms,
        )

    # ── Layer 2：意圖分類 ─────────────────────────────────────
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

    # ── Layer 3：放行，呼叫 Claude API ───────────────────────
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
