from __future__ import annotations

import pytest
from selectolax.lexbor import LexborHTMLParser

from launch_collector.adapters import Candidate
from launch_collector.errors import CollectionError
from launch_collector.html_content import content_from_body
from launch_collector.models import SourceKey
from launch_collector.urls import brand_url


def test_content_when_image_only_article_has_lazy_official_media() -> None:
    # Given
    candidate = Candidate(
        source_key=SourceKey("news:1"),
        source_url=brand_url("/news/1", "compose"),
        title="sample",
        posted_on=None,
        thumbnail_url=None,
    )
    body = LexborHTMLParser(
        """<article><script>secret</script>
        <img src="data:image/png;x" data-src="/files/a.jpg"><img src="/files/a.jpg">
        <img src="https://evil.test/tracker.jpg"></article>"""
    ).css_first("article")
    assert body is not None
    # When
    post = content_from_body(body, candidate, "compose")
    # Then
    assert post.body_text == ""
    assert tuple(map(str, post.image_urls)) == ("https://composecoffee.com/files/a.jpg",)
    assert post.thumbnail_url == post.image_urls[0]
    assert post.release_on is None
    assert post.is_seasonal is None


def test_content_when_script_is_the_only_body_content() -> None:
    # Given
    candidate = Candidate(
        source_key=SourceKey("news:1"),
        source_url=brand_url("/news/1", "compose"),
        title="sample",
        posted_on=None,
        thumbnail_url=None,
    )
    body = LexborHTMLParser("<article><script>unsafe()</script></article>").css_first("article")
    assert body is not None
    # When / Then
    with pytest.raises(CollectionError, match="EMPTY_CONTENT"):
        _ = content_from_body(body, candidate, "compose")
