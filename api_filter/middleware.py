"""
FastAPI 整合範例

── 使用方式 ──────────────────────────────────────────────────────
在你的 main.py：

    from fastapi import FastAPI
    from api_filter.middleware import router as filter_router

    app = FastAPI()
    app.include_router(filter_router)

或直接使用 pre_filter() 函式嵌入現有的 /chat endpoint：

    from api_filter.filter import pre_filter

    @app.post("/chat")
    async def chat(req: ChatRequest):
        result = pre_filter(req.message)
        if result.blocked:
            return {"reply": result.reply, "filtered": True}
        # 呼叫 Claude API ...
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .filter import pre_filter, FilterResult

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    filtered: bool
    layer: str
    latency_ms: float


@router.post("", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:
    # ── 三層過濾 ──────────────────────────────────────────
    result: FilterResult = pre_filter(req.message)

    if result.blocked:
        return ChatResponse(
            reply=result.reply,
            filtered=True,
            layer=result.layer,
            latency_ms=result.latency_ms,
        )

    # ── 放行：呼叫 Claude API ──────────────────────────────
    # 在此替換成你實際的 Claude API 呼叫邏輯
    # 例如：
    #   import anthropic
    #   client = anthropic.Anthropic()
    #   response = client.messages.create(
    #       model="claude-sonnet-5",
    #       max_tokens=2048,
    #       system=LEGAL_SYSTEM_PROMPT,   # 帶入法律知識庫 system prompt
    #       messages=[{"role": "user", "content": req.message}],
    #   )
    #   reply_text = response.content[0].text
    reply_text = "[Claude API 回覆放這裡]"

    return ChatResponse(
        reply=reply_text,
        filtered=False,
        layer=result.layer,
        latency_ms=result.latency_ms,
    )
