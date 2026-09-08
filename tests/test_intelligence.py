import copy
import unittest

from codex_radar_push.core.intelligence import build_report


def point(model="gpt-9-future", effort="new-effort", iq=100, total=10, minutes=2):
    return {"model": model, "effort": effort, "iq": iq, "total": total,
            "valid_tasks": total, "average_minutes": minutes,
            "source_updated_at": "2026-09-08T08:00:00Z"}


def payload(points):
    return {"schema": 3, "mode": "equal_latest_3", "source_updated_at": "2026-09-08T08:00:00Z", "points": points}


class IntelligenceTests(unittest.TestCase):
    def test_all_gpt_models_and_unknown_efforts_are_included(self):
        report = build_report(payload([point(), point("claude-test", iq="irrelevant"),
                                       point("gpt-6-astra", "max"), point("gpt-5.5", "high")]))
        self.assertEqual(len(report.rows), 3)
        self.assertEqual({r.model for r in report.rows}, {"gpt-9-future", "gpt-6-astra", "gpt-5.5"})
        self.assertEqual(report.rows[0].effort, "new-effort")

    def test_zero_scores_and_missing_time_are_not_hidden(self):
        report = build_report(payload([point(iq=0, minutes=None)]))
        self.assertEqual(report.rows[0].software.score, 0)
        self.assertIsNone(report.rows[0].software.minutes)

    def test_duplicate_newest_wins_but_ambiguous_conflict_fails(self):
        a = point(iq=90)
        b = dict(a, iq=110, source_updated_at="2026-09-08T09:00:00+00:00")
        report = build_report(payload([b, a, a]))
        self.assertEqual(report.rows[0].software.score, 110)
        with self.assertRaises(ValueError):
            build_report(payload([a, dict(a, iq=120)]))

    def test_order_and_fetch_time_do_not_change_fingerprint(self):
        a = payload([point(), point("gpt-8-another")])
        b = copy.deepcopy(a)
        b["points"].reverse()
        b["source_updated_at"] = "2026-09-09T08:00:00Z"
        for p in b["points"]:
            p["source_updated_at"] = b["source_updated_at"]
        self.assertEqual(build_report(a).change_basis, build_report(b).change_basis)
        b["points"].append(point("another-provider", iq=120))
        b["points"][0]["total"] = 50
        self.assertEqual(build_report(a).change_basis, build_report(b).change_basis)
        b["points"].append(point("gpt-10-new"))
        self.assertNotEqual(build_report(a).change_basis, build_report(b).change_basis)

    def test_missing_and_invalid_scores_do_not_fabricate_results(self):
        for invalid in [None, True, float("nan"), float("inf"), "bad", -1]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                build_report(payload([point(iq=invalid)]))
        with self.assertRaises(ValueError):
            build_report(payload([point(total=0)]))
        with self.assertRaises(ValueError):
            build_report({"points": {}})

    def test_schema_two_weighted_count(self):
        p = payload([point()])
        p["schema"], p["mode"] = 2, "weighted_latest_3"
        p["points"][0].pop("total")
        p["points"][0]["weighted_total"] = 20
        row = build_report(p).rows[0]
        self.assertEqual(row.software.tasks, 20)


if __name__ == "__main__":
    unittest.main()
