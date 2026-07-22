import unittest

from codex_radar_push.core.models import RadarSection, RadarSnapshot
from codex_radar_push.core.radar_display import format_radar_message


class RadarDisplayTests(unittest.TestCase):
    def test_formats_visual_summary_for_all_sections(self):
        snapshot = RadarSnapshot(
            sections={
                "reset": RadarSection(
                    "reset",
                    "重置雷达",
                    "7月2日18:06研判",
                    "发重置卡：高 · 基本已触发\n硬重置：低到中低",
                ),
                "quota": RadarSection(
                    "quota",
                    "额度雷达",
                    "7月2日15:34更新",
                    "\n".join(
                        [
                            "20x Pro 5h $272.76 / 7d $1,636.56 (实测)",
                            "5x Pro 5h $68.19 / 7d $409.14 (推测)",
                            "Plus 5h $13.64 / 7d $81.83 (推测)",
                            "趋势：$1,897.32 → $1,636.56 (-$260.76, -13.7%)",
                            "近5次：2026-07-01-am $1,658.63 | 2026-07-01-pm $1,726.56 | 2026-07-02 $1,825.74 | 2026-07-02-pm $1,897.32 | 2026-07-02-pm_2 $1,636.56",
                        ]
                    ),
                ),
                "iq": RadarSection(
                    "iq",
                    "智商雷达",
                    "7月2日15:42更新",
                    "\n".join(
                        [
                            "本次 Codex 多模型智商测试共消耗等价 $114.56 的 API 费用。",
                            "GPT-5.5-xhigh 105.0 (green) 7/10 费用 $37.0 耗时 2.2h date=2026-07-02-pm_2",
                            "GPT-5.5-medium 105.0 (green) 7/10 费用 $19.1 耗时 1.2h date=2026-07-02-pm_2",
                        ]
                    ),
                ),
            }
        )

        message = format_radar_message(snapshot, ["reset", "quota", "iq"], "Codex 雷达刷新")

        self.assertIn("重置卡：高 · 基本已触发", message)
        self.assertIn("20x Pro 7d 近5次", message)
        self.assertIn("$1,659 → $1,727 → $1,826 → $1,897 → $1,637", message)
        self.assertIn("本次变化：-$260.76（-13.7%）", message)
        self.assertIn("GPT-5.5 medium", message)
        self.assertIn("█████████░  $19.1  1.2h", message)
        self.assertIn("保质量：GPT-5.5 medium（105 green，7/10）", message)
        self.assertIn("性价比：GPT-5.5 medium（105 green，$19.1，1.2h）", message)

    def test_iq_recommendations_split_quality_and_value(self):
        snapshot = RadarSnapshot(
            sections={
                "iq": RadarSection(
                    "iq",
                    "智商雷达",
                    "7月5日07:58更新",
                    "\n".join(
                        [
                            "本次 Codex 多模型智商测试共消耗等价 $129.34 的 API 费用。",
                            "GPT-5.5-xhigh 60.0 (red) 4/10 费用 $36.5 耗时 2.2h date=2026-07-05-am",
                            "GPT-5.5-high 105.0 (green) 7/10 费用 $24.7 耗时 1.7h date=2026-07-05-am",
                            "GPT-5.5-medium 90.0 (yellow) 6/10 费用 $19.2 耗时 1.3h date=2026-07-05-am",
                            "GPT-5.5-low 60.0 (red) 4/10 费用 $13.7 耗时 1.3h date=2026-07-05-am",
                            "GPT-5.4-xhigh 90.0 (yellow) 6/10 费用 $21.8 耗时 2.8h date=2026-07-05-am",
                            "GPT-5.4-high 90.0 (yellow) 6/10 费用 $13.4 耗时 1.8h date=2026-07-05-am",
                        ]
                    ),
                )
            }
        )

        message = format_radar_message(snapshot, ["iq"], "Codex 雷达刷新")

        self.assertIn("保质量：GPT-5.5 high（105 green，7/10）", message)
        self.assertIn("性价比：GPT-5.4 high（90 yellow，$13.4，1.8h）", message)


if __name__ == "__main__":
    unittest.main()
