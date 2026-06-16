"""Satisfaction / dissatisfaction inference (Phase 15).

RuleAnalyzer (default) scans the user's turn for correction / re-question /
negative phrases and a latency signal — deterministic and testable. LLMAnalyzer
(opt-in, Ollama) is the richer estimator. Both produce an `Analysis` that is
persisted to inferred_feedback_logs.
"""

from __future__ import annotations

import json
from typing import Protocol, runtime_checkable

import httpx
from pydantic import BaseModel

# (substring, issue_type). Order matters: more specific phrases first.
_NEGATIVE_SIGNALS: tuple[tuple[str, str], ...] = (
    ("そうじゃない", "misunderstanding"),
    ("違う", "misunderstanding"),
    ("もっと具体的", "too_abstract"),
    ("浅い", "shallow_answer"),
    ("長すぎ", "too_verbose"),
    ("前にも言った", "ignored_context"),
    ("前に言った", "ignored_context"),
    ("それは不要", "over_automation"),
    ("いらない", "over_automation"),
    ("何言ってる", "misunderstanding"),
    ("やり直し", "misunderstanding"),
    ("やり直して", "misunderstanding"),
    ("もういい", "shallow_answer"),
)
_POSITIVE_SIGNALS: tuple[str, ...] = ("いいね", "助かる", "それでOK", "ありがとう", "完璧", "ばっちり")

_NEUTRAL_SCORE = 0.6
_NEG_WEIGHT = 0.3
_POS_WEIGHT = 0.3
_LATENCY_PENALTY = 0.1
_LATENCY_THRESHOLD_MS = 30_000
_CONFIDENCE_WITH_SIGNAL = 0.7
_CONFIDENCE_NO_SIGNAL = 0.3
_LLM_TIMEOUT_S = 60.0


class Analysis(BaseModel):
    """The inferred outcome of a single turn."""

    predicted_satisfaction: float
    issue_type: str | None = None
    issue_detail: str | None = None
    evidence: str | None = None
    confidence: float


@runtime_checkable
class Analyzer(Protocol):
    """Infers satisfaction/issues for a user turn."""

    def analyze(self, user_input: str, *, latency_ms: int | None = None) -> Analysis: ...


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


class RuleAnalyzer:
    """Deterministic phrase/latency-based satisfaction inference."""

    def analyze(self, user_input: str, *, latency_ms: int | None = None) -> Analysis:
        negatives = [(phrase, issue) for phrase, issue in _NEGATIVE_SIGNALS if phrase in user_input]
        positives = [phrase for phrase in _POSITIVE_SIGNALS if phrase in user_input]

        score = _NEUTRAL_SCORE + _POS_WEIGHT * len(positives) - _NEG_WEIGHT * len(negatives)
        issue_type: str | None = None
        evidence: str | None = None
        if negatives:
            evidence, issue_type = negatives[0]

        if latency_ms is not None and latency_ms > _LATENCY_THRESHOLD_MS:
            score -= _LATENCY_PENALTY
            if issue_type is None:
                issue_type = "latency"
                evidence = f"latency={latency_ms}ms"

        has_signal = bool(negatives or positives)
        return Analysis(
            predicted_satisfaction=_clamp01(score),
            issue_type=issue_type,
            evidence=evidence,
            confidence=_CONFIDENCE_WITH_SIGNAL if has_signal else _CONFIDENCE_NO_SIGNAL,
        )


class LLMAnalyzer:
    """Richer satisfaction inference via Ollama (opt-in; requires a running model)."""

    _SYSTEM = (
        "直近のユーザー発話から、前の応答へのユーザー満足度を推定する。"
        'JSON のみを返す: {"predicted_satisfaction":0..1,"issue_type":"...|null",'
        '"issue_detail":"...","evidence":"...","confidence":0..1}。'
    )

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url
        self._model = model
        self._fallback = RuleAnalyzer()

    def analyze(self, user_input: str, *, latency_ms: int | None = None) -> Analysis:
        try:
            res = httpx.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "stream": False,
                    "format": "json",
                    "messages": [
                        {"role": "system", "content": self._SYSTEM},
                        {"role": "user", "content": user_input},
                    ],
                },
                timeout=_LLM_TIMEOUT_S,
            )
            res.raise_for_status()
            data = json.loads(res.json()["message"]["content"])
            return Analysis.model_validate(data)
        except (httpx.HTTPError, KeyError, json.JSONDecodeError, ValueError):
            # Fall back to deterministic rules if the model is unavailable/malformed.
            return self._fallback.analyze(user_input, latency_ms=latency_ms)
