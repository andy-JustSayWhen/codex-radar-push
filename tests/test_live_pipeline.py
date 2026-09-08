import io
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from codex_radar_push.core.codex_radar_client import fetch_intelligence
from codex_radar_push.core.intelligence import build_report
from codex_radar_push.core.iq_table import format_intelligence_table, _display_width
from codex_radar_push.core.radar_parser import parse_radar_snapshot
from codex_radar_push.features.radar_query.runner import query_latest
from codex_radar_push.features.radar_refresh_alert.runner import evaluate_snapshot, run
from test_intelligence import payload, point


class LivePipelineTests(unittest.TestCase):
    def setUp(self):
        self.software = payload([point("gpt-6-astra", "ultra"), point("全新模型-name", "future")])
        self.visual = payload([point("gpt-6-astra", "ultra", iq=130), point("visual-only", "anything")])
        self.report = build_report(self.software, self.visual)

    def response(self, value, cache="HIT"):
        response = io.BytesIO(json.dumps(value).encode())
        response.headers = {"X-Codex-Cache": cache}
        return response

    def test_real_endpoint_contract_and_no_legacy_fetch(self):
        paths = []

        def fetch(request, timeout):
            paths.append(request.full_url)
            return self.response(self.visual if request.full_url.endswith("visual-spatial-reasoning") else self.software)

        with patch("codex_radar_push.core.codex_radar_client._open_url", side_effect=fetch):
            self.assertEqual(fetch_intelligence(), self.report)
        self.assertEqual(set(paths), {
            "https://codex-reset-radar.pages.dev/api/intelligence-efficiency-metrics",
            "https://codex-reset-radar.pages.dev/api/visual-spatial-reasoning",
        })

    def test_stale_or_unknown_cache_is_not_silently_used(self):
        for status in ("STALE", "STALE-IF-ERROR", "ERROR", ""):
            with self.subTest(status=status), patch(
                "codex_radar_push.core.codex_radar_client._open_url",
                side_effect=lambda *a, **kw: self.response(self.software, status),
            ), self.assertRaises(ValueError):
                fetch_intelligence()

    def test_table_has_all_models_full_names_and_aligned_columns(self):
        message = format_intelligence_table(self.report)
        self.assertIn("3 个模型 / 3 个档位", message)
        self.assertEqual(message.count("```"), 2)
        self.assertNotIn("```text", message)
        for row in self.report.rows:
            self.assertEqual(message.count(row.name), 1)
        table = message.split("```\n")[1].split("\n```")[0].splitlines()
        self.assertEqual(len({_display_width(line) for line in table}), 1)
        self.assertIn("115.00", message)
        self.assertIn("—", message)
        self.assertIn("工程数据：09-08 16:00", message)

    def test_iq_query_does_not_depend_on_html_or_model_regex(self):
        with patch("codex_radar_push.features.radar_query.runner.fetch_intelligence", return_value=self.report), patch(
            "codex_radar_push.features.radar_query.runner.fetch_html", side_effect=AssertionError("HTML unnecessary")
        ):
            message = query_latest("codex智商")
        for row in self.report.rows:
            self.assertIn(row.name, message)

    def test_new_model_survives_cooldown_and_is_delivered_in_full_table(self):
        before = parse_radar_snapshot({}, "", self.report)
        updated = payload(self.software["points"] + [point("unreleased-model-99", "unknown")])
        after = parse_radar_snapshot({}, "", build_report(updated, self.visual))
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.json"
            evaluate_snapshot(before, state, now=1000)
            # Seed a previous alert to exercise the cooldown.
            saved = json.loads(state.read_text())
            saved["last_alert_at"] = 1000
            state.write_text(json.dumps(saved))
            self.assertEqual(evaluate_snapshot(after, state, now=1010), ([], ""))
            changed, message = evaluate_snapshot(after, state, now=1600)
            self.assertEqual(changed, ["iq"])
            self.assertIn("unreleased-model-99 unknown", message)
            self.assertEqual(message.count("```"), 2)
            self.assertEqual(evaluate_snapshot(after, state, now=1700), ([], ""))

    def test_bad_payload_does_not_advance_watcher_state(self):
        now = datetime(2026, 9, 8, 12, tzinfo=ZoneInfo("Asia/Shanghai")).timestamp()
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.json"
            state.write_text('{"sentinel": true}')
            with patch("codex_radar_push.features.radar_refresh_alert.runner.fetch_intelligence", side_effect=ValueError("invalid")):
                with self.assertRaises(ValueError):
                    run(state, now=now)
            self.assertEqual(state.read_text(), '{"sentinel": true}')


if __name__ == "__main__":
    unittest.main()
