"""
第二層：本地輕量意圖判斷
不需要 LLM，純關鍵字 + 簡易評分，決定是否真的要呼叫 Claude API。
"""
import re
from dataclasses import dataclass

# 高權重法律詞（出現一個就幾乎確定是法律問題）
HIGH_WEIGHT_LEGAL = {
    "訴訟", "起訴", "上訴", "答辯", "判決", "裁定", "聲請", "抗告",
    "假扣押", "假處分", "強制執行", "羈押", "交保", "緩刑",
    "合約", "契約", "違約", "損害賠償", "侵權", "本票", "支票",
    "書狀", "起訴書", "答辯狀", "聲明書", "訴願", "廢止處分",
    "民法", "刑法", "勞基法", "消保法", "公司法", "土地法",
    "詐欺", "竊盜", "傷害", "恐嚇", "誹謗", "妨礙",
    "第.*條", r"\d+條",
}

# 中權重法律詞（需要 2 個以上才觸發）
MED_WEIGHT_LEGAL = {
    "法律", "法規", "法令", "法院", "律師", "法官", "檢察官",
    "權利", "義務", "賠償", "責任", "債務", "債權", "擔保",
    "租賃", "買賣", "借貸", "繼承", "遺囑", "遺產", "離婚",
    "告訴", "告發", "被告", "原告", "證據", "鑑定", "公證",
    "違法", "合法", "罰款", "罰鍰", "吊銷",
    # 租屋相關
    "房東", "房客", "租屋", "押金", "保證金", "租約", "驅逐",
    # 勞動相關
    "薪水", "薪資", "工資", "加班費", "資遣費", "解雇", "開除", "資遣",
    # 申訴報案
    "報案", "申訴", "投訴", "舉報", "檢舉",
    # 財產相關
    "欠錢", "欠債", "欠薪", "追討",
    # 口語法律用語
    "打官司", "官司", "索賠",
}

# 問句指標（有問句代表在詢問，加分）
QUESTION_PATTERNS = [
    r"[？?]",
    r"(怎麼|如何|可以|能不能|有沒有|是否|應該|需要|要怎樣)",
    r"(我該|我能|我可以|我需要|我要)",
]

# 閒聊指標（有這些扣分）
CHIT_CHAT_PATTERNS = [
    r"(今天天氣|天氣好|吃什麼|好吃|好看|推薦|哪裡好玩)",
    r"(電影|音樂|遊戲|運動|旅遊|美食|食譜)",
    r"(你幾歲|你喜歡)",  # 移除 你是誰/你叫什麼：已由 Layer 1 身份詢問攔截
]

MIN_LEGAL_SCORE = 2  # 達到此分數才送 API

# 複雜問題關鍵詞（需要較強模型）
COMPLEX_LEGAL = {
    "書狀", "起訴書", "答辯狀", "上訴狀", "聲明書", "訴願書",
    "IRAC", "論證", "涵攝", "判決分析", "蘇格拉底",
    "強制執行", "假扣押", "假處分", "羈押", "抗告",
}


@dataclass
class IntentResult:
    is_legal: bool
    score: float
    reason: str
    model: str  # 建議使用的 Claude model


def classify_intent(text: str) -> IntentResult:
    """
    回傳 IntentResult。
    is_legal=True → 送 Claude API；False → 回預設「非法律問題」回覆。
    model 欄位依複雜度分級：haiku / sonnet-5 / opus-4-8
    """
    score = 0.0
    reasons = []
    high_hit = False

    # 高權重詞命中
    for kw in HIGH_WEIGHT_LEGAL:
        if re.search(kw, text):
            score += 3
            reasons.append(f"high:{kw}")
            high_hit = True
            break

    # 中權重詞計數
    med_hits = sum(1 for kw in MED_WEIGHT_LEGAL if kw in text)
    if med_hits > 0:
        score += med_hits * 1.5
        reasons.append(f"med_hits:{med_hits}")

    # 問句加分
    for pat in QUESTION_PATTERNS:
        if re.search(pat, text):
            score += 1
            reasons.append("question")
            break

    # 閒聊扣分
    for pat in CHIT_CHAT_PATTERNS:
        if re.search(pat, text):
            score -= 3
            reasons.append("chit_chat")
            break

    # 字數加分（較長的問題通常是認真詢問）
    char_count = len(text.strip())
    if char_count >= 30:
        score += 1
    if char_count >= 80:
        score += 1

    is_legal = score >= MIN_LEGAL_SCORE

    # 分級模型選擇
    if not is_legal:
        model = "claude-haiku-4-5-20251001"
    elif any(kw in text for kw in COMPLEX_LEGAL) or char_count >= 150:
        model = "claude-opus-4-8"       # 書狀撰寫、IRAC 論證
    elif high_hit or score >= 5:
        model = "claude-sonnet-5"       # 一般法律諮詢
    else:
        model = "claude-haiku-4-5-20251001"  # 簡單法律查詢

    return IntentResult(
        is_legal=is_legal,
        score=score,
        reason=", ".join(reasons) if reasons else "no_signal",
        model=model,
    )


NON_LEGAL_REPLY = (
    "您好！法寶貝專注於法律問題的諮詢，"
    "您的問題目前看起來不像是法律相關議題。\n\n"
    "如果您有合約糾紛、訴訟程序、權益保障或其他法律疑問，"
    "請直接描述您的狀況，我很樂意協助！"
)
