# 00 Index

## Project Files

- `codex_radar_push/features/radar_refresh_alert/runner.py`: alert feature workflow, Beijing quiet-hour suppression, auto-refresh message formatting, fenced-code wrapping for single-bubble WeChat delivery, transient fetch timeout handling, and alert cooldown.
- `codex_radar_push/core/radar_display.py`: compact multiline radar display for Hermes query and refresh messages, including separate IQ recommendations for quality and value.
- `codex_radar_push/core/iq_table.py`: formats the scheduled IQ push as an aligned monospace block directly from stable `current.json` model data.
- `codex_radar_push/core/codex_radar_client.py`: HTTP fetch for HTML and `current.json`.
- `codex_radar_push/core/radar_parser.py`: reset, quota, and IQ radar parsing; reset change fingerprints ignore judgement time and long prose, and track only actionable reset labels/statuses, while IQ replies include the current multi-model score cards and recent GPT-5.5-xhigh trend.
- `codex_radar_push/core/state_store.py`: JSON state load/save and change detection.
- `codex_radar_push/core/models.py`: radar snapshot and section dataclasses.
- `codex_radar_push/shared/text.py`: pure HTML/text helpers, including exact `<section>` class-token extraction.
- `codex_radar_push/shared/hashing.py`: pure stable hashing helper.
- `scripts/codex_radar_refresh_watch.py`: Hermes `no_agent` script entrypoint.
- `scripts/hermes_cron_codex_radar_refresh_watch.py`: Python wrapper copied to `/opt/data/scripts` for Hermes cron.
- `scripts/codex_radar_query.py`: Hermes keyword query entrypoint.
- `scripts/codex_radar_iq_table.py`: scheduled Feishu IQ table entrypoint.
- `scripts/install_hermes_job.py`: installs the new Hermes cron job and removes the old daily Codex Radar job from `jobs.json`.
- `hermes_skill/codex-radar/SKILL.md`: Hermes skill instructions for `codex雷达` / `codex额度` / `codex智商` / `codex重置`.
- `docs/adr/0001-hermes-cron-script-location.md`: records why Hermes cron uses a wrapper under `/opt/data/scripts`.
- `docs/glossary.md`: project terms for FCMA, Hermes cron scripts, wrappers, and deployment directories.
- `tests/`: unit tests for parser and runner behavior.
- `knowledge/消息渠道的选择.md`: channel selection, runtime target configuration, delivery verification, and privacy boundaries.
- `knowledge/消息格式及示例.md`: Feishu-safe monospace formatting rules and examples.

## Notes

- First watcher run stores baseline and prints nothing.
- Later runs print only changed radar sections, wrapped in a fenced text block so Hermes WeChat delivery keeps the multiline card in one message bubble.
- Reset radar auto-alerts are not triggered by judgement time refresh or long prose rewrites alone; they require actionable reset labels/statuses to change.
- Beijing quiet hours are 23:00 through 06:59; scheduled refresh alerts return empty output and do not fetch during that window.
- Transient Codex Radar fetch timeouts are skipped silently so Hermes does not send cron failure noise.
- Refresh alerts have a 10-minute delivery cooldown to avoid WeChat iLink rate limits during bursty radar updates.
- The scheduled IQ table job delivers printed output to its configured Feishu target.
- Deploy into the target Hermes data directory configured by the operator.
- Hermes job name: `codexradar-refresh-alert`, schedule `5 * * * *`, with the delivery target supplied at runtime.
- Removed old job `codexradar-model-iq`; old script was backed up before removal.
