# Codex Radar Refresh Push Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Hermes `no_agent` cron task that pushes WeChat messages when Codex Radar reset, quota, or IQ radar sections refresh.

**Architecture:** Use FCMA: `features/radar_refresh_alert` owns the user-facing alert workflow, `core` owns fetching/parsing/state/Hermes cron integration, and `shared` owns pure helpers. The watcher computes per-section fingerprints, persists last seen state, and prints a message only when a section changes so Hermes can deliver it.

**Tech Stack:** Python 3 standard library, `unittest`, and Hermes cron `no_agent` script mode.

---

### Task 1: Local FCMA Skeleton And Tests

**Files:**
- Create: `codex_radar_push/shared/text.py`
- Create: `codex_radar_push/shared/hashing.py`
- Create: `codex_radar_push/core/models.py`
- Create: `codex_radar_push/core/radar_parser.py`
- Create: `codex_radar_push/features/radar_refresh_alert/runner.py`
- Create: `tests/test_radar_parser.py`
- Create: `tests/test_runner.py`

- [ ] **Step 1: Write failing parser tests**

```python
def test_parse_quota_from_static_html():
    html = "<section class='quota-radar'><h2>额度雷达 <span>7月2日15:34更新</span></h2><div class='quota-radar-row'><strong>20x Pro</strong><span>$272.76</span><span>$1,636.56</span><em>实测</em></div></section>"
    snapshot = parse_radar_snapshot({"model_iq": {"latest": {"date": "2026-07-02-pm_2", "score": 105.0, "status": "green"}}}, html)
    assert snapshot.sections["quota"].updated_at == "7月2日15:34更新"
    assert "$1,636.56" in snapshot.sections["quota"].summary
```

- [ ] **Step 2: Run parser test and verify it fails**

Run: `python3 -m unittest tests.test_radar_parser -v`

- [ ] **Step 3: Implement minimal parser**

Use standard-library `html.parser` plus regex fallback to extract:
- reset radar update time and cards from HTML
- quota radar update time, rows, trend, formula from HTML
- IQ latest date/score/status from JSON

- [ ] **Step 4: Write failing runner tests**

```python
def test_first_run_stores_baseline_without_message():
    changed, message = evaluate_snapshot(snapshot, empty_state)
    assert changed == []
    assert message == ""
```

- [ ] **Step 5: Run runner test and verify it fails**

Run: `python3 -m unittest tests.test_runner -v`

- [ ] **Step 6: Implement runner state comparison**

Persist JSON state containing per-section fingerprints. First run writes baseline and does not print an alert. Later runs print only changed sections.

### Task 2: NAS Deployment Artifacts

**Files:**
- Create: `scripts/codex_radar_refresh_watch.py`
- Create: `scripts/install_hermes_job.py`
- Create: `agent.md`
- Create: `00 index.md`

- [ ] **Step 1: Write CLI wrapper**

`scripts/codex_radar_refresh_watch.py` imports the feature runner and exits with code 0 when unchanged, because Hermes should not treat no-change as a failure.

- [ ] **Step 2: Write Hermes job installer**

`scripts/install_hermes_job.py` edits the configured Hermes jobs file, removes old job `codexradar-model-iq`, adds new job `codexradar-refresh-alert`, and keeps a timestamped backup.

- [ ] **Step 3: Write local docs**

`agent.md` explains FCMA boundaries and NAS deployment. `00 index.md` lists project files.

### Task 3: Verification And NAS Cutover

**Files:**
- Modify in the configured project directory.
- Modify the configured Hermes jobs file.
- Remove the legacy script after verification.

- [ ] **Step 1: Run local tests**

Run: `python3 -m unittest discover -v`

- [ ] **Step 2: Copy project to NAS**

Deploy to `CODEX_RADAR_PROJECT_DIR`.

- [ ] **Step 3: Run NAS tests**

Run: `PYTHONPATH="$CODEX_RADAR_PROJECT_DIR" python3 -m unittest discover -s "$CODEX_RADAR_PROJECT_DIR/tests" -v`

- [ ] **Step 4: Run watcher twice on NAS**

First run stores baseline with no alert. Second run should be no-change. A forced state mutation test should print one alert.

- [ ] **Step 5: Install Hermes cron job**

Run installer inside the deployed project.

- [ ] **Step 6: Remove old A script after B is usable**

Back up and remove the legacy script; remove its old job from `jobs.json`.
