from __future__ import annotations

from datetime import date
from typing import Any


def render_report(report_date: date, briefing: dict[str, Any]) -> str:
    """把早报 JSON 渲成变体 A markdown：日期标题、导语、各条标题与 why、来源链接。"""
    lines = [
        f"# AI 科技早报 · {report_date.month} 月 {report_date.day} 日",
        "",
        briefing["lead"],
        "",
    ]
    for item in briefing["items"]:
        lines.append(f"**{item['headline']}。** {item['why']}")
        lines.append(f"来源：{item['source']} · [原文]({item['url']})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
