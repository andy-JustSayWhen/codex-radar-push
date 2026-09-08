import unittest

from codex_radar_push.core.radar_parser import parse_radar_snapshot


class RadarParserTests(unittest.TestCase):
    def test_parse_quota_from_static_html(self):
        html = """
        <section class="quota-radar" aria-label="额度雷达">
          <div class="quota-radar-head">
            <h2>额度雷达 <span>7月2日15:34更新</span></h2>
          </div>
          <div class="quota-radar-table">
            <div class="quota-radar-row">
              <strong>20x Pro</strong>
              <span>$272.76</span>
              <span>$1,636.56</span>
              <em>实测</em>
            </div>
          </div>
          <div class="quota-radar-trend-head">
            <strong>额度变化趋势</strong>
            <span>$1,897.32 → $1,636.56 (-$260.76, -13.7%)</span>
          </div>
          <p>本次公式：20x Pro 5h = $114.56 / (43% - 1%) * 100 = $272.76；其中 1% 为测量任务本身的消耗。</p>
        </section>
        """

        snapshot = parse_radar_snapshot(
            {
                "model_iq": {
                    "latest": {
                        "date": "2026-07-02-pm_2",
                        "score": 105.0,
                        "status": "green",
                        "passed": 7,
                        "tasks": 10,
                    }
                }
            },
            html,
        )

        quota = snapshot.sections["quota"]
        self.assertEqual(quota.updated_at, "7月2日15:34更新")
        self.assertIn("20x Pro 5h $272.76 / 7d $1,636.56 (实测)", quota.summary)
        self.assertIn("-13.7%", quota.summary)
        self.assertIn("20x Pro 5h =", quota.summary)

    def test_parse_reset_and_iq_sections(self):
        html = """
        <section class="reset-judgement" aria-label="重置雷达研判">
          <h2>重置雷达研判 <em>7月2日16:12研判</em></h2>
          <article class="reset-judgement-card">
            <span>发重置卡</span>
            <strong>高 · 基本已触发</strong>
            <p>官方信号强。</p>
          </article>
        </section>
        <section class="model-iq model-iq-green" aria-label="Codex 雷达">
          <h2>降智雷达 <span>7月2日15:42更新</span></h2>
        </section>
        """

        snapshot = parse_radar_snapshot(
            {
                "model_iq": {
                    "latest": {
                        "date": "2026-07-02-pm_2",
                        "score": 105.0,
                        "status": "green",
                        "passed": 7,
                        "tasks": 10,
                    }
                }
            },
            html,
        )

        reset = snapshot.sections["reset"]
        iq = snapshot.sections["iq"]
        self.assertEqual(reset.updated_at, "7月2日16:12研判")
        self.assertIn("发重置卡：高 · 基本已触发", reset.summary)
        self.assertEqual(iq.updated_at, "2026-07-02-pm_2")
        self.assertIn("未知模型", iq.summary)
        self.assertIn("105", iq.summary)

    def test_reset_fingerprint_ignores_time_and_prose_but_tracks_action(self):
        first = parse_radar_snapshot({}, self._reset_html("7月3日08:08研判", "官方信号强。"))
        same_description = parse_radar_snapshot({}, self._reset_html("7月3日10:09研判", "官方信号强。"))
        changed_description = parse_radar_snapshot({}, self._reset_html("7月3日12:10研判", "社区反证仍在。"))
        changed_status = parse_radar_snapshot(
            {},
            self._reset_html("7月3日14:16研判", "官方信号强。", reset_status="中 · 观察中"),
        )
        changed_signal = parse_radar_snapshot(
            {},
            self._reset_html("7月3日14:16研判", "官方信号强。", signal="硬重置风险上升"),
        )

        first_reset = first.sections["reset"]
        self.assertEqual(first_reset.updated_at, "7月3日08:08研判")
        self.assertEqual(first_reset.fingerprint, same_description.sections["reset"].fingerprint)
        self.assertEqual(first_reset.fingerprint, changed_description.sections["reset"].fingerprint)
        self.assertNotEqual(first_reset.fingerprint, changed_status.sections["reset"].fingerprint)
        self.assertNotEqual(first_reset.fingerprint, changed_signal.sections["reset"].fingerprint)

    def test_iq_legacy_snapshot_uses_all_structured_rows_without_html_cards(self):
        snapshot = parse_radar_snapshot({"model_iq": {
            "latest": {"model": "future-primary", "score": 100, "date": "2026-09-08"},
            "comparisons": {
                "another-model": {"label": "Future model", "latest": {"score": 0}},
            },
        }}, "<section class='changed-layout'>stale model names</section>")
        iq = snapshot.sections["iq"]
        self.assertIn("future-primary", iq.summary)
        self.assertIn("Future model", iq.summary)
        self.assertNotIn("stale model names", iq.summary)
        self.assertEqual(iq.updated_at, "2026-09-08")

    def _reset_html(self, updated_at, description, reset_status="高 · 基本已触发", signal="发卡路径占优"):
        return f"""
        <section class="reset-judgement" aria-label="重置雷达研判">
          <div class="reset-judgement-head">
            <h2>重置雷达研判 <em>{updated_at}</em></h2>
            <strong>{signal}</strong>
          </div>
          <article class="reset-judgement-card">
            <span>发重置卡</span>
            <strong>{reset_status}</strong>
            <p>Tibo 最新回复：{description}</p>
          </article>
          <article class="reset-judgement-card">
            <span>硬重置</span>
            <strong>低到中低</strong>
            <p>硬重置动机本轮仍弱。</p>
          </article>
        </section>
        """


if __name__ == "__main__":
    unittest.main()
