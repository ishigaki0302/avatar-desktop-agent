"""Tests for the weather tool's wttr.in parsing (Phase: factual answers)."""

import pytest

from agent.tools.base import ToolError
from agent.tools.weather import parse_wttr

_SAMPLE = {
    "current_condition": [
        {
            "temp_C": "25",
            "FeelsLikeC": "26",
            "humidity": "60",
            "weatherDesc": [{"value": "晴れ"}],
        },
    ],
    "nearest_area": [{"areaName": [{"value": "Tokyo"}]}],
}


def test_parse_wttr_extracts_fields() -> None:
    out = parse_wttr(_SAMPLE)
    assert out["location"] == "Tokyo"
    assert out["temp_c"] == "25"
    assert out["feels_like_c"] == "26"
    assert out["description"] == "晴れ"


def test_parse_wttr_without_area() -> None:
    out = parse_wttr({"current_condition": [{"temp_C": "20", "weatherDesc": [{"value": "曇り"}]}]})
    assert out["location"] == ""
    assert out["temp_c"] == "20"


def test_parse_wttr_rejects_empty() -> None:
    with pytest.raises(ToolError, match="unexpected"):
        parse_wttr({"current_condition": []})
