from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import feedparser
import httpx

from .config import Feed

BEIJING = ZoneInfo("Asia/Shanghai")
USER_AGENT = "ai-briefing/0.1"


def collect_day_entries(
    http: httpx.Client,
    report_day: date,
    feeds: Sequence[Feed],
) -> list[dict[str, str]] | None:
    """拉取各源，只返回落在报告日（北京时间）内的条目。全部获取失败返回 None。"""
    collected: list[dict[str, str]] = []
    failed = 0
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
                "summary": (raw.get("summary") or "").strip(),
                "url": url,
                "published": beijing_day.isoformat(),
            }
        )
    return entries


def _published_at(entry: Any) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed is None:
        return None
    return datetime(*parsed[:6], tzinfo=timezone.utc)
