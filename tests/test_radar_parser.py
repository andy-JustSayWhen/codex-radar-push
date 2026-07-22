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
        self.assertEqual(iq.updated_at, "7月2日15:42更新")
        self.assertIn("gpt-5.5", iq.summary)
        self.assertIn("105.0", iq.summary)

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

    def test_parse_iq_section_ignores_readout_class_and_includes_model_cards(self):
        html = """
        <figure class="model-iq-readout">
          <figcaption>7月2日18:06更新</figcaption>
        </figure>
        <section class="model-iq model-iq-green" aria-label="Codex 雷达">
          <div class="model-iq-head">
            <h2>降智雷达 <span>7月2日15:42更新</span></h2>
          </div>
          <p class="model-iq-run-cost-note">本次 Codex 多模型智商测试共消耗等价 $114.56 的 API 费用。可点击卡片筛选要显示的模型。</p>
          <div class="model-iq-score-chip model-iq-score-chip-primary" data-model-key="gpt_55_xhigh">
            <span>GPT-5.5-xhigh</span>
            <div class="model-iq-score-metrics"><strong>105.0</strong><span class="model-iq-score-mini">$37.0</span><span class="model-iq-score-mini">2.2h</span></div>
          </div>
          <div class="model-iq-score-chip model-iq-score-chip-comparison" data-model-key="gpt_55_high">
            <span>GPT-5.5-high</span>
            <div class="model-iq-score-metrics"><strong>75.0</strong><span class="model-iq-score-mini">$23.5</span><span class="model-iq-score-mini">1.5h</span></div>
          </div>
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
                    },
                    "recent_days": [
                        {"date": "2026-07-01-pm", "score": 60.0, "status": "red", "passed": 4, "tasks": 10},
                        {"date": "2026-07-02-pm_2", "score": 105.0, "status": "green", "passed": 7, "tasks": 10},
                    ],
                    "comparisons": {
                        "gpt_55_high": {
                            "latest": {
                                "date": "2026-07-02-pm_2",
                                "score": 75.0,
                                "status": "red",
                                "passed": 5,
                                "tasks": 10,
                            }
                        }
                    },
                }
            },
            html,
        )

        iq = snapshot.sections["iq"]
        self.assertEqual(iq.updated_at, "7月2日15:42更新")
        self.assertIn("本次 Codex 多模型智商测试共消耗等价 $114.56 的 API 费用。", iq.summary)
        self.assertIn("GPT-5.5-xhigh 105.0 (green) 7/10 费用 $37.0 耗时 2.2h", iq.summary)
        self.assertIn("GPT-5.5-high 75.0 (red) 5/10 费用 $23.5 耗时 1.5h", iq.summary)
        self.assertIn("GPT-5.5-xhigh近5次", iq.summary)

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
