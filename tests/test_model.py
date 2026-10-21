import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build  # noqa: E402
from engine import business_case  # noqa: E402
from tests.xlsx_eval import Workbook  # noqa: E402

M = build.compute()
BC, PF, RD, REPORT = M["bc"], M["portfolio"], M["readiness"], M["report"]
RANKED = [r for r in PF["ranking"] if r["rank"]]


class BusinessCaseTest(unittest.TestCase):
    def test_minutes_saved_by_hand(self):
        v = business_case.pick(BC["values"])
        review = 1 - v["stp_rate"] - v["manual_rate"]
        after = v["stp_rate"] * 0.3 + review * 2.5 + v["manual_rate"] * 5.5
        self.assertAlmostEqual(BC["base"]["saved_minutes_per_document"], round(5.5 - after, 3), places=3)

    def test_payback(self):
        self.assertEqual(business_case.payback_months([120, 120, 120], 60), 6.0)
        self.assertEqual(business_case.payback_months([60, 120], 120), 18.0)
        self.assertIsNone(business_case.payback_months([-10, -10], 50))

    def test_cash_never_exceeds_capacity(self):
        for y in BC["base"]["years"]:
            self.assertLessEqual(y["cash_fte"], y["fte_freed"])

    def test_pilot_numbers_flow_into_the_case(self):
        self.assertEqual(BC["values"]["stp_rate"]["base"], REPORT["test"]["stp_rate"])
        self.assertEqual(BC["values"]["pilot_escape_rate"]["base"], REPORT["pooled_escape_rate"])


class ClaimsTest(unittest.TestCase):
    """Sentences in the documents that are not generated, checked against the model."""

    def test_portfolio_claims(self):
        self.assertEqual(RANKED[0]["id"], "UC-01")
        self.assertGreaterEqual(RANKED[0]["top1"], 0.99)
        self.assertLess(RANKED[1]["score"] - RANKED[4]["score"], 0.1, "prioritization.md: places 2-5 within about 0.1")
        for uc in ("UC-05", "UC-06"):
            self.assertEqual(next(r for r in PF["ranking"] if r["id"] == uc)["top3"], 0.0)
        parked = [r["id"] for r in PF["ranking"] if r["parked"]]
        self.assertEqual(parked, ["UC-08"])

    def test_business_case_claims(self):
        rows = BC["tornado"]["rows"]
        self.assertEqual([rows[0]["key"], rows[1]["key"]], ["attrition_fte", "error_cost"])
        stp = next(r for r in rows if r["key"] == "stp_rate")
        self.assertLess(stp["swing"], rows[0]["swing"] / 5, "the straight-through rate is a small driver")
        self.assertLess(BC["scenarios"]["pessimistic"]["cash"]["npv"], 0, "pessimistic case loses money")
        self.assertLessEqual(BC["cash_if_all_leavers_replaced"]["payback_months"], 24)
        self.assertAlmostEqual(BC["base"]["years"][1]["fte_freed"], 2.4, delta=0.05, msg="article: about 2.4 FTE")

    def test_pilot_claims(self):
        ab = REPORT["test_ablation"]
        self.assertEqual((ab["A"]["escapes"], ab["B"]["escapes"], ab["D"]["escapes"]), (36, 14, 0), "deck, article, demo script")
        self.assertAlmostEqual(ab["A"]["stp_rate"], 0.955, places=3)
        self.assertEqual(REPORT["ablation_dev"]["D"]["escapes"], 2, "pilot-results: 2 dev escapes")
        demo = json.loads((ROOT / "site/data/pilot.json").read_text())
        doc = next(d for d in demo["documents"] if d["id"] == "DOC-0084")
        self.assertEqual(doc["received"], "2026-09-08")
        self.assertTrue(any(r.startswith("V11") for r in doc["reasons"]))
        self.assertTrue(any(r.startswith("V13") for r in doc["reasons"]))

    def test_readiness_claims(self):
        self.assertAlmostEqual(RD["overall"], 1.9, delta=0.05)
        self.assertEqual(min(RD["dimensions"], key=lambda d: d["current"])["name"], "People & skills")


class WorkbookTest(unittest.TestCase):
    def test_roi_workbook_reproduces_the_model(self):
        wb = Workbook(ROOT / "04-business-case/roi-calculator.xlsx")
        self.assertAlmostEqual(wb.value("Model", "B26"), BC["base"]["cash"]["npv"], delta=20)
        self.assertAlmostEqual(wb.value("Model", "B25"), BC["base"]["capacity"]["npv"], delta=20)

    def test_readiness_workbook_reproduces_the_model(self):
        wb = Workbook(ROOT / "02-ai-readiness/readiness-scorecard.xlsx")
        n = len(RD["dimensions"]) + 2
        self.assertAlmostEqual(wb.value("Summary", f"B{n}"), RD["overall"], places=2)

    def test_scoring_workbook_ranks_like_the_model(self):
        wb = Workbook(ROOT / "03-opportunity-discovery/use-case-scoring.xlsx")
        rank_col = "Q"
        ranks = {wb.value("Scoring", f"A{r}"): wb.value("Scoring", f"{rank_col}{r}") for r in range(8, 18)}
        for row in PF["ranking"]:
            self.assertEqual(ranks[row["id"]], row["rank"] if row["rank"] else "-", row["id"])


class SiteTest(unittest.TestCase):
    def test_browser_model_matches(self):
        try:
            out = subprocess.run(["node", str(ROOT / "scripts/check_js.js")], capture_output=True, text=True)
        except FileNotFoundError:
            self.skipTest("node not installed")
        self.assertEqual(out.returncode, 0, out.stderr)


if __name__ == "__main__":
    unittest.main()
