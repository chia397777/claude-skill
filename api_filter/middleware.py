"""
FastAPI 整合：三層過濾 + 紅單引擎 + 升級判斷 + Prompt Caching + 分級模型

── 快速接入 ─────────────────────────────────────────────────────
    from fastapi import FastAPI
    from api_filter.middleware import router as filter_router

    app = FastAPI()
    app.include_router(filter_router)

環境變數：
    ANTHROPIC_API_KEY=sk-ant-...
    GOOGLE_MAPS_API_KEY=（可選，有則回傳可讀地址）
    LEGAL_SYSTEM_PROMPT=（可選，不設則用內建 fallback）

端點一覽：
    POST /chat                    一般對話（含三層過濾 + 升級判斷）
    POST /morning                 生成今日紅單（純離線，成本 $0）
    POST /location/detect         依 GPS 自動偵測位置並載入對應離線包
    DELETE /chat/{sid}/history    清除對話歷史
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
from .red_slip.template import RedSlipData, ScheduleItem, render_red_slip
from .red_slip.escalation import check_escalation, EscalationResult, ESCALATION_BRIDGE
from .location.detector import detect_from_coordinates, auto_load_packs, LocationContext

router = APIRouter(tags=["chat"])

# ── Anthropic Client（單例）──────────────────────────────────
_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY 環境變數未設定")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


# ── System Prompt + Prompt Caching ──────────────────────────
_DEFAULT_SYSTEM = """你是法寶貝，一位專業的台灣法律諮詢助理。
以雙專業角色（法學教授＋律師）交叉分析使用者的法律問題。
論證框架採 IRAC（Issue → Rule → Application → Conclusion）。
引用法條時請確認正確性，並標示出處。
回答時使用繁體中文，語氣親切專業。"""


def _get_system_prompt() -> str:
    return os.environ.get("LEGAL_SYSTEM_PROMPT", _DEFAULT_SYSTEM)


def _build_cached_system(prompt_text: str) -> list[dict]:
    """加上 cache_control，system prompt 首次後快取 5 分鐘，節省 ~85% input token。"""
    return [{"type": "text", "text": prompt_text, "cache_control": {"type": "ephemeral"}}]


# ── 對話歷史（in-memory；production 換 Redis）───────────────
_histories: dict[str, Deque[dict]] = {}
MAX_TURNS = 10  # 保留最近 N 輪（1 輪 = user + assistant）


def _get_history(session_id: str) -> list[dict]:
    return list(_histories.get(session_id, []))


def _append_history(session_id: str, role: str, content: str) -> None:
    if session_id not in _histories:
        _histories[session_id] = deque(maxlen=MAX_TURNS * 2)
    _histories[session_id].append({"role": role, "content": content})


# ════════════════════════════════════════════════════════════
#  Schema
# ════════════════════════════════════════════════════════════

class ScheduleItemIn(BaseModel):
    time: str = Field(..., example="09:00")
    title: str = Field(..., example="週會")


class MorningRequest(BaseModel):
    """生成紅單所需資料（全由 Flutter App 本地提供，無需 API）"""
    name: str = Field(..., example="小明")
    weather: str = Field(default="", example="晴天 28°C")
    schedule: list[ScheduleItemIn] = Field(default_factory=list)
    todos: list[str] = Field(default_factory=list)
    reminder: str = Field(default="", example="記得吃藥 💊")
    session_id: str = Field(default="default", max_length=64)


class MorningResponse(BaseModel):
    red_slip: str
    session_id: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default="default", max_length=64)


class ChatResponse(BaseModel):
    reply: str
    filtered: bool
    escalated: bool
    escalation_reason: str   # "none" | "repetition" | "emotion"
    layer: str
    model_used: str | None
    latency_ms: float
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


class LocationRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="緯度")
    lng: float = Field(..., ge=-180, le=180, description="經度")
    session_id: str = Field(default="default", max_length=64)
    auto_load: bool = Field(default=True, description="是否自動載入偵測到的離線包")


class LocationResponse(BaseModel):
    matched_label: str          # 比對到的地點名稱（空字串代表不在已知範圍）
    suggested_packs: list[str]  # 建議載入的 pack_id 清單
    loaded_packs: list[str]     # 本次實際載入的 pack_id（已載入者不重複計）
    geocoded_address: str       # Google Geocoding 回傳的可讀地址（需 API Key）


# ════════════════════════════════════════════════════════════
#  端點一：POST /morning  生成今日紅單（純離線）
# ════════════════════════════════════════════════════════════

@router.post("/morning", response_model=MorningResponse)
async def morning_endpoint(req: MorningRequest) -> MorningResponse:
    data = RedSlipData(
        name=req.name,
        weather=req.weather,
        schedule=[ScheduleItem(time=i.time, title=i.title) for i in req.schedule],
        todos=req.todos,
        reminder=req.reminder,
    )
    slip = render_red_slip(data)

    # 把紅單存入對話歷史，讓後續 /chat 能感知今天的脈絡
    _append_history(req.session_id, "assistant", slip)

    return MorningResponse(red_slip=slip, session_id=req.session_id)


# ════════════════════════════════════════════════════════════
#  端點二：POST /chat  對話（含過濾 + 升級判斷）
# ════════════════════════════════════════════════════════════

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:

    # ── Layer 1 & 2：靜態過濾（問候 / 閒聊 / 非法律）─────
    result: FilterResult = pre_filter(req.message)

    if result.blocked:
        return ChatResponse(
            reply=result.reply,
            filtered=True,
            escalated=False,
            escalation_reason="none",
            layer=result.layer,
            model_used=None,
            latency_ms=result.latency_ms,
        )

    # ── Layer 1.5：升級判斷（重複 / 情緒升溫）───────────
    history = _get_history(req.session_id)
    escalation: EscalationResult = check_escalation(req.message, history)

    # ── 決定模型 ──────────────────────────────────────────
    intent = classify_intent(req.message)
    if escalation.should_escalate:
        # 升級：至少用 Sonnet，複雜問題維持 Opus
        model = "claude-opus-4-8" if intent.model == "claude-opus-4-8" else "claude-sonnet-5"
    else:
        model = intent.model

    # ── 組裝訊息（升級時加過渡提示進 context）────────────
    messages = list(history)
    user_content = req.message
    if escalation.should_escalate:
        # 在 assistant 位置插入過渡橋接句，讓使用者感受到重視
        messages.append({"role": "assistant", "content": ESCALATION_BRIDGE})
    messages.append({"role": "user", "content": user_content})

    # ── Layer 3：呼叫 Claude API ──────────────────────────
    try:
        client = _get_client()
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=_build_cached_system(_get_system_prompt()),
            messages=messages,
        )
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude API 錯誤：{e}")

    reply_text = response.content[0].text

    # 寫入歷史（不含橋接句，保持歷史乾淨）
    _append_history(req.session_id, "user", req.message)
    _append_history(req.session_id, "assistant", reply_text)

    usage = response.usage
    return ChatResponse(
        reply=reply_text,
        filtered=False,
        escalated=escalation.should_escalate,
        escalation_reason=escalation.reason,
        layer=result.layer,
        model_used=model,
        latency_ms=result.latency_ms,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        cache_write_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
    )


# ════════════════════════════════════════════════════════════
#  端點三：POST /location/detect  GPS 自動偵測並載入離線包
# ════════════════════════════════════════════════════════════

@router.post("/location/detect", response_model=LocationResponse)
async def location_detect(req: LocationRequest) -> LocationResponse:
    """
    前端傳入 GPS 座標，後端：
      1. 以 bbox 規則判斷使用者位置（機場 / 高雄 / 台南 / 屏東 / 台東…）
      2. 自動載入對應的離線對話包（若 auto_load=True）
      3. 可選呼叫 Google Geocoding API 取得可讀地址（需 GOOGLE_MAPS_API_KEY）

    前端在 App 啟動或使用者授予定位權限後呼叫一次即可。
    """
    from api_filter.offline_packs.loader import load_pack, is_loaded

    google_api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    ctx: LocationContext = detect_from_coordinates(req.lat, req.lng, google_api_key or None)

    loaded: list[str] = []
    if req.auto_load:
        for pack_id in ctx.suggested_packs:
            if not is_loaded(pack_id):
                try:
                    load_pack(pack_id)
                    loaded.append(pack_id)
                except FileNotFoundError:
                    pass

    return LocationResponse(
        matched_label=ctx.matched_label,
        suggested_packs=ctx.suggested_packs,
        loaded_packs=loaded,
        geocoded_address=ctx.geocoded_address,
    )


# ════════════════════════════════════════════════════════════
#  端點四：DELETE /chat/{session_id}/history  清除歷史
# ════════════════════════════════════════════════════════════

@router.delete("/chat/{session_id}/history")
async def clear_history(session_id: str) -> dict:
    _histories.pop(session_id, None)
    return {"cleared": True, "session_id": session_id}
