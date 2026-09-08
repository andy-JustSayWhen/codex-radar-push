import copy
import unittest

from codex_radar_push.core.intelligence import build_report


def point(model="future-model-9", effort="new-effort", iq=100, total=10, minutes=2):
    return {"model": model, "effort": effort, "iq": iq, "total": total,
            "valid_tasks": total, "average_minutes": minutes,
            "source_updated_at": "2026-09-08T08:00:00Z"}


def payload(points):
    return {"schema": 3, "mode": "equal_latest_3", "source_updated_at": "2026-09-08T08:00:00Z", "points": points}


class IntelligenceTests(unittest.TestCase):
    def test_union_and_website_weighted_scores(self):
        report = build_report(payload([point(iq=100, total=10, minutes=2), point("software-only")]),
                              payload([point(iq=130, total=5, minutes=8), point("visual-only")]))
        self.assertEqual(len(report.rows), 3)
        row = next(r for r in report.rows if r.model == "future-model-9")
        self.assertEqual(row.composite, 110)
        self.assertEqual(row.minutes, 4)
        self.assertTrue(all(r.composite is None for r in report.rows if r is not row))

    def test_zero_scores_and_missing_time_are_not_hidden(self):
        report = build_report(payload([point(iq=0, minutes=None)]), payload([point(iq=0)]))
        self.assertEqual(report.rows[0].composite, 0)
        self.assertIsNone(report.rows[0].minutes)

    def test_duplicate_newest_wins_but_ambiguous_conflict_fails(self):
        a = point(iq=90)
        b = dict(a, iq=110, source_updated_at="2026-09-08T09:00:00+00:00")
        report = build_report(payload([b, a, a]), payload([point()]))
        self.assertEqual(report.rows[0].software.score, 110)
        with self.assertRaises(ValueError):
            build_report(payload([a, dict(a, iq=120)]), payload([point()]))

    def test_order_and_fetch_time_do_not_change_fingerprint(self):
        a = payload([point(), point("another-model")])
        b = copy.deepcopy(a)
        b["points"].reverse()
        b["source_updated_at"] = "2026-09-09T08:00:00Z"
        for p in b["points"]:
            p["source_updated_at"] = b["source_updated_at"]
        visual = payload([point()])
        self.assertEqual(build_report(a, visual).change_basis, build_report(b, visual).change_basis)
        b["points"].append(point("new-model"))
        self.assertNotEqual(build_report(a, visual).change_basis, build_report(b, visual).change_basis)

    def test_missing_and_invalid_scores_do_not_fabricate_results(self):
        for invalid in [None, True, float("nan"), float("inf"), "bad", -1]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                build_report(payload([point(iq=invalid)]), payload([point()]))
        with self.assertRaises(ValueError):
            build_report(payload([point(total=0)]), payload([point()]))
        with self.assertRaises(ValueError):
            build_report({"points": {}}, payload([point()]))

    def test_schema_two_weighted_count(self):
        p = payload([point()])
        p["schema"], p["mode"] = 2, "weighted_latest_3"
        p["points"][0].pop("total")
        p["points"][0]["weighted_total"] = 20
        row = build_report(p, payload([point(iq=130, total=10)])).rows[0]
        self.assertEqual(row.composite, 110)


if __name__ == "__main__":
    unittest.main()
