# AI 科技早报

个人用 AI/科技行业早报。采集当日条目，提取成短中文叙事，先落盘再推到自己的微信。

## 环境

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## 安装

```bash
uv sync
cp .env.example .env
```

在 `.env` 里填入：

- `OPENAI_API_KEY`、`OPENAI_MODEL`（必填）
- `OPENAI_BASE_URL`（选填，默认官方 Chat Completions）
- `SERVERCHAN_SENDKEY`（推送时必填；`--dry-run` 可省略。占位值 `SCT_REPLACE_ME` 不会被当成推送成功）

## 运行

```bash
uv run ai-briefing
```

只生成 `reports/` 下当天的 Markdown（`.md`）和 JSON（`.json`），不推送微信：

```bash
uv run ai-briefing --dry-run
```