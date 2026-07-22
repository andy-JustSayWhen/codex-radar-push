# Glossary

## FCMA

Feature-Centric Modular Architecture. Code is organized by feature first, with shared system capabilities in `core` and pure helpers in `shared`.

## Hermes Home

The persistent Hermes data directory, configured through `HERMES_DATA_DIR` for the target environment.

## Hermes Cron Script

The `script` field on a Hermes cron job. Hermes resolves this field relative to `/opt/data/scripts`, not relative to the job `workdir`.

## Wrapper Script

A small Python executable under `/opt/data/scripts` that satisfies Hermes cron script resolution and delegates to the real project script under `/opt/data/codex-radar-push`. Hermes executes cron scripts with Python, so shell wrappers are invalid here.

## Project Script

The source-controlled entrypoint under `scripts/`, such as `scripts/codex_radar_refresh_watch.py`. These scripts are part of the project and are not directly referenced by Hermes cron.

## Runtime Deployment Directory

The deployed application copy under `CODEX_RADAR_PROJECT_DIR`. Repository-only files such as `AGENTS.md` must not be copied there.
