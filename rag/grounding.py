"""Citation parsing, refusal detection, human-referral and spend-advice checks. Pure functions, no Chainlit dependency, easy to test."""
from __future__ import annotations

import re

REFUSAL = "I don't have that information in the wiki snapshot."

_CITE = re.compile(r"\[S(\d+)\]")
# Some models write full-width brackets (【S2】) despite the [S2] example in the prompt
_FULLWIDTH_CITE = re.compile(r"【\s*S(\d+)\s*】")


def normalize_citations(answer: str) -> str:
    """Rewrite 【Sn】 as [Sn], so every citation check below and the UI badges see one format. Apply once per answer."""
    return _FULLWIDTH_CITE.sub(r"[S\1]", answer)

# Questions about real money or accounts: the wiki can't and shouldn't answer these, refer to official support.
# Game terms collide with naive keywords ("Charged Attack", shop "purchase", "take into account"), so each
# English pattern needs a money/account context, not just the word.
_REFERRAL = re.compile(
    r"refund|top[- ]?up|recharge|chargeback|billing|"
    r"(?:double|over|was|been|got|they|i was|me)\s+charged|charged\s+(?:me|twice|my\s+card)|"
    r"\bpayment|\bpaid\b.*\b(?:not|never|didn'?t|missing)|(?:didn'?t|never|not)\b.*\breceive\b.*\b(?:crystals?|purchase|order)|"
    r"\baccount\b.*\b(?:hacked|banned|suspended|locked|stolen|compromised|recover|delete|login|log in)|"
    r"\b(?:hacked|banned|suspended|locked out)\b|password|"
    r"充值|退款|扣款|付款|账号|封号|被盗|密码",
    re.I,
)

REFERRAL_TEXT = (
    "This involves real money or your account. A wiki can't resolve that — "
    "please contact **HoYoverse official customer support** for top-up, refund, or account issues."
)

# "Should I pull/spend?" — the system must give facts only, never a spending recommendation (safeguard #2)
_SPEND_Q = re.compile(
    r"\bshould\s+i\s+(?:pull|roll|wish|spend|buy|save|skip|get|go for|whale|top)|"
    r"\b(?:worth|wise|smart|good idea)\b.{0,40}\b(?:pull|pulling|roll|rolling|spend|spending|wish|wishing|buy|buying|money)|"
    r"\b(?:pull|roll|wish|spend)\b.{0,30}\b(?:or\s+(?:save|skip|wait))|"
    r"\b(?:rent|savings|paycheck|salary|credit card|loan)\b|"
    r"(?:值得|该不该|要不要).{0,6}(?:抽|氪|充)|抽不抽|氪不氪",
    re.I,
)
_RECOMMENDS = re.compile(
    r"\b(?:you\s+should|i(?:'d| would)?\s+recommend|i\s+suggest|definitely|it'?s\s+(?:worth|a good idea))\b"
    r".{0,40}\b(?:pull|roll|wish|spend|buy|save|skip|wait)|"
    r"\b(?:worth\s+(?:pulling|rolling|spending|it)|must[- ]pull|go for it)\b",
    re.I,
)

SPEND_PROMPT_NOTE = (
    "The user is asking whether to spend money or wishes. Do NOT recommend pulling, spending, saving, or skipping. "
    "State only the relevant cited facts (rates, pity rules, banner dates, kit details) and let the user decide."
)
SPEND_TEXT = (
    "This assistant gives facts only, not spending advice. Gacha pulls are randomized; official drop rates are "
    "listed in-game under **Wish → Details**. Only spend money you can afford to lose."
)


def cited_indices(answer: str, n_sources: int) -> list[int]:
    """Source numbers actually cited in the answer (1-based, deduplicated in order, out-of-range dropped)."""
    seen = []
    for m in _CITE.finditer(answer):
        i = int(m.group(1))
        if 1 <= i <= n_sources and i not in seen:
            seen.append(i)
    return seen


def strip_citations(answer: str) -> str:
    """Remove [Sn] markers: their numbering is only valid for the turn that produced them."""
    return re.sub(r"\s*\[S\d+\]", "", answer)


def is_refusal(answer: str) -> bool:
    """A full refusal: contains the refusal sentence and cites nothing.

    A partial answer ("X is ... [S1]. I don't have that information ...") cites sources and is NOT a refusal.
    """
    return REFUSAL.lower().rstrip(".") in answer.lower() and not _CITE.search(answer)


def needs_referral(question: str) -> bool:
    return bool(_REFERRAL.search(question))


def is_spend_question(question: str) -> bool:
    return bool(_SPEND_Q.search(question))


def recommends_spending(answer: str) -> bool:
    return bool(_RECOMMENDS.search(strip_citations(answer)))


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


_WORD = re.compile(r"[\w'’]+")
MAX_QUOTE_WORDS = 25


def long_quotes(answer: str, sources: list[str], limit: int = MAX_QUOTE_WORDS) -> list[str]:
    """Runs of more than `limit` consecutive words copied verbatim (case-insensitive) from any source."""
    n = limit + 1
    src_grams = set()
    for s in sources:
        w = [x.lower() for x in _WORD.findall(s)]
        src_grams.update(tuple(w[i:i + n]) for i in range(len(w) - n + 1))
    words = _WORD.findall(strip_citations(answer))
    low = [x.lower() for x in words]
    hits, i = [], 0
    while i <= len(low) - n:
        if tuple(low[i:i + n]) in src_grams:
            j = i + n  # extend the run as far as it keeps matching
            while j < len(low) and tuple(low[j - n + 1:j + 1]) in src_grams:
                j += 1
            hits.append(" ".join(words[i:j]))
            i = j
        else:
            i += 1
    return hits
