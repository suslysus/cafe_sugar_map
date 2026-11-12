from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from launch_collector.errors import CollectionError
from launch_collector.paik import parse_detail, parse_list
from launch_collector.urls import canonical_post_url, post_key

FIXTURES = Path(__file__).parent / "fixtures" / "paik"


def test_list_when_official_page_contains_multiple_posts() -> None:
    # Given
    html = (FIXTURES / "list-page1.html").read_text(encoding="utf-8")
    # When
    result = parse_list(html, 1)
    # Then
    assert len(result.candidates) == 10
    assert len({item.source_key for item in result.candidates}) == 10
    assert result.candidates[0].title == "시그니처 딥라떼 출시"
    assert result.candidates[0].posted_on == date(2026, 11, 4)
    assert result.next_page == 2


@pytest.mark.parametrize("index", [1, 2, 3])
def test_detail_when_official_article_is_image_only(index: int) -> None:
    # Given
    listing = parse_list((FIXTURES / "list-page1.html").read_text(encoding="utf-8"), 1)
    candidate = listing.candidates[index - 1]
    html = (FIXTURES / f"detail-{index}.html").read_text(encoding="utf-8")
    # When
    result = parse_detail(html, candidate)
    # Then
    assert result.title == candidate.title
    assert result.source_key == candidate.source_key
    assert result.body_text == ""
    assert result.image_urls
    assert result.thumbnail_url == result.image_urls[0]
    assert result.posted_on == candidate.posted_on
    assert result.release_on is None
    assert result.is_seasonal is result.is_limited is None


def test_detail_when_body_has_lazy_relative_and_duplicate_images() -> None:
    # Given
    listing = parse_list((FIXTURES / "list-page1.html").read_text(encoding="utf-8"), 1)
    html = '<div class="view_wrap"><div class="view_tit"><h2>음료 안내</h2></div>'
    html += '<div class="view_cont"><script>SECRET</script><style>BAD</style><p>본문</p>'
    html += '<img src="data:image/gif;base64,AAAA" data-src="/wp-content/uploads/a.jpg">'
    html += '<img src="https://paikdabang.com/wp-content/uploads/a.jpg">'
    html += '<img src="javascript:alert(1)"></div></div>'
    # When
    result = parse_detail(html, listing.candidates[0])
    # Then
    assert result.body_text == "본문"
    assert tuple(map(str, result.image_urls)) == (
        "https://paikdabang.com/wp-content/uploads/a.jpg",
    )


@pytest.mark.parametrize(
    "html",
    ["<html>maintenance</html>", "<table><tr><td>changed markup</td></tr></table>"],
)
def test_list_when_markup_is_not_a_recognized_board(html: str) -> None:
    # Given / When / Then
    with pytest.raises(CollectionError, match="LIST_LAYOUT_CHANGED"):
        _ = parse_list(html, 1)


def test_list_when_recognized_board_explicitly_has_no_posts() -> None:
    # Given
    html = '<table><thead><tr><th class="tit">제목</th><th class="date">등록일</th>'
    html += '</tr></thead><tbody><tr><td colspan="5">등록된 게시글이 없습니다.</td></tr>'
    html += "</tbody></table>"
    # When
    result = parse_list(html, 1)
    # Then
    assert result.explicit_empty
    assert result.candidates == ()


def test_detail_when_article_content_is_missing() -> None:
    # Given
    candidate = parse_list((FIXTURES / "list-page1.html").read_text(encoding="utf-8"), 1)
    # When / Then
    with pytest.raises(CollectionError, match="DETAIL_LAYOUT_CHANGED"):
        _ = parse_detail("<html>not an article</html>", candidate.candidates[0])


def test_post_key_when_url_has_tracking_or_different_percent_encoding() -> None:
    # Given
    first = canonical_post_url("https://paikdabang.com/post_news/라떼/?utm_source=test#top")
    second = canonical_post_url("http://www.paikdabang.com/post_news/%eb%9d%bc%eb%96%bc/")
    # When / Then
    assert first == second
    assert post_key(first) == post_key(second)
    assert str(post_key(first)).startswith("url:")


def test_post_key_when_url_is_not_an_official_article() -> None:
    # Given / When / Then
    with pytest.raises(CollectionError, match="INVALID_URL"):
        _ = canonical_post_url("https://example.com/post_news/fake/")
