"""Citation parsing, refusal detection, and human-referral checks. Pure functions, no Chainlit dependency, easy to test."""
from __future__ import annotations

import re

REFUSAL = "I don't have that information in the wiki snapshot."

_CITE = re.compile(r"\[S(\d+)\]")

# Questions about real money or accounts: the wiki can't and shouldn't answer these, refer to official support
_REFERRAL = re.compile(
    r"refund|top[- ]?up|recharge|chargeback|payment|charged|purchase|billing|"
    r"account|hacked|banned|suspended|password|"
    r"充值|退款|扣款|付款|账号|封号|被盗|密码",
    re.I,
)

REFERRAL_TEXT = (
    "This involves real money or your account. A wiki can't resolve that — "
    "please contact **HoYoverse official customer support** for top-up, refund, or account issues."
)


def cited_indices(answer: str, n_sources: int) -> list[int]:
    """Source numbers actually cited in the answer (1-based, deduplicated in order, out-of-range dropped)."""
    seen = []
    for m in _CITE.finditer(answer):
        i = int(m.group(1))
        if 1 <= i <= n_sources and i not in seen:
            seen.append(i)
    return seen


def is_refusal(answer: str) -> bool:
    return REFUSAL.lower().rstrip(".") in answer.lower()


def needs_referral(question: str) -> bool:
    return bool(_REFERRAL.search(question))


_NUMBER = re.compile(r"(?<![\w.])\d+(?:,\d{3})*(?:\.\d+)?")


def unsupported_numbers(answer: str, sources: list[str]) -> list[str]:
    """Numbers in the answer that do not appear verbatim in the cited sources (deduplicated in order).

    "Verbatim" means whole-number boundaries: if the source says 218.88, an answer saying 218.8 is not found. Thousands separators are stripped on both sides before comparing.
    """
    text = _CITE.sub(" ", answer)
    pool = " ".join(sources).replace(",", "")
    bad = []
    for m in _NUMBER.finditer(text):
        n = m.group(0).replace(",", "")
        if n not in bad and not re.search(rf"(?<![\d.]){re.escape(n)}(?![\d]|\.\d)", pool):
            bad.append(m.group(0))
    return bad
