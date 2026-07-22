# 00 Index

- `features/radar_refresh_alert/`: change-detection workflow for Codex Radar refresh alerts; auto-trigger messages skip Beijing quiet hours from 23:00 through 06:59, use a compact multiline card layout wrapped in a fenced text block for single-bubble WeChat delivery, skip transient fetch timeouts, and enforce a 10-minute alert cooldown.
- `features/radar_query/`: on-demand keyword query workflow for Hermes replies.
- `core/codex_radar_client.py`: fetches Codex Radar HTML and `current.json`.
- `core/radar_display.py`: formats reset, quota, and IQ snapshots into compact Hermes text cards, with separate IQ quality and value recommendations.
- `core/radar_parser.py`: parses reset, quota, and IQ radar sections into snapshots; reset change fingerprints ignore judgement time and long prose, and track only actionable reset labels/statuses, while IQ parsing includes current multi-model cards and recent GPT-5.5-xhigh trend.
- `core/state_store.py`: persists fingerprints and detects changed sections.
- `core/models.py`: dataclasses for radar sections and snapshots.
- `shared/text.py`: pure text and HTML helper functions, including exact `<section>` class-token extraction.
- `shared/hashing.py`: pure stable hash helper.
