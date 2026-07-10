"""
FastAPI 整合：三層過濾 + Prompt Caching + 分級模型

── 快速接入 ─────────────────────────────────────────────────────
在你的 main.py：

    from fastapi import FastAPI
    from api_filter.middleware import router as filter_router

    app = FastAPI()
    app.include_router(filter_router)

環境變數需設定：
    ANTHROPIC_API_KEY=sk-ant-...
    LEGAL_SYSTEM_PROMPT=（你的法律知識庫 system prompt，可從檔案讀取）
"""
from __future__ import annotations

import os
from collections import deque
from typing import Deque

import anthropic
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .filter import pre_filter, FilterResult
from .intent import classify_intent

router = APIRouter(prefix="/chat", tags=["chat"])

# ── Anthropic Client（單例，跨 request 共用 TCP 連線）─────────
_client: anthropic.Anthropic | None = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY 環境變數未設定")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


# ── System Prompt（附 cache_control，首次後快取 5 分鐘）──────
def _build_system(prompt_text: str) -> list[dict]:
    return [
        {
            "type": "text",
            "text": prompt_text,
            "cache_control": {"type": "ephemeral"},
        }
    ]


# ── 對話歷史（in-memory，production 請換 Redis）─────────────
# session_id → deque of {"role": ..., "content": ...}
_histories: dict[str, Deque[dict]] = {}
MAX_HISTORY_TURNS = 10  # 保留最近 N 輪（1 輪 = user + assistant）


def _get_history(session_id: str) -> list[dict]:
    return list(_histories.get(session_id, []))


def _append_history(session_id: str, role: str, content: str) -> None:
    if session_id not in _histories:
        _histories[session_id] = deque(maxlen=MAX_HISTORY_TURNS * 2)
    _histories[session_id].append({"role": role, "content": content})


# ── 預設 Legal System Prompt（沒有設環境變數時的 fallback）──
_DEFAULT_SYSTEM = """你是法寶貝，一位專業的台灣法律諮詢助理。
以雙專業角色（法學教授＋律師）交叉分析使用者的法律問題。
論證框架採 IRAC（Issue → Rule → Application → Conclusion）。
引用法條時請確認正確性，並標示出處。
回答時使用繁體中文，語氣親切專業。"""


def _get_system_prompt() -> str:
    return os.environ.get("LEGAL_SYSTEM_PROMPT", _DEFAULT_SYSTEM)


# ── Request / Response Schema ────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default="default", max_length=64)


class ChatResponse(BaseModel):
    reply: str
    filtered: bool
    layer: str
    model_used: str | None
    latency_ms: float
    # 快取命中資訊（方便 debug，production 可移除）
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


# ── 主 Endpoint ──────────────────────────────────────────────
@router.post("", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:

    # ── 三層過濾 ─────────────────────────────────────────────
    result: FilterResult = pre_filter(req.message)

    if result.blocked:
        return ChatResponse(
            reply=result.reply,
            filtered=True,
            layer=result.layer,
            model_used=None,
            latency_ms=result.latency_ms,
        )

    # ── 取得意圖分析（含分級 model）─────────────────────────
    intent = classify_intent(req.message)

    # ── 組裝對話歷史 ──────────────────────────────────────────
    history = _get_history(req.session_id)
    history.append({"role": "user", "content": req.message})

    # ── 呼叫 Claude API（含 prompt caching）──────────────────
    try:
        client = _get_client()
        response = client.messages.create(
            model=intent.model,
            max_tokens=2048,
            system=_build_system(_get_system_prompt()),
            messages=history,
        )
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude API 錯誤：{e}")

    reply_text = response.content[0].text

    # 記錄對話歷史
    _append_history(req.session_id, "user", req.message)
    _append_history(req.session_id, "assistant", reply_text)

    # 快取 token 使用量（可寫 log / metrics）
    usage = response.usage
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0

    return ChatResponse(
        reply=reply_text,
        filtered=False,
        layer=result.layer,
        model_used=intent.model,
        latency_ms=result.latency_ms,
        cache_read_tokens=cache_read,
        cache_write_tokens=cache_write,
    )


# ── 清除對話歷史（讓使用者可以「重新開始」）────────────────
@router.delete("/{session_id}/history")
async def clear_history(session_id: str) -> dict:
    _histories.pop(session_id, None)
    return {"cleared": True, "session_id": session_id}
