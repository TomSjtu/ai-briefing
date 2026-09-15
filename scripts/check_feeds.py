"""读取 feeds.yaml，检查每个 RSS/Atom 源能否拉取并解析。

连通性由使用者负责；本脚本只做手动探测，不参与每日早报。
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

import feedparser
import httpx
import yaml

from ai_briefing.config import Feed, load_feeds
from ai_briefing.feeds import USER_AGENT

TIMEOUT = httpx.Timeout(15.0, connect=10.0)


def probe_feed(http: httpx.Client, feed: Feed) -> tuple[str | None, int]:
    """探测一个源。成功返回 (None, 条目数)，失败返回 (短错误码, 0)。"""
    try:
        response = http.get(
            feed.url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        if not parsed.version:
            return "unparseable feed", 0
        return None, len(parsed.entries)
    except httpx.HTTPStatusError as exc:
        return f"HTTP {exc.response.status_code}", 0
    except httpx.TimeoutException:
        return "timeout", 0
    except httpx.HTTPError:
        return "network error", 0
    except (ValueError, TypeError):
        return "unparseable feed", 0


def format_line(feed: Feed, error: str | None, entry_count: int) -> str:
    status = "ok" if error is None else "fail"
    detail = f"{entry_count} entries" if error is None else error
    return f"{status:4}  {feed.source_id:24}  {feed.name}  {detail}"


def run_checks(http: httpx.Client, feeds: Sequence[Feed]) -> int:
    """打印每个源的探测结果。没有源或任一失败返回 1。"""
    failed = 0
    for feed in feeds:
        error, entry_count = probe_feed(http, feed)
        print(format_line(feed, error, entry_count))
        if error is not None:
            failed += 1
    print(f"{len(feeds) - failed} ok, {failed} failed")
    if not feeds:
        print("没有可检查的信息源", file=sys.stderr)
        return 1
    return 1 if failed else 0


def main(*, http: httpx.Client | None = None) -> int:
    try:
        feeds = load_feeds()
    except (OSError, ValueError, TypeError, AttributeError, yaml.YAMLError) as exc:
        print(f"数据源配置无效：{exc}", file=sys.stderr)
        return 1
    if http is not None:
        return run_checks(http, feeds)
    with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
        return run_checks(client, feeds)


if __name__ == "__main__":
    raise SystemExit(main())
