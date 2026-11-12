"""Rule-based launch classification, checked against titles seen on the official boards.

Titles below were collected from the four official news boards on 2026-11-10. Body
snippets are shortened and curly quotes are written as straight quotes. Expected
decisions are the team's reading of each post.
"""

from __future__ import annotations

import pytest

from launch_collector.classify import classify

ACCEPTED = [
    # Explicit launch word plus a beverage in the title.
    ("시그니처 딥라떼 출시", "", "title_launch_and_beverage"),
    ("올해 수확한 포도 & 복숭아 주스 출시", "", "title_launch_and_beverage"),
    ("슈크림부터 치즈까지…컴포즈커피, 가을 라떼 4종 출격", "", "title_launch_and_beverage"),
    (
        '컴포즈커피, 음료·베이커리 신메뉴 7종 출시…"비스코프 라떼 등"',
        "",
        "title_launch_and_beverage",
    ),
    (
        "컴포즈커피, 복숭아·한라봉 활용 여름 신메뉴 출시…저당 음료도 선봬",
        "",
        "title_launch_and_beverage",
    ),
    ("스타벅스, 홀리데이 음료 첫선", "", "title_launch_and_beverage"),
    ("NEW! 딸기 라떼", "", "title_launch_and_beverage"),
    # A flavor word before a food word does not hide a real drink later in the title.
    ("말차 쿠키 라떼 출시", "", "title_launch_and_beverage"),
    # A beverage with a menu count reads as a menu introduction.
    ("오늘은 어떤 TEA 4종", "", "title_beverage_count"),
    ("달콤한 꿀밤 &고구마 음료4종", "", "title_beverage_count"),
    ("마음까지 따뜻해지는 전통음료 3종", "", "title_beverage_count"),
    # Paik posters: the title is just the drink name.
    ("달콤, 고소함이 한잔에! 토피넛라떼", "", "title_beverage_name"),
    ("고소함이 쌀아있네! 우리쌀 라떼", "", "title_beverage_name"),
    ("기다렸던 그 맛, 뱅쇼", "", "title_beverage_name"),
    ("찻잎을 볶아 더한 깊은 풍미 호지차라떼", "", "title_beverage_name"),
    ("부드러운 티라미수 라떼", "", "title_beverage_name"),
    # Launch in the title, beverage named in the same body sentence.
    (
        "컴포즈커피, 구미식 수박화채 재해석한 여름 메뉴 선보여",
        "(출처 : 컴포즈커피) 수박을 활용한 화채 메뉴를 선보이며 계절 음료 라인업 강화에 나섰다.",
        "body_launch_and_beverage",
    ),
    ("11월 신메뉴 안내", "딸기 라떼 2종을 새롭게 선보입니다.", "body_launch_and_beverage"),
]

NEEDS_REVIEW = [
    # Launch announced, but nothing says whether it is a drink (poster-only posts).
    ("[이벤트] 겨울시즌 신메뉴 출시 이벤트", "", "launch_without_beverage"),
    ("[이벤트] 가을시즌 신메뉴 출시", "", "launch_without_beverage"),
    ("[이벤트] 이츠셰프컬렉션 신메뉴 출시", "", "launch_without_beverage"),
    ("BLACK VELVET 달콤쌈사름하게 즐기는 신메뉴 4종 출시", "", "launch_without_beverage"),
    (
        "새로워진 하루 한 컵 3종 출시",
        "하루 한 컵 사과 & 땅콩버터  하루 한 컵 방울토마토  하루 한 컵 베지스틱",
        "launch_without_beverage",
    ),
    (
        "10월 27일, 리저브 크리스마스 2026 출시 이벤트",
        "리저브 크리스마스 2026  베트남 둥 크노",
        "launch_without_beverage",
    ),
    # A notice word must not hide a launch from review.
    ("신메뉴 출시 안내", "", "launch_without_beverage"),
    ("[공지] 신메뉴 출시", "", "launch_without_beverage"),
    # A launch that is only mentioned as the reason for a discount.
    ("컴포즈커피, '딥 다이브 비터홀릭' 출시 기념 할인 프로모션", "", "launch_with_promotion"),
    # Apps and services are launched too; a person decides.
    ("MGC커피 앱 리뉴얼 출시", "", "launch_with_service"),
    ("커피 구독 서비스 출시", "", "launch_with_service"),
    ("모바일 음료 주문 서비스 새롭게 선보여", "", "launch_with_service"),
    # Beverage in the title and a launch only in the body.
    (
        "커피만으론 부족했다…컴포즈커피, 메뉴 다각화 승부수",
        "(출처 : 컴포즈커피) 음료부터 식사 대용 메뉴, 디저트까지 아우르는 신메뉴를 대거 출시한다.",
        "body_launch_only",
    ),
]

EXCLUDED = [
    # Food launches, including food named after a drink flavor.
    ("[출시] 샌드위치 신메뉴 출시", "", "title_food_launch"),
    ("달콤·고소 밤 풍미 담았다…컴포즈커피, 가을 한정 '밤 티라미수' 출시", "", "title_food_launch"),
    (
        "컴포즈커피, '초코 바게트·명란 소프트 바게트' 고객 호응에 다시 돌아왔다",
        "",
        "title_food_launch",
    ),
    ('"상하목장 원유에 치즈케이크·초코쉘"…컴포즈커피, 여름 신메뉴 출시', "", "title_food_launch"),
    ("코어 홀케이크 4종 출시", "", "title_food_launch"),
    ("더블 치즈 케이크 출시", "", "title_food_launch"),
    ("신규 푸딩, 요거트 출시", "", "title_food_launch"),
    ("말차 케이크 출시", "", "title_food_launch"),
    ("녹차 아이스크림 출시", "", "title_food_launch"),
    ("커피콩빵 출시", "", "title_food_launch"),
    ("밀크티 쿠키 출시", "", "title_food_launch"),
    ("커피 젤리 출시", "", "title_food_launch"),
    ("녹차 마카롱 신메뉴", "", "title_food_launch"),
    # Goods and merchandise.
    ("온라인 스토어 골든 노엘 MD 출시", "", "title_goods"),
    ("컴포즈커피, 디즈니 협업 '이상한 나라의 앨리스' 드립백·키링 세트 출시", "", "title_goods"),
    ('컴포즈커피, 디즈니 협업 여름 굿즈 8종 완성…"夏 시즌 마지막 선봬"', "", "title_goods"),
    ("[출시] 붕괴: 스타레일 콜라보 스탬프 챌린지!", "", "title_goods"),
    ("[안내] MGC x 사랑의 하츄핑 2 공식 콜라보 굿즈 사전예약 안내", "", "title_goods"),
    # Discounts on existing drinks.
    ("빽다방 20주년 기념 아메리카노(ICED) 1천원에 만나보세요! (8/19~8/21)", "", "title_promotion"),
    ("컴포즈커피, 10월 카카오페이 첫 결제 고객에 '아아' 쿠폰 증정", "", "title_promotion"),
    (
        "청량함과 든든함 한 번에...컴포즈커피, 여름 한정 '서머 세트' 할인 프로모션",
        "",
        "title_promotion",
    ),
    # Notices, results, company news.
    (
        "빽다방 디카페인 커피 판매 매장 안내",
        "이제 빽다방에서도 디카페인 커피를 즐겨보세요.",
        "title_notice",
    ),
    ("[이벤트] NCT 127 팬 사인회 당첨자 발표", "", "title_notice"),
    ("2026 크리스마스 홀케이크 사전 예약", "", "title_notice"),
    ("새벽 5시부터 '오픈런'…컴포즈커피, 7일 필리핀 1호점 연다", "", "title_notice"),
    ("컴포즈커피, '매경 100대 프랜차이즈' 5년 연속 선정…국내외 시장 공략 박차", "", "title_notice"),
    # No launch signal at all. A year is not a menu count; a generic drink word is not a name.
    ("[이벤트] SMGC 2 : PLAY TODAY", "", "no_launch_signal"),
    ("김원훈 뜨자 성수 들썩...컴포즈커피 '수박빙수 대란' 터졌다", "", "no_launch_signal"),
    ("2026 종로 커피 축제 참가", "", "no_launch_signal"),
    ("알고 마시면 더 맛있는 커피", "", "no_launch_signal"),
    ("1원칙: 신선한 커피", "", "no_launch_signal"),
]


@pytest.mark.parametrize(("title", "body", "rule"), ACCEPTED)
def test_classify_when_post_announces_a_drink(title: str, body: str, rule: str) -> None:
    # When
    result = classify(title, body)
    # Then
    assert (result.decision, result.evidence["rule"]) == ("accepted", rule), result.evidence


@pytest.mark.parametrize(("title", "body", "rule"), NEEDS_REVIEW)
def test_classify_when_drink_is_unclear(title: str, body: str, rule: str) -> None:
    # When
    result = classify(title, body)
    # Then
    assert (result.decision, result.evidence["rule"]) == ("needs_review", rule), result.evidence


@pytest.mark.parametrize(("title", "body", "rule"), EXCLUDED)
def test_classify_when_post_is_not_a_drink_launch(title: str, body: str, rule: str) -> None:
    # When
    result = classify(title, body)
    # Then
    assert (result.decision, result.evidence["rule"]) == ("excluded", rule), result.evidence


def test_classify_does_not_read_tiramisu_or_brand_name_as_a_drink() -> None:
    # When
    result = classify("컴포즈커피 티라미수 출시", "")
    # Then
    assert result.decision == "excluded"
    assert "beverage" not in result.evidence


def test_classify_records_the_rule_and_matched_words() -> None:
    # When
    result = classify("시그니처 딥라떼 출시", "")
    # Then
    assert result.evidence["rule"] == "title_launch_and_beverage"
    assert result.evidence["launch"] == ["출시"]
    assert result.evidence["beverage"] == ["라떼"]


def test_classify_joins_a_body_sentence_broken_across_lines() -> None:
    # Given: the article body as extracted from the official page (news:319362)
    lines = [
        "(출처 : 컴포즈커피)\n\n\n\n\n",
        "컴포즈커피가 여름철 대표 과일인 수박을 활용한 화채 메뉴를 선보이며",
        "계절 음료 라인업 강화에 나섰다.",
        "컴포즈커피는 신메뉴 2종을 선보였다고 30일 밝혔다.",
    ]
    # When
    result = classify("컴포즈커피, 구미식 수박화채 재해석한 여름 메뉴 선보여", "\n\n".join(lines))
    # Then
    assert result.decision == "accepted", result.evidence
    assert result.evidence["body_sentence"] == " ".join(lines[1:3])


def test_classify_keeps_body_evidence_short() -> None:
    # Given
    sentence = "신메뉴 음료 " + "아주 긴 설명 " * 100 + "를 선보였다."
    # When
    result = classify("여름 메뉴 선보여", sentence)
    # Then
    assert result.decision == "accepted"
    quote = result.evidence["body_sentence"]
    assert isinstance(quote, str)
    assert len(quote) <= 120
