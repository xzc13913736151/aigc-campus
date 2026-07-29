from types import SimpleNamespace

from assistant.orchestrator import (
    _build_fill_payload,
    _build_payload_generation_messages,
    _coerce_optional_bool,
    _correct_payload_for_prompt,
    _default_payload_for_kind,
    _extract_negotiable,
    _refresh_trade_description,
    _missing_fields,
    _normalize_payload,
    _postprocess_generated_patch,
    _sanitize_trade_description,
    build_assistant_presentation,
)


def test_trade_condition_prompt_explains_semantics_and_chinese_output():
    session = SimpleNamespace(
        page_type="publish",
        context_path="/pages/trade/create",
        context_target_type="",
        context_target_id="",
    )

    messages = _build_payload_generation_messages(
        session,
        "trade_post_create",
        "用了两年，屏幕有一点划痕",
        {},
        {},
        [],
    )

    prompt = "\n".join(message["content"] for message in messages)
    assert "商品的新旧程度和实际使用状况" in prompt
    assert "不要套固定档位" in prompt
    assert "用户没有提供相关信息时填“无”" in prompt


def test_explicit_condition_in_user_reply_overrides_generic_model_value():
    payload = _correct_payload_for_prompt(
        "trade_post_create",
        {"condition": "used", "title": "出售笔记本电脑", "description": "个人自用笔记本电脑"},
        "我想起来了，成色是九成新",
    )

    assert payload["condition"] == "九成新"


def test_combined_condition_and_negotiability_reply_parses_each_field_separately():
    prompt = "成色：轻微使用痕迹；不议价"
    payload = _correct_payload_for_prompt(
        "trade_post_create",
        {"condition": "", "is_negotiable": None, "description": "出售二手手机"},
        prompt,
    )

    assert payload["condition"] == "轻微使用痕迹"
    assert payload["is_negotiable"] is False


def test_natural_chinese_condition_generated_by_model_is_preserved():
    patch = _postprocess_generated_patch(
        "trade_post_create",
        {"condition": "有明显划痕但功能正常"},
    )

    assert patch["condition"] == "有明显划痕但功能正常"


def test_missing_or_generic_english_condition_becomes_none_label():
    normalized = _normalize_payload(
        "trade_post_create",
        {
            "post_type": "sell",
            "title": "出售自用笔记本电脑",
            "description": "个人自用，功能正常，支持校内当面验机交易。",
            "condition": "",
            "is_negotiable": True,
        },
    )
    generated = _postprocess_generated_patch("trade_post_create", {"condition": "used"})

    assert normalized["condition"] == "无"
    assert generated["condition"] == "无"


def test_unspecified_negotiability_stays_missing_and_is_not_filled():
    payload = _default_payload_for_kind("trade_post_create", SimpleNamespace(), "出售一台电脑")
    normalized = _normalize_payload(
        "trade_post_create",
        {
            **payload,
            "post_type": "sell",
            "title": "出售自用笔记本电脑",
            "description": "个人自用，功能正常，支持校内当面验机交易。",
        },
    )
    fill_payload = _build_fill_payload("trade_post_create", normalized)
    presentation = build_assistant_presentation(
        {"intent": "trade_post_create", "collected_payload": normalized, "missing_fields": []}
    )
    negotiable_field = next(field for field in presentation["fields"] if field["key"] == "is_negotiable")

    assert normalized["is_negotiable"] is None
    assert "is_negotiable" not in fill_payload
    assert negotiable_field["display_value"] == "未说明"
    assert negotiable_field["source"] == "missing"


def test_boolean_strings_are_coerced_strictly():
    assert _coerce_optional_bool("true") is True
    assert _coerce_optional_bool("false") is False
    assert _coerce_optional_bool("unknown") is None


def test_negative_negotiation_phrases_override_positive_substrings():
    assert _extract_negotiable("不可议价，价格3000元") is False
    assert _extract_negotiable("不能议价") is False
    assert _extract_negotiable("不接受还价") is False
    assert _extract_negotiable("可以小刀") is True

    corrected = _correct_payload_for_prompt(
        "trade_post_create",
        {"is_negotiable": True, "description": "出售二手手机", "title": "出售二手手机"},
        "不可议价，3000元",
    )
    assert corrected["is_negotiable"] is False


def test_trade_description_removes_claims_without_user_evidence():
    generated = "本人有一台闲置的二手手机，功能一切正常，外观无明显损坏，日常使用流畅，价格可商议。"
    sanitized = _sanitize_trade_description(generated, "我想卖一台二手手机")

    assert "二手手机" in sanitized
    assert "功能一切正常" not in sanitized
    assert "无明显损坏" not in sanitized
    assert "使用流畅" not in sanitized
    assert "价格可商议" not in sanitized


def test_trade_description_preserves_explicit_user_facts():
    generated = "出售一台vivo手机，功能正常，外观八成新，价格可以小刀。"
    facts = "我想卖一台vivo手机。功能正常，八成新，价格可以小刀"

    assert _sanitize_trade_description(generated, facts) == generated


def test_trade_description_refreshes_from_authoritative_fields_without_inventing_facts():
    generated = "出售一部自用二手手机，成色良好，无维修记录，配件齐全，价格可商议。"
    refreshed = _refresh_trade_description(
        generated,
        {
            "condition": "轻微使用痕迹",
            "price": 8000,
            "price_mode": "fixed",
            "is_negotiable": False,
        },
        "卖二手手机。成色：轻微使用痕迹；价格8000元；不议价",
    )

    assert "成色为轻微使用痕迹" in refreshed
    assert "价格为8000元" in refreshed
    assert "不接受议价" in refreshed
    assert "成色良好" not in refreshed
    assert "无维修记录" not in refreshed
    assert "配件齐全" not in refreshed
    assert "价格可商议" not in refreshed


def test_team_size_and_dating_preferences_are_not_invented():
    team = _normalize_payload(
        "team_post_create",
        {
            "title": "校园项目招募前端同学",
            "summary": "寻找同学一起完成校园项目",
            "details": "项目方向已经确定，希望找到合适的同学一起认真推进和协作。",
            "target_size": None,
        },
    )
    dating = _normalize_payload(
        "dating_setup",
        {
            "profile": {"bio": "我平时喜欢摄影、电影和跑步，也愿意认真认识新的朋友。", "interests": ["摄影", "电影", "跑步"]},
            "preference": {"preferred_genders": [], "preferred_interests": []},
        },
    )
    missing, _labels = _missing_fields("dating_setup", dating)

    assert team["target_size"] is None
    assert dating["preference"]["preferred_interests"] == []
    assert "preference" in missing
