import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from codex_radar_push.core.iq_table import format_iq_table


class IqTableTests(unittest.TestCase):
    def test_formats_current_json_models_without_html(self):
        model_iq = {
            "latest": {
                "model": "gpt-5.6-sol",
                "reasoning_effort": "max",
                "score": 107.6,
                "average_task_time_human": "35分钟",
            },
            "comparisons": {
                "gpt_56_sol_xhigh": {
                    "label": "GPT-5.6 Sol xhigh",
                    "latest": {"score": 92.8, "average_task_time_human": "28分钟"},
                },
                "gpt_56_terra_max": {
                    "label": "GPT-5.6 Terra max",
                    "latest": {"score": 102.2, "average_task_time_human": "34分钟"},
                },
                "gpt_55_high_distributed": {
                    "label": "GPT-5.5 high",
                    "latest": {"score": 79.4, "average_task_time_human": "16分钟"},
                },
            },
        }
        now = datetime(2026, 7, 22, 14, 30, tzinfo=ZoneInfo("Asia/Shanghai"))

        message = format_iq_table(model_iq, now=now)

        self.assertEqual(
            message,
            "\n".join(
                [
                    "降智雷达：14:30",
                    "",
                    "```",
                    "模型                 分数  耗时",
                    "Sol max             107.6  35分钟",
                    "Sol xhigh            92.8  28分钟",
                    "Terra max           102.2  34分钟",
                    "GPT-5.5 high         79.4  16分钟",
                    "```",
                ]
            ),
        )

    def test_raises_when_current_json_has_no_model_rows(self):
        with self.assertRaisesRegex(ValueError, "没有可用的模型数据"):
            format_iq_table({"latest": {}, "comparisons": {}})


if __name__ == "__main__":
    unittest.main()
