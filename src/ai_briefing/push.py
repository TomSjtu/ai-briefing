from __future__ import annotations

import sys

import httpx


PLACEHOLDER_SENDKEY = "SCT_REPLACE_ME"


def push_to_wechat(http: httpx.Client, sendkey: str, title: str, desp: str) -> bool:
    """把标题和 markdown 正文发到微信。成功返回 True。"""
    if not sendkey or sendkey == PLACEHOLDER_SENDKEY:
        return False
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    try:
        response = http.post(url, json={"title": title, "desp": desp})
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError, TypeError):
        return False
    
    print("[推送] 成功", file=sys.stderr)
    return True
