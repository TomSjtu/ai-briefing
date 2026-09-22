from __future__ import annotations

import re
import sys
from collections.abc import Sequence
from datetime import date, datetime, timezone
from html import unescape
from html.parser import HTMLParser
from typing import Any
from zoneinfo import ZoneInfo

import feedparser
import httpx

from .config import Feed

BEIJING = ZoneInfo("Asia/Shanghai")
USER_AGENT = "ai-briefing/0.1"
SUMMARY_MAX_CHARS = 4000


def collect_day_entries(
    http: httpx.Client,
    report_day: date,
    feeds: Sequence[Feed],
) -> list[dict[str, str]] | None:
    """拉取各源，只返回落在报告日（北京时间）内的条目。全部获取失败返回 None。"""
    collected: list[dict[str, str]] = []
    failed = 0
    print(f"[采集] 开始，共 {len(feeds)} 个源，日期 {report_day.isoformat()}", file=sys.stderr)
    for feed in feeds:
        try:
            response = http.get(
                feed.url,
                headers={"User-Agent": USER_AGENT},
                timeout=15.0,
                follow_redirects=True,
            )
            response.raise_for_status()
            windowed = _window_entries(feed, response.content, report_day)
        except (httpx.HTTPError, ValueError, TypeError):
            failed += 1
            continue
        collected.extend(windowed)
    print(
        f"[采集] 合计当日 {len(collected)} 条，{len(feeds) - failed}/{len(feeds)} 源成功",
        file=sys.stderr,
    )
    if failed == len(feeds):
        return None
    return collected


def _window_entries(feed: Feed, content: bytes, report_day: date) -> list[dict[str, str]]:
    parsed = feedparser.parse(content)
    if not parsed.version:
        raise ValueError("unparseable feed")
    entries: list[dict[str, str]] = []
    for raw in parsed.entries:
        published = _published_at(raw)
        if published is None:
            continue
        beijing_day = published.astimezone(BEIJING).date()
        if beijing_day != report_day:
            continue
        title = (raw.get("title") or "").strip()
        url = (raw.get("link") or "").strip()
        if not title or not url:
            continue
        entries.append(
            {
                "source": feed.name,
                "title": title,
                "summary": _entry_text(raw),
                "url": url,
                "published": beijing_day.isoformat(),
            }
        )
    return entries


def _entry_text(raw: Any) -> str:
    """优先用 feed 内 content 摘录，没有再用 summary；去 HTML 并截断。"""
    content_plain = [_plain_text(value) for value in _content_values(raw)]
    content_plain = [text for text in content_plain if text]
    if content_plain:
        text = max(content_plain, key=len)
    else:
        summary = raw.get("summary")
        text = _plain_text(summary) if isinstance(summary, str) else ""
    return text[:SUMMARY_MAX_CHARS]


def _content_values(raw: Any) -> list[str]:
    blocks = raw.get("content")
    if not isinstance(blocks, list):
        return []
    values: list[str] = []
    for block in blocks:
        value = block.get("value") if hasattr(block, "get") else None
        if isinstance(value, str) and value.strip():
            values.append(value)
    return values


class _HTMLToText(HTMLParser):
    _SKIP = frozenset({"script", "style"})
    _BREAK = frozenset({"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._SKIP:
            self._skip += 1
        elif tag in self._BREAK:
            self._chunks.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._skip:
            self._skip -= 1
        elif tag in self._BREAK:
            self._chunks.append(" ")

    def handle_data(self, data: str) -> None:
        if self._skip == 0:
            self._chunks.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", "".join(self._chunks)).strip()


def _plain_text(value: str) -> str:
    raw = value.strip()
    if not raw:
        return ""
    if "<" not in raw:
        return re.sub(r"\s+", " ", unescape(raw)).strip()
    parser = _HTMLToText()
    parser.feed(raw)
    parser.close()
    return parser.text()


def _published_at(entry: Any) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed is None:
        return None
    return datetime(*parsed[:6], tzinfo=timezone.utc)
