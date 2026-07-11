"""
pytest tests/test_filter.py -v
"""
import pytest
from api_filter.filter import pre_filter


# ── 第一層應攔截的案例 ─────────────────────────────────────
@pytest.mark.parametrize("text", [
    "你好",
    "您好！",
    "嗨",
    "hi",
    "Hello",
    "早安",
    "晚安～",
    "謝謝你",
    "感謝！",
    "Thank you",
    "掰掰",
    "再見",
    "bye",
    "好的",
    "OK",
    "ok",
    "ㄅ",
    "哈哈哈",
])
def test_layer1_blocks_greetings(text):
    r = pre_filter(text)
    assert r.blocked, f"應被第一層攔截但放行了：{text!r}"
    assert r.layer == "layer1_greeting"
    assert r.reply is not None and len(r.reply) > 0


# ── 第二層應攔截的案例（閒聊/非法律）──────────────────────
@pytest.mark.parametrize("text", [
    "今天天氣真好",
    "推薦我吃什麼好呢？",
    "你喜歡看什麼電影",
    "我想去旅遊，哪裡好玩？",
    "幫我介紹一首好聽的歌",
])
def test_layer2_blocks_chit_chat(text):
    r = pre_filter(text)
    assert r.blocked, f"應被第二層攔截但放行了：{text!r}"
    assert r.layer == "layer2_intent"


# ── 第三層應放行的法律問題 ────────────────────────────────
@pytest.mark.parametrize("text", [
    "我的房東不退押金，我該怎麼辦？",
    "合約上寫的違約金條款是否合法？",
    "被告我侵權，我需要準備哪些證據？",
    "民法第184條的意思是什麼？",
    "我想提起訴訟，程序是什麼？",
    "勞基法規定的資遣費怎麼計算？",
    "本票可以強制執行嗎？",
    "離婚後子女監護權如何爭取？",
    "公司欠我薪水，我可以去哪裡申訴？",
    "被詐欺了，應該去哪裡報案？",
])
def test_layer3_passes_legal_questions(text):
    r = pre_filter(text)
    assert not r.blocked, f"法律問題被誤攔截了：{text!r}"
    assert r.layer == "pass"


# ── 問候語中夾帶法律問題不應被攔截 ──────────────────────
@pytest.mark.parametrize("text", [
    "你好，我想問一下合約違約金的問題",
    "嗨，我被告了怎麼辦",
    "謝謝你，那判決書下來之後我要怎麼上訴？",
])
def test_legal_greeting_mix_passes(text):
    r = pre_filter(text)
    # 問候語 + 法律問題，應放行
    assert not r.blocked, f"夾帶法律問題的問候語被誤攔截：{text!r}"


# ── Layer 1 身份詢問攔截 ─────────────────────────────────
@pytest.mark.parametrize("text", [
    "你是誰",
    "你能做什麼",
    "你有什麼功能",
    "介紹一下自己",
    "法寶貝是什麼",
    "你好啊！請問你是誰？",
    "你可以幫我什麼",
])
def test_layer1_blocks_identity_questions(text):
    r = pre_filter(text)
    assert r.blocked, f"身份詢問應被 Layer 1 攔截：{text!r}"
    assert r.layer == "layer1_greeting"
    assert "法寶貝" in r.reply, f"身份回覆應含有法寶貝：{text!r}"


# ── 口語法律詞應放行至 Layer 3 ──────────────────────────
@pytest.mark.parametrize("text", [
    "你能幫我打官司嗎",
    "我想找人打官司",
    "這種事情可以索賠嗎",
])
def test_colloquial_legal_terms_pass(text):
    r = pre_filter(text)
    assert not r.blocked or r.layer == "layer1_5_offline_pack", \
        f"口語法律問題被誤攔截：{text!r} → {r.layer}"


# ── 回覆輪替測試（不重複） ────────────────────────────────
def test_greeting_replies_rotate():
    replies = set()
    for _ in range(6):
        r = pre_filter("你好")
        replies.add(r.reply)
    # 應有超過 1 種不同回覆
    assert len(replies) > 1, "問候語回覆沒有輪替"


# ── 效能基準：過濾應在 5ms 以內完成 ──────────────────────
def test_filter_latency():
    r = pre_filter("我想提起訴訟，程序是什麼？")
    assert r.latency_ms < 5, f"過濾耗時過長：{r.latency_ms:.2f}ms"
