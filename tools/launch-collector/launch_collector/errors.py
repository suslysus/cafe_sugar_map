"""Stable collection failures reported without response bodies or credentials."""

from __future__ import annotations


class CollectionError(Exception):
    def __init__(self, code: str) -> None:
        self.code: str = code
        super().__init__(code)
