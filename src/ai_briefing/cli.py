from __future__ import annotations

import argparse

import httpx
from dotenv import load_dotenv

from .runner import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-briefing",
        description="采集当日条目，提取早报并写入本地和推送",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="生成 Markdown 和 JSON 报告，但不推送",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    with httpx.Client(timeout=httpx.Timeout(180.0, connect=10.0)) as client:
        return run(http=client, dry_run=args.dry_run)
