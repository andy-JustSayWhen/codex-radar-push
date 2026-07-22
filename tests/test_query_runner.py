import unittest

from codex_radar_push.core.models import RadarSection, RadarSnapshot
from codex_radar_push.features.radar_query.runner import format_query_response, resolve_query_sections


class QueryRunnerTests(unittest.TestCase):
    def _snapshot(self):
        return RadarSnapshot(
            sections={
                "reset": RadarSection("reset", "重置雷达", "7月2日16:12研判", "重置摘要"),
                "quota": RadarSection("quota", "额度雷达", "7月2日15:34更新", "额度摘要"),
                "iq": RadarSection("iq", "智商雷达", "7月2日15:42更新", "智商摘要"),
            }
        )

    def test_resolve_query_sections_from_keywords(self):
        self.assertEqual(resolve_query_sections("codex额度"), ["quota"])
        self.assertEqual(resolve_query_sections("codex智商"), ["iq"])
        self.assertEqual(resolve_query_sections("codex重置"), ["reset"])
        self.assertEqual(resolve_query_sections("codex雷达"), ["reset", "quota", "iq"])

    def test_format_query_response_for_single_section(self):
        message = format_query_response(self._snapshot(), ["quota"])

        self.assertIn("Codex 雷达最新状态", message)
        self.assertIn("额度雷达  15:34", message)
        self.assertIn("额度摘要", message)
        self.assertNotIn("重置摘要", message)

    def test_format_query_response_for_all_sections(self):
        message = format_query_response(self._snapshot(), ["reset", "quota", "iq"])

        self.assertIn("重置摘要", message)
        self.assertIn("额度摘要", message)
        self.assertIn("智商摘要", message)


if __name__ == "__main__":
    unittest.main()
