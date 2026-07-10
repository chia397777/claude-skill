"""
第一層：本地規則過濾
命中 → 直接回罐頭訊息，成本 0
"""
import re
import random

# 問候語模式（正則）
GREETING_PATTERNS = [
    r"^(你好|您好|哈囉|嗨|hi|hello|hey|嘿)[!！。~～\s]*$",
    r"^(早安|午安|晚安|早上好|下午好|晚上好)[!！。~～\s]*$",
    r"^(謝謝|感謝|多謝|thank you|thanks)[你您妳!！。~～\s]*$",
    r"^(掰掰|再見|拜拜|bye|goodbye|晚安)[!！。~～\s]*$",
    r"^(好的|好|OK|ok|okay|okey|ㄅ)[!！。~～\s]*$",
    r"^(哈+|呵+|XD|xd|😄|😊|🙏)+[\s]*$",
]

# 法律相關關鍵字（有這些就不攔）
LEGAL_KEYWORDS = [
    # 訴訟程序
    "訴訟", "起訴", "上訴", "答辯", "聲請", "抗告", "再審", "聲明異議",
    "開庭", "庭期", "法院", "法官", "檢察官", "律師", "辯護", "公設辯護人",
    # 民事
    "合約", "契約", "違約", "損害賠償", "侵權", "不當得利", "撤銷",
    "終止", "解除", "租賃", "買賣", "借貸", "票據", "本票", "支票",
    "強制執行", "假扣押", "假處分", "拍賣", "查封",
    # 刑事
    "刑事", "犯罪", "詐欺", "竊盜", "傷害", "恐嚇", "妨礙", "誹謗",
    "公訴", "自訴", "羈押", "交保", "緩刑", "假釋", "拘提", "逮捕",
    # 行政
    "行政訴訟", "訴願", "撤銷處分", "罰鍰", "吊銷", "廢止", "核准",
    # 法律文件
    "判決", "裁定", "書狀", "起訴書", "答辯狀", "上訴狀", "聲明書",
    "公證", "認證", "法條", "法規", "條文", "第.*條", "民法", "刑法",
    "勞基法", "消保法", "公司法", "土地法", "建築法",
    # 權利義務
    "權利", "義務", "賠償", "責任", "債務", "債權", "抵押", "擔保",
    "繼承", "遺囑", "遺產", "監護", "扶養", "離婚", "贍養費", "子女監護",
    # 一般法律用語
    "法律", "法令", "規定", "違法", "合法", "罰款", "告訴", "告發",
    "被告", "原告", "被害人", "證人", "證據", "鑑定",
]

# 問候語罐頭回覆庫（輪流使用避免生硬）
GREETING_REPLIES = [
    "您好！我是法寶貝，專門協助您處理法律相關問題。請問有什麼法律問題需要諮詢嗎？",
    "嗨！有任何法律疑問都可以告訴我，例如合約問題、訴訟程序、權益保障等，我很樂意幫忙！",
    "您好！請直接說明您的法律問題，我會盡力為您提供協助。",
]

THANKS_REPLIES = [
    "不客氣！如果還有其他法律問題，隨時可以問我。",
    "很高興能幫上忙！有任何法律疑問都歡迎繼續提問。",
    "不用謝！法律問題就交給法寶貝，祝您一切順利。",
]

GOODBYE_REPLIES = [
    "再見！有法律問題記得回來找我。",
    "掰掰！祝您訴訟順利、平安喜樂。",
    "再見！法寶貝隨時在這裡等您。",
]

OK_REPLIES = [
    "好的，請繼續說明您的問題，我在聆聽。",
    "了解！請問還有什麼法律問題需要協助嗎？",
]

_reply_index: dict[str, int] = {}


def _pick_reply(category: str, replies: list[str]) -> str:
    idx = _reply_index.get(category, 0)
    reply = replies[idx % len(replies)]
    _reply_index[category] = idx + 1
    return reply


def _contains_legal_keyword(text: str) -> bool:
    for kw in LEGAL_KEYWORDS:
        if re.search(kw, text):
            return True
    return False


def check_greeting(text: str) -> str | None:
    """
    回傳罐頭訊息字串，或 None（代表不是問候語，繼續往下處理）。
    """
    stripped = text.strip()

    # 太短且沒有法律關鍵字 → 先檢查是否為問候語
    if len(stripped) <= 15 and not _contains_legal_keyword(stripped):
        lower = stripped.lower()

        # 道別
        if re.search(r"掰掰|再見|拜拜|bye|goodbye", lower):
            return _pick_reply("goodbye", GOODBYE_REPLIES)

        # 感謝
        if re.search(r"謝謝|感謝|多謝|thank", lower):
            return _pick_reply("thanks", THANKS_REPLIES)

        # OK 類
        if re.search(r"^(好的?|OK|ok|okay|okey|ㄅ)[!！。~～\s]*$", stripped):
            return _pick_reply("ok", OK_REPLIES)

        # 問候語正則比對
        for pattern in GREETING_PATTERNS:
            if re.match(pattern, stripped, re.IGNORECASE):
                return _pick_reply("greeting", GREETING_REPLIES)

    return None
