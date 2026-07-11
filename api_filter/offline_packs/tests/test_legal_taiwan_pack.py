"""
pytest api_filter/offline_packs/tests/test_legal_taiwan_pack.py -v
"""
import pytest
from api_filter.offline_packs.loader import _loader as loader, match_offline


@pytest.fixture(autouse=True)
def load_pack():
    loader.clear()
    loader.load("legal_taiwan")
    yield
    loader.clear()


# ══ 結構驗證 ══════════════════════════════════════════════════

def test_pack_loads_29_scenarios():
    assert len(loader._packs[0]["scenarios"]) == 29

def test_all_scenarios_have_required_fields():
    for s in loader._packs[0]["scenarios"]:
        assert "id" in s
        assert "category" in s
        assert "triggers" in s and len(s["triggers"]) > 0
        assert "response" in s and len(s["response"]) > 50

def test_categories_count():
    cats = {}
    for s in loader._packs[0]["scenarios"]:
        cats[s["category"]] = cats.get(s["category"], 0) + 1
    assert cats["rental"] == 6
    assert cats["labor"] == 6
    assert cats["consumer"] == 5
    assert cats["traffic"] == 4
    assert cats["family"] == 4
    assert cats["process"] == 4


# ══ 租賃（rental）══════════════════════════════════════════════

def test_rental_deposit_limit():
    m = match_offline("押金上限是多少")
    assert m and m.scenario_id == "rental_deposit_limit"
    assert "2個月" in m.response

def test_rental_deposit_limit_trigger_variant():
    m = match_offline("押金最多可以收幾個月")
    assert m and m.scenario_id == "rental_deposit_limit"

def test_rental_deposit_return():
    m = match_offline("押金退還的規定是什麼")
    assert m and m.scenario_id == "rental_deposit_return"

def test_rental_deposit_return_trigger_variant():
    m = match_offline("房東不退押金我怎麼辦")
    assert m and m.scenario_id == "rental_deposit_return"

def test_rental_early_termination_tenant():
    m = match_offline("我想提前退租怎麼辦")
    assert m and m.scenario_id == "rental_early_termination_tenant"

def test_rental_early_termination_tenant_variant():
    m = match_offline("中途搬走要賠多少")
    assert m and m.scenario_id == "rental_early_termination_tenant"

def test_rental_early_termination_landlord():
    m = match_offline("房東趕人合法嗎")
    assert m and m.scenario_id == "rental_early_termination_landlord"

def test_rental_early_termination_landlord_variant():
    m = match_offline("房東要我搬走有沒有賠償")
    assert m and m.scenario_id == "rental_early_termination_landlord"

def test_rental_repair_obligation():
    m = match_offline("房東不修水管誰要負責")
    assert m and m.scenario_id == "rental_repair_obligation"

def test_rental_repair_obligation_variant():
    m = match_offline("租屋修繕責任怎麼算")
    assert m and m.scenario_id == "rental_repair_obligation"

def test_rental_contract_dispute():
    m = match_offline("租約糾紛要去哪裡申訴")
    assert m and m.scenario_id == "rental_contract_dispute"

def test_rental_contract_dispute_variant():
    m = match_offline("租賃爭議怎麼解決")
    assert m and m.scenario_id == "rental_contract_dispute"


# ══ 勞資（labor）══════════════════════════════════════════════

def test_labor_overtime_pay():
    m = match_offline("加班費計算方式")
    assert m and m.scenario_id == "labor_overtime_pay"
    assert "1.34" in m.response or "1/3" in m.response

def test_labor_overtime_pay_variant():
    m = match_offline("加班費怎麼算才對")
    assert m and m.scenario_id == "labor_overtime_pay"

def test_labor_severance():
    m = match_offline("資遣費計算公式")
    assert m and m.scenario_id == "labor_severance"
    assert "0.5" in m.response

def test_labor_severance_variant():
    m = match_offline("被資遣可以領多少")
    assert m and m.scenario_id == "labor_severance"

def test_labor_wrongful_termination():
    m = match_offline("違法解僱怎麼辦")
    assert m and m.scenario_id == "labor_wrongful_termination"

def test_labor_wrongful_termination_variant():
    m = match_offline("被非法開除可以怎麼做")
    assert m and m.scenario_id == "labor_wrongful_termination"

def test_labor_notice_period():
    m = match_offline("離職預告期要幾天")
    assert m and m.scenario_id == "labor_notice_period"
    assert "10" in m.response

def test_labor_notice_period_variant():
    m = match_offline("提前幾天辭職才合法")
    assert m and m.scenario_id == "labor_notice_period"

def test_labor_unpaid_wages():
    m = match_offline("老闆不給薪水怎麼辦")
    assert m and m.scenario_id == "labor_unpaid_wages"
    assert "1955" in m.response

def test_labor_unpaid_wages_variant():
    m = match_offline("薪資未付要怎麼申訴")
    assert m and m.scenario_id == "labor_unpaid_wages"

def test_labor_insurance():
    m = match_offline("雇主未投保勞保怎麼辦")
    assert m and m.scenario_id == "labor_insurance"

def test_labor_insurance_variant():
    m = match_offline("老闆沒幫我保勞保")
    assert m and m.scenario_id == "labor_insurance"


# ══ 消費（consumer）════════════════════════════════════════════

def test_consumer_seven_days():
    m = match_offline("七日鑑賞期怎麼用")
    assert m and m.scenario_id == "consumer_seven_days"
    assert "7" in m.response

def test_consumer_seven_days_variant():
    m = match_offline("網購退貨可以嗎")
    assert m and m.scenario_id == "consumer_seven_days"

def test_consumer_defective_goods():
    m = match_offline("買到瑕疵商品怎麼辦")
    assert m and m.scenario_id == "consumer_defective_goods"

def test_consumer_defective_goods_variant():
    m = match_offline("商品有瑕疵可以退嗎")
    assert m and m.scenario_id == "consumer_defective_goods"

def test_consumer_online_fraud():
    m = match_offline("網購詐騙付了錢沒收到")
    assert m and m.scenario_id == "consumer_online_fraud"
    assert "165" in m.response

def test_consumer_online_fraud_variant():
    m = match_offline("付錢沒收到貨賣家跑路了")
    assert m and m.scenario_id == "consumer_online_fraud"

def test_consumer_deposit_refund():
    m = match_offline("訂金退還可以嗎")
    assert m and m.scenario_id == "consumer_deposit_refund"

def test_consumer_deposit_refund_variant():
    m = match_offline("訂金不退合法嗎")
    assert m and m.scenario_id == "consumer_deposit_refund"

def test_consumer_false_advertising():
    m = match_offline("廣告誇大不實怎麼申訴")
    assert m and m.scenario_id == "consumer_false_advertising"

def test_consumer_false_advertising_variant():
    m = match_offline("不實廣告可以告嗎")
    assert m and m.scenario_id == "consumer_false_advertising"


# ══ 交通事故（traffic）══════════════════════════════════════════

def test_traffic_accident_steps():
    m = match_offline("發生車禍怎麼處理")
    assert m and m.scenario_id == "traffic_accident_steps"
    assert "110" in m.response

def test_traffic_accident_steps_variant():
    m = match_offline("車禍現場處理步驟")
    assert m and m.scenario_id == "traffic_accident_steps"

def test_traffic_compulsory_insurance():
    m = match_offline("強制險理賠怎麼申請")
    assert m and m.scenario_id == "traffic_compulsory_insurance"
    assert "200" in m.response

def test_traffic_compulsory_insurance_variant():
    m = match_offline("強制汽車責任險怎麼用")
    assert m and m.scenario_id == "traffic_compulsory_insurance"

def test_traffic_hit_and_run():
    m = match_offline("肇事逃逸對方跑了怎麼辦")
    assert m and m.scenario_id == "traffic_hit_and_run"

def test_traffic_hit_and_run_variant():
    m = match_offline("車禍逃逸怎麼辦")
    assert m and m.scenario_id == "traffic_hit_and_run"

def test_traffic_fault_determination():
    m = match_offline("車禍過失責任怎麼認定")
    assert m and m.scenario_id == "traffic_fault_determination"

def test_traffic_fault_determination_variant():
    m = match_offline("事故責任鑑定要去哪裡")
    assert m and m.scenario_id == "traffic_fault_determination"


# ══ 家事（family）══════════════════════════════════════════════

def test_family_divorce_agreement():
    m = match_offline("協議離婚要怎麼辦手續")
    assert m and m.scenario_id == "family_divorce_agreement"
    assert "戶政" in m.response

def test_family_divorce_agreement_variant():
    m = match_offline("辦理離婚手續需要什麼")
    assert m and m.scenario_id == "family_divorce_agreement"

def test_family_divorce_litigation():
    m = match_offline("對方不肯離婚可以怎麼做")
    assert m and m.scenario_id == "family_divorce_litigation"

def test_family_divorce_litigation_variant():
    m = match_offline("單方面離婚有什麼方法")
    assert m and m.scenario_id == "family_divorce_litigation"

def test_family_child_custody():
    m = match_offline("離婚後監護權歸誰")
    assert m and m.scenario_id == "family_child_custody"

def test_family_child_custody_variant():
    m = match_offline("子女監護怎麼爭取")
    assert m and m.scenario_id == "family_child_custody"

def test_family_inheritance():
    m = match_offline("遺產繼承的順序是什麼")
    assert m and m.scenario_id == "family_inheritance"
    assert "拋棄繼承" in m.response

def test_family_inheritance_variant():
    m = match_offline("拋棄繼承怎麼辦")
    assert m and m.scenario_id == "family_inheritance"


# ══ 申訴管道（process）══════════════════════════════════════════

def test_process_mediation():
    m = match_offline("怎麼申請調解委員會")
    assert m and m.scenario_id == "process_mediation"
    assert "免費" in m.response

def test_process_mediation_variant():
    m = match_offline("鄉鎮調解怎麼申請")
    assert m and m.scenario_id == "process_mediation"

def test_process_legal_aid():
    m = match_offline("法律扶助基金會怎麼申請")
    assert m and m.scenario_id == "process_legal_aid"
    assert "412-8518" in m.response

def test_process_legal_aid_variant():
    m = match_offline("沒錢請律師有免費法律諮詢嗎")
    assert m and m.scenario_id == "process_legal_aid"

def test_process_labor_complaint():
    m = match_offline("1955勞工申訴專線怎麼用")
    assert m and m.scenario_id == "process_labor_complaint"

def test_process_labor_complaint_variant():
    m = match_offline("勞資爭議申訴去哪裡")
    assert m and m.scenario_id == "process_labor_complaint"

def test_process_consumer_complaint():
    m = match_offline("1950消費者申訴")
    assert m and m.scenario_id == "process_consumer_complaint"

def test_process_consumer_complaint_variant():
    m = match_offline("消費糾紛去哪裡申訴")
    assert m and m.scenario_id == "process_consumer_complaint"


# ══ 回應品質驗證 ══════════════════════════════════════════════

def test_all_responses_contain_legal_basis():
    """每個回應都應含有法律依據、申訴管道或行動步驟其中之一"""
    for s in loader._packs[0]["scenarios"]:
        has_legal = "法律依據" in s["response"] or "依據" in s["response"]
        has_action = "下一步" in s["response"] or "申訴" in s["response"] or "步驟" in s["response"]
        has_contact = "📞" in s["response"] or "申請" in s["response"] or "管道" in s["response"]
        assert has_legal or has_action or has_contact, f"{s['id']} 缺少法律依據或行動步驟"

def test_all_responses_min_length():
    for s in loader._packs[0]["scenarios"]:
        assert len(s["response"]) >= 100, f"{s['id']} 回應太短（{len(s['response'])} 字）"

def test_no_scenario_id_duplicate():
    ids = [s["id"] for s in loader._packs[0]["scenarios"]]
    assert len(ids) == len(set(ids)), "有重複的 scenario id"
