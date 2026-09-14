from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

from ai_briefing.config import load_feeds, load_settings
from ai_briefing.extract import extract_content
from ai_briefing.feeds import collect_day_entries
from ai_briefing.push import push_to_wechat
from ai_briefing.render import render_report

BEIJING = ZoneInfo("Asia/Shanghai")


def report_date(now: datetime | None = None) -> date:
    """返回 now 对应的北京日历日；now 为空则取当前时间。"""
    current = now or datetime.now(BEIJING)
    if current.tzinfo is None:
        current = current.replace(tzinfo=BEIJING)
    return current.astimezone(BEIJING).date()


def run(
    reports_dir: Path = Path("reports"),
    *,
    http: httpx.Client,
    environ: Mapping[str, str] = os.environ,
    now: datetime | None = None,
    entries: Sequence[Mapping[str, str]] | None = None,
    dry_run: bool = False,
) -> int:
    """生成当天早报并写入 Markdown/JSON；非 dry-run 时再推到微信，返回退出码。"""
    settings = load_settings(environ)
    if settings is None:
        print("缺少模型凭证", file=sys.stderr)
        return 1

    day = report_date(now)
    if entries is None:
        try:
            resolved_feeds = load_feeds()
        except (OSError, ValueError) as exc:
            print(f"数据源配置无效：{exc}", file=sys.stderr)
            return 1
        entries = collect_day_entries(http, day, resolved_feeds)
        if entries is None:
            print("获取信息源失败", file=sys.stderr)
            return 1
    briefing = extract_content(http, settings, day, entries)
    if briefing is None:
        print("提取内容失败", file=sys.stderr)
        return 1
    markdown = render_report(day, briefing)
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / f"{day.isoformat()}.md").write_text(markdown, encoding="utf-8")
    (reports_dir / f"{day.isoformat()}.json").write_text(
        json.dumps(briefing, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if dry_run:
        # 设置 dry_run 不要推送
        return 0
    if not push_to_wechat(
        http, settings.serverchan_sendkey, briefing["card_title"], markdown
    ):
        print("推送失败", file=sys.stderr)
        return 1
    return 0
