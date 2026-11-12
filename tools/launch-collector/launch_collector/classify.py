"""Decide whether an official post announces a drink, with the words that decided it.

The rules read the title first and use the body only for a launch sentence that also
names a drink. Anything that is a launch but does not say what was launched stays
`needs_review`; nothing is guessed from images.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydantic import JsonValue

if TYPE_CHECKING:
    from collections.abc import Callable

    from launch_collector.models import Decision


def alternation(*parts: str) -> str:
    return "|".join(parts)


SOURCE_TAG = re.compile(r"\(출처\s*:\s*[^)]*\)")
# Brand names and boilerplate contain "커피" but say nothing about the post.
NOISE = re.compile(
    alternation(
        SOURCE_TAG.pattern,
        r"메가\s*MGC\s*커피",
        "메가커피",
        r"컴포즈\s*커피",
        "스타벅스",
        "빽다방",
        r"커피\s*프랜차이즈",
    )
)
LAUNCH = re.compile(
    alternation(
        "출시", "신메뉴", "신제품", "선보", "선봬", "출격", "돌아왔", "돌아온", "런칭", "론칭",
        "새로워진", "새롭게",
    )
)  # fmt: skip
COUNT = re.compile(r"\d+\s*종")
BEVERAGE = re.compile(
    alternation(
        "라떼", "아메리카노", "에스프레소", "콜드브루", "커피", "음료", "에이드", "주스",
        "스무디", "프라페", "쉐이크", "셰이크", "뱅쇼", "모카", "카푸치노", "마끼아또",
        "밀크티", "아이스티", "블랙티", "티브리즈", "드링크",
        "녹차", "홍차", "말차", "호지차", "유자차", "생강차", "대추차", "쌍화차",
        "레몬차", "자몽차", "모과차",
        r"\bTEA\b",
        # A standalone 티 (tea), never the first syllable of 티라미수 or 스티커.
        r"(?<![가-힣])티(?![가-힣])",
    ),
    re.IGNORECASE,
)  # fmt: skip
FOOD = re.compile(
    alternation(
        "케이크", "샌드위치", "와플", "바게트", "티라미수", "빙수", "푸딩", "요거트",
        "베이커리", "디저트", "도넛", "크로플", "토스트", "머핀", "스콘", "파니니",
        "핫도그", "아이스크림", "브레드", "크레이프", "몽블랑", "쿠키", "떡", "빵",
    )
)  # fmt: skip
GOODS = re.compile(
    alternation(
        "굿즈", r"\bMD\b", "텀블러", "키링", "키체인", "머그", "테이블웨어", "드립백",
        "스탬프", "챌린지", "포토카드",
    )
)  # fmt: skip
PROMOTION = re.compile(
    alternation(
        "할인", "쿠폰", "프로모션", "증정", "무료", "적립", r"1\+1", r"\d+\s*천\s*원",
        r"\d[\d,]*원",
    )
)  # fmt: skip
NOTICE = re.compile(
    alternation(
        "당첨", "발표", "안내", "매장", "오픈", "선정", "가입", "기부", "예약",
        r"팬\s*사인회", "프리퀀시", "진출", "호점", "채용", "공지", "점검",
    )
)  # fmt: skip
# Articles break lines in the middle of sentences, so only punctuation ends a sentence.
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
# Trailing spaces, punctuation and quotes (including curly quotes) after a drink name.
TRAILING = re.compile(r"[\s!?.~\u2026'\"\u2018\u2019\u201c\u201d)\]]+$")
QUOTE_LIMIT = 120

TITLE_SIGNALS: dict[str, re.Pattern[str]] = {
    "launch": LAUNCH,
    "count": COUNT,
    "beverage": BEVERAGE,
    "food": FOOD,
    "goods": GOODS,
    "promotion": PROMOTION,
    "notice": NOTICE,
}


@dataclass(frozen=True, slots=True)
class Classification:
    decision: Decision
    evidence: dict[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Signals:
    found: dict[str, list[str]]
    name_title: bool
    body_sentence: str | None

    def has(self, key: str) -> bool:
        return bool(self.found[key])

    @property
    def drink_launch(self) -> bool:
        return self.has("launch") and self.has("beverage")

    @property
    def drink_title(self) -> bool:
        return self.has("beverage") and not self.has("food")


def words(pattern: re.Pattern[str], text: str) -> list[str]:
    seen: list[str] = []
    for match in pattern.finditer(text):
        word = match.group(0)
        if word not in seen:
            seen.append(word)
    return seen


def launch_sentence(body: str) -> str | None:
    """First body sentence that both announces something and names a drink, as written."""
    for sentence in SENTENCE_END.split(body):
        text = " ".join(SOURCE_TAG.sub(" ", sentence).split())
        checked = NOISE.sub(" ", text)
        if LAUNCH.search(checked) and BEVERAGE.search(checked):
            return text if len(text) <= QUOTE_LIMIT else text[: QUOTE_LIMIT - 1] + "\u2026"
    return None


def ends_with_beverage(title: str) -> bool:
    stripped = TRAILING.sub("", title)
    return any(match.end() == len(stripped) for match in BEVERAGE.finditer(stripped))


# Checked in order; the first matching rule decides.
RULES: tuple[tuple[Callable[[Signals], bool], Decision, str], ...] = (
    (lambda s: s.has("goods") and not s.drink_launch, "excluded", "title_goods"),
    (lambda s: s.has("notice") and not s.drink_launch, "excluded", "title_notice"),
    (lambda s: s.has("promotion") and s.has("launch"), "needs_review", "launch_with_promotion"),
    (lambda s: s.has("promotion"), "excluded", "title_promotion"),
    (lambda s: s.drink_launch, "accepted", "title_launch_and_beverage"),
    (lambda s: s.has("launch") and s.has("food"), "excluded", "title_food_launch"),
    (
        lambda s: s.has("launch") and s.body_sentence is not None,
        "accepted",
        "body_launch_and_beverage",
    ),
    (lambda s: s.has("launch"), "needs_review", "launch_without_beverage"),
    (lambda s: s.drink_title and s.has("count"), "accepted", "title_beverage_count"),
    (lambda s: s.drink_title and s.name_title, "accepted", "title_beverage_name"),
    (lambda s: s.body_sentence is not None, "needs_review", "body_launch_only"),
)


def classify(title: str, body_text: str) -> Classification:
    title_text = NOISE.sub(" ", title)
    signals = Signals(
        found={key: words(pattern, title_text) for key, pattern in TITLE_SIGNALS.items()},
        name_title=ends_with_beverage(title_text),
        body_sentence=launch_sentence(body_text),
    )
    decision: Decision = "excluded"
    rule = "no_launch_signal"
    for applies, rule_decision, rule_name in RULES:
        if applies(signals):
            decision, rule = rule_decision, rule_name
            break
    evidence: dict[str, JsonValue] = {"rule": rule}
    for key, value in signals.found.items():
        if value:
            evidence[key] = list[JsonValue](value)
    if signals.body_sentence and rule.startswith("body_"):
        evidence["body_sentence"] = signals.body_sentence
    return Classification(decision, evidence)
