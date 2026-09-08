# AGENTS.md

## Purpose Of This File

This file is for coding agents that maintain this code repository. It defines the engineering architecture and maintenance rules for feature development.

It is **not** application runtime content, a Hermes skill, a Hermes prompt, a cron instruction, or an end-user usage guide. Do not copy this file into the NAS/Hermes application deployment directory. Hermes-facing behavior belongs in `hermes_skill/codex-radar/SKILL.md` and thin scripts under `scripts/`.

## Project Purpose

This project provides Hermes-compatible Codex Radar automation:

- scheduled refresh detection for reset, quota, and IQ radar updates
- on-demand keyword queries for `codex雷达`, `codex额度`, `codex智商`, `codex降智`, and `codex重置`
- deployment into an operator-configured Hermes data directory

## Architecture: FCMA

This project must follow **FCMA: Feature-Centric Modular Architecture**.

All code must belong to exactly one of these layers:

- `codex_radar_push/features/`: user-facing features and complete workflows
- `codex_radar_push/core/`: system capabilities such as fetchers, parsers, state storage, and Hermes integration
- `codex_radar_push/shared/`: pure helper functions with no business logic and no IO

Dependency direction is strict:

```text
features -> core -> shared
```

Allowed:

- `features` may import `core` and `shared`
- `core` may import `shared`
- `shared` may import only standard library or other pure shared helpers

Forbidden:

- `core` importing from `features`
- `shared` importing from `core` or `features`
- feature modules importing directly from other feature modules
- putting business logic in `shared`
- creating generic catch-all files such as `utils.py` for unrelated helpers
- organizing primary code by technical type such as `controllers/`, `services/`, `models/`, or `utils/`

## Current Module Ownership

### Features

- `features/radar_refresh_alert/`: scheduled refresh alert workflow. Compares snapshots, persists state through core, and formats change alerts for Hermes delivery. Auto-trigger messages must stay silent during Beijing quiet hours from 23:00 through 06:59; manual query replies are not quiet-hour gated. Auto-trigger messages should be printed once as a compact multiline card, not line-by-line. Transient fetch timeouts must not fail the cron job, and refresh alerts use a 30-minute cooldown that preserves pending changes for the next eligible run.
- `features/radar_query/`: on-demand query workflow. Resolves user keywords and formats the requested radar sections.

### Core

- `core/codex_radar_client.py`: fetches HTML and the live software intelligence endpoint; validates current cache responses.
- `core/intelligence.py`: normalizes all GPT model/effort records. See `docs/SPEC-model-discovery.md` and `docs/design-model-discovery.md`.
- `core/radar_display.py`: compact Hermes text display for reset and quota, and GPT score tables for IQ snapshots.
- `core/iq_table.py`: formats all live intelligence rows into an aligned, unlabeled fenced block with model abbreviations, scores and integer minutes.
- `core/radar_parser.py`: converts reset/quota HTML and normalized intelligence reports into snapshots. Reset fingerprints track actionable status changes. IQ fingerprints track the complete sorted model set and measurements independently of fetch times.
- `core/state_store.py`: JSON state persistence and fingerprint change detection.
- `core/models.py`: dataclasses for radar sections and snapshots.

### Shared

- `shared/text.py`: pure HTML/text normalization helpers.
- `shared/hashing.py`: pure stable hashing helper.

## Scripts

- `scripts/codex_radar_refresh_watch.py`: Hermes `no_agent` cron entrypoint. Prints only when a radar section changed.
- `scripts/codex_radar_query.py`: Hermes keyword-query entrypoint. Prints current radar status for all or selected sections.
- `scripts/codex_radar_iq_table.py`: Hermes scheduled IQ-table entrypoint. Prints all current model scores and average task times for Feishu delivery.
- `scripts/install_hermes_job.py`: installs the Hermes cron job and removes the old daily Codex Radar job.

Scripts are thin entrypoints only. Business workflow belongs in `features/`; IO and integration belong in `core/`.

## Testing

Use standard library `unittest`; do not introduce new runtime dependencies unless clearly necessary.

Run locally:

```bash
python3 -m unittest discover -s tests -v
```

Run in the target Hermes environment:

```bash
PYTHONPATH="$CODEX_RADAR_PROJECT_DIR" python3 -m unittest discover -s "$CODEX_RADAR_PROJECT_DIR/tests" -v
```

## Operational Context

Configure deployment paths through environment variables. Do not place `AGENTS.md` inside the deployed application:

- project: `CODEX_RADAR_PROJECT_DIR`
- Hermes data directory: `HERMES_DATA_DIR`
- delivery target: `CODEX_RADAR_DELIVERY_TARGET`

Installer defaults for a new refresh watcher (existing deployments retain their configured schedules):

- name: `codexradar-refresh-alert`
- schedule: `5 * * * *`
- mode: `no_agent: true`
- delivery: explicit runtime target

Scheduling rationale:

- Codex Radar sections do not update every 3 minutes.
- Run at minute 5 each hour so known hourly/windowed updates are checked after a short delay, while unknown updates are still checked hourly.
- The scheduled watcher returns empty output during Beijing quiet hours from 23:00 through 06:59. It does not fetch or update state during that window, so the next daytime run can report accumulated changes.

## Maintenance Rules

- Before adding code, decide whether it belongs in `features`, `core`, or `shared`.
- Keep each feature as a complete workflow boundary.
- Add or update tests before behavior changes.
- Update `00 index.md` and `AGENTS.md` when structure or operational behavior changes.
- Keep `AGENTS.md` repository-only. Exclude it from runtime/application deployment artifacts.
- Do not restore the removed old daily script `scripts/codexradar_model_iq.py`; it was replaced by FCMA watcher/query code.
