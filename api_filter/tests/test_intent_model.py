"""
pytest tests/test_intent_model.py -v
驗證分級模型選擇邏輯
"""
import pytest
from api_filter.intent import classify_intent


@pytest.mark.parametrize("text,expected_model", [
    # Opus：書狀撰寫、複雜論證
    ("幫我寫一份答辯狀，針對原告的侵權主張", "claude-opus-4-8"),
    ("我要提起訴願，請幫我進行 IRAC 論證", "claude-opus-4-8"),
    ("請幫我分析這份判決書並寫上訴狀", "claude-opus-4-8"),

    # Sonnet：一般法律諮詢（高分）
    ("我被詐欺了，應該去哪裡報案？合約是否有效？", "claude-sonnet-5"),
    ("勞基法第幾條規定資遣費怎麼算？", "claude-sonnet-5"),
    ("合約違約金條款是否合法？能不能主張無效？", "claude-sonnet-5"),

    # Haiku：簡單法律查詢（剛過門檻）
    ("房東不退押金怎麼辦", "claude-haiku-4-5-20251001"),
    ("我欠薪可以去哪申訴", "claude-haiku-4-5-20251001"),
])
def test_model_tiering(text, expected_model):
    result = classify_intent(text)
    assert result.is_legal, f"應判斷為法律問題：{text!r}"
    assert result.model == expected_model, (
        f"模型分級錯誤\n"
        f"  輸入：{text!r}\n"
        f"  預期：{expected_model}\n"
        f"  實際：{result.model}\n"
        f"  分數：{result.score}\n"
        f"  原因：{result.reason}"
    )
