"""Tests that intent prompt encodes critical date-extraction rules."""

from app.agent.prompts import load_prompt


def test_intent_prompt_per_year_since_override() -> None:
    prompt = load_prompt("intent")
    assert "per year since 2015" in prompt
    assert "start_year=2015" in prompt


def test_intent_prompt_date_window_table() -> None:
    prompt = load_prompt("intent")
    assert "between 2015 and 2018" in prompt
    assert "between 2015 to 2018" in prompt
    assert "since / from / after" in prompt


def test_intent_prompt_dates_belong_in_filters_not_assumptions_only() -> None:
    prompt = load_prompt("intent")
    assert "not only in `assumptions`" in prompt


def test_intent_prompt_no_conflicting_do_not_infer_date_block() -> None:
    prompt = load_prompt("intent")
    assert "**Do not infer** unless the query" not in prompt
