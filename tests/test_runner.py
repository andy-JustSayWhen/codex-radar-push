from datetime import datetime
import tempfile
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo
from unittest.mock import patch

from codex_radar_push.core.models import RadarSection, RadarSnapshot
from codex_radar_push.core.state_store import changed_sections
from codex_radar_push.features.radar_refresh_alert.runner import evaluate_snapshot, format_message, is_quiet_time, run


class RunnerTests(unittest.TestCase):
    def _snapshot(self, reset="r1", quota="q1", iq="i1"):
        return RadarSnapshot(
            sections={
                "reset": RadarSection("reset", "重置雷达", "t1", reset),
                "quota": RadarSection("quota", "额度雷达", "t1", quota),
                "iq": RadarSection("iq", "智商雷达", "t1", iq),
            }
        )

    def test_first_run_reports_all_sections_and_stores_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"

            changed, message = evaluate_snapshot(self._snapshot(), state_path)

            self.assertEqual(changed, ["reset", "quota", "iq"])
            self.assertIn("Codex 雷达刷新", message)
            self.assertTrue(state_path.exists())

    def test_changed_section_returns_wechat_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            evaluate_snapshot(self._snapshot(), state_path, now=1000)

            changed, message = evaluate_snapshot(self._snapshot(quota="q2"), state_path, now=3000)

            self.assertEqual(changed, ["quota"])
            self.assertIn("Codex 雷达刷新", message)
            self.assertIn("额度雷达", message)
            self.assertIn("q2", message)

    def test_cooldown_keeps_pending_change_for_next_alert(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            evaluate_snapshot(self._snapshot(), state_path, now=1000)
            changed, message = evaluate_snapshot(self._snapshot(quota="q2"), state_path, now=3000)
            self.assertEqual(changed, ["quota"])
            self.assertIn("q2", message)

            changed, message = evaluate_snapshot(self._snapshot(quota="q3"), state_path, now=3010)

            self.assertEqual(changed, [])
            self.assertEqual(message, "")
            self.assertNotIn("q3", state_path.read_text(encoding="utf-8"))
            changed, message = evaluate_snapshot(self._snapshot(quota="q3"), state_path, now=4800)
            self.assertEqual(changed, ["quota"])
            self.assertIn("q3", message)

    def test_reset_basis_migration_does_not_alert_when_action_matches(self):
        state = {
            "sections": {
                "reset": {
                    "fingerprint": "old-time-based-fingerprint",
                    "summary": "发重置卡：高 · 基本已触发\n硬重置：低到中低",
                    "change_basis": (
                        "重置雷达 发卡路径占优 发重置卡 高 · 基本已触发 "
                        "旧版长解释正文 硬重置 低到中低"
                    ),
                }
            }
        }
        snapshot = RadarSnapshot(
            sections={
                "reset": RadarSection(
                    "reset",
                    "重置雷达",
                    "7月3日12:10研判",
                    "发重置卡：高 · 基本已触发\n硬重置：低到中低",
                    "发卡路径占优\n发重置卡：高 · 基本已触发\n硬重置：低到中低",
                )
            }
        )

        self.assertEqual(changed_sections(state, snapshot), [])

    def test_reset_prose_change_does_not_alert_after_action_baseline_exists(self):
        baseline = RadarSection(
            "reset",
            "重置雷达",
            "7月3日10:09研判",
            "发重置卡：高 · 基本已触发\n硬重置：低到中低",
            "发卡路径占优\n发重置卡：高 · 基本已触发\n硬重置：低到中低",
        )
        state = {
            "sections": {
                "reset": {
                    "fingerprint": baseline.fingerprint,
                    "summary": baseline.summary,
                    "change_basis": baseline.change_basis,
                }
            }
        }
        snapshot = RadarSnapshot(
            sections={
                "reset": RadarSection(
                    "reset",
                    "重置雷达",
                    "7月3日12:10研判",
                    "发重置卡：高 · 基本已触发\n硬重置：低到中低",
                    "发卡路径占优\n发重置卡：高 · 基本已触发\n硬重置：低到中低",
                )
            }
        )

        self.assertEqual(changed_sections(state, snapshot), [])

    def test_reset_action_change_alerts_after_new_baseline_exists(self):
        baseline = RadarSection(
            "reset",
            "重置雷达",
            "7月3日10:09研判",
            "发重置卡：高 · 基本已触发\n硬重置：低到中低",
            "发卡路径占优\n发重置卡：高 · 基本已触发\n硬重置：低到中低",
        )
        state = {
            "sections": {
                "reset": {
                    "fingerprint": baseline.fingerprint,
                    "summary": baseline.summary,
                    "change_basis": baseline.change_basis,
                }
            }
        }
        snapshot = RadarSnapshot(
            sections={
                "reset": RadarSection(
                    "reset",
                    "重置雷达",
                    "7月3日12:10研判",
                    "发重置卡：高 · 基本已触发\n硬重置：中",
                    "发卡路径占优\n发重置卡：高 · 基本已触发\n硬重置：中",
                )
            }
        )

        self.assertEqual(changed_sections(state, snapshot), ["reset"])

    def test_refresh_message_uses_compact_multiline_card_layout(self):
        message = format_message(self._snapshot(reset="发重置卡：高\n硬重置：低到中低"), ["reset"])

        self.assertTrue(message.startswith("```text\n"))
        self.assertTrue(message.endswith("\n```"))
        self.assertIn("\n", message)
        self.assertIn("Codex 雷达刷新", message)
        self.assertIn("重置雷达  t1", message)
        self.assertIn("重置卡：高", message)
        self.assertIn("硬重置：低到中低", message)

    def test_run_silently_skips_transient_fetch_timeout(self):
        with patch("codex_radar_push.features.radar_refresh_alert.runner.fetch_intelligence", side_effect=TimeoutError):
            self.assertEqual(run(now=self._beijing_timestamp(2026, 9, 8, 12, 0)), "")

    def test_quiet_time_uses_beijing_23_to_7_window(self):
        self.assertFalse(is_quiet_time(self._beijing_timestamp(2026, 7, 2, 22, 59)))
        self.assertTrue(is_quiet_time(self._beijing_timestamp(2026, 7, 2, 23, 0)))
        self.assertTrue(is_quiet_time(self._beijing_timestamp(2026, 7, 3, 6, 59)))
        self.assertFalse(is_quiet_time(self._beijing_timestamp(2026, 7, 3, 7, 0)))

    def test_run_skips_fetch_during_quiet_time(self):
        with patch("codex_radar_push.features.radar_refresh_alert.runner.fetch_intelligence") as fetch:
            message = run(now=self._beijing_timestamp(2026, 7, 2, 23, 0))

            self.assertEqual(message, "")
            fetch.assert_not_called()

    def _beijing_timestamp(self, year, month, day, hour, minute):
        return datetime(year, month, day, hour, minute, tzinfo=ZoneInfo("Asia/Shanghai")).timestamp()


if __name__ == "__main__":
    unittest.main()
