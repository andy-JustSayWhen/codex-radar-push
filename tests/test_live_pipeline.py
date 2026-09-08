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
        self.software = payload([point("gpt-6-astra", "ultra"), point("gpt-9-全新模型", "future")])
        self.report = build_report(self.software)

    def response(self, value, cache="HIT"):
        response = io.BytesIO(json.dumps(value).encode())
        response.headers = {"X-Codex-Cache": cache}
        return response

    def test_real_endpoint_contract_and_no_legacy_fetch(self):
        paths = []

        def fetch(request, timeout):
            paths.append(request.full_url)
            return self.response(self.software)

        with patch("codex_radar_push.core.codex_radar_client._open_url", side_effect=fetch):
            self.assertEqual(fetch_intelligence(), self.report)
        self.assertEqual(set(paths), {
            "https://codex-reset-radar.pages.dev/api/intelligence-efficiency-metrics",
        })

    def test_stale_or_unknown_cache_is_not_silently_used(self):
        for status in ("STALE", "STALE-IF-ERROR", "ERROR", ""):
            with self.subTest(status=status), patch(
                "codex_radar_push.core.codex_radar_client._open_url",
                side_effect=lambda *a, **kw: self.response(self.software, status),
            ), self.assertRaises(ValueError):
                fetch_intelligence()

    def test_three_column_format_matches_user_example(self):
        report = build_report(payload([
            point("gpt-5.6-sol", "xhigh", iq=102.2, minutes=24.6),
            point("gpt-5.6-sol", "max", iq=109, minutes=33.1),
            point("gpt-5.6-terra", "max", iq=106.3, minutes=32),
            point("gpt-5.5", "xhigh", iq=106.3, minutes=23),
            point("other-provider", "high", iq=150),
        ]))
        message = format_intelligence_table(report, datetime(2026, 9, 8, 14, 30))
        self.assertEqual(message, "\n".join([
            "降智雷达：14:30", "", "```",
            "模型                 分数  耗时",
            "Sol max               109  33分钟",
            "Sol xhigh           102.2  25分钟",
            "Terra max           106.3  32分钟",
            "5.5 xhigh           106.3  23分钟",
            "```",
        ]))

    def test_new_names_missing_time_and_name_collisions(self):
        report = build_report(payload([point("gpt-9-future", "unknown", minutes=None),
                                       point("gpt-10-future", "unknown", iq=0)]))
        message = format_intelligence_table(report)
        self.assertIn("9 future unknown", message)
        self.assertIn("10 future unknown", message)
        self.assertIn("—", message)
        self.assertNotIn("综合", message)
        self.assertNotIn("数据：", message)
        self.assertEqual(message.count("```"), 2)

    def test_iq_query_does_not_depend_on_html_or_model_regex(self):
        with patch("codex_radar_push.features.radar_query.runner.fetch_intelligence", return_value=self.report), patch(
            "codex_radar_push.features.radar_query.runner.fetch_html", side_effect=AssertionError("HTML unnecessary")
        ):
            message = query_latest("codex智商")
        self.assertIn("Astra ultra", message)
        self.assertIn("全新模型 future", message)
        self.assertEqual(message, format_intelligence_table(self.report))

    def test_new_model_survives_cooldown_and_is_delivered_in_full_table(self):
        before = parse_radar_snapshot({}, "", self.report)
        updated = payload(self.software["points"] + [point("gpt-99-unreleased", "unknown")])
        after = parse_radar_snapshot({}, "", build_report(updated))
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.json"
            evaluate_snapshot(before, state, now=1000)
            # Seed a previous alert to exercise the cooldown.
            saved = json.loads(state.read_text())
            saved["last_alert_at"] = 1000
            state.write_text(json.dumps(saved))
            self.assertEqual(evaluate_snapshot(after, state, now=1010), ([], ""))
            changed, message = evaluate_snapshot(after, state, now=2800)
            self.assertEqual(changed, ["iq"])
            self.assertIn("Unreleased unknown", message)
            self.assertEqual(message.count("```"), 2)
            self.assertEqual(evaluate_snapshot(after, state, now=2900), ([], ""))

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
