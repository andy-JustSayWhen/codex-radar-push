---
name: codex-radar
description: "查询 Codex 雷达最新状态。用户提到 codex雷达、codex额度、codex智商、codex降智、codex重置、Codex quota、Codex IQ、Codex reset 时使用。"
version: 3.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [codex, quota, radar, query, weixin]
---

# Codex Radar Query

Use this skill when Andy asks for Codex Radar status, including:

- `codex雷达`
- `codex额度`
- `codex智商`
- `codex降智`
- `codex重置`
- Codex quota / Codex IQ / Codex reset

## Required Behavior

Run the query script and reply with its stdout only. Do not summarize, rewrite, or add a management footer.

```bash
cd /opt/data/codex-radar-push
python3 scripts/codex_radar_query.py "<USER_MESSAGE>"
```

Routing:

- `codex雷达` or generic Codex Radar query: returns reset + quota + IQ.
- `codex额度`: returns quota radar only.
- `codex智商` or `codex降智`: returns IQ radar only.
- `codex重置`: returns reset radar only.

## Notes

- The query script uses public Codex Radar data from `https://codex-reset-radar.pages.dev/`.
- The scheduled push job is separate: `codexradar-refresh-alert`.
- Do not run independent quota tests. Only fetch and report Codex Radar data.
