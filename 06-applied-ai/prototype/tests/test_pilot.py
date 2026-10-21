import json
import unittest
from dataclasses import replace
from types import SimpleNamespace

from evals.run import THRESHOLDS, load, pick_threshold, run
from freightdoc.extract import RulesProvider, classify, extract, parse_date, parse_number
from freightdoc.pipeline import POLICIES, Result, link_shipments, process, route
from freightdoc.providers.claude import SCHEMA, ClaudeProvider
from freightdoc.reference import iso6346_check_digit, iso6346_valid
from freightdoc.validate import check_document

BL = """BILL OF LADING
B/L number: NSLU12345678
Shipper: Calderwick Paper Ltd
Consignee: Oostveld Machinery NV
Vessel: Celtic Mariner
Port of loading: GBTIL
Port of discharge: BEZEE
Container no: CSQU3054383
Seal no: SL1234567
Packages: 120 PKGS
Gross weight: 18.443,4 kg
Issue date: 12/09/2026"""


class ReferenceTest(unittest.TestCase):
    def test_iso6346_known_example(self):
        # The worked example from the ISO 6346 standard.
        self.assertEqual(iso6346_check_digit("CSQU305438"), 3)
        self.assertTrue(iso6346_valid("CSQU3054383"))
        self.assertFalse(iso6346_valid("CSQU3054384"))
        self.assertFalse(iso6346_valid("CSQU30543B3"))


class ExtractTest(unittest.TestCase):
    def test_numbers_in_both_notations(self):
        self.assertEqual(parse_number("18.443,4 kg"), 18443.4)
        self.assertEqual(parse_number("18,443.4 KG"), 18443.4)
        self.assertEqual(parse_number("18.443 kg"), 18443.0)
        self.assertEqual(parse_number("6392.5 kg"), 6392.5)
        self.assertEqual(parse_number("850,3 kg"), 850.3)
        self.assertEqual(parse_number("40,675 lbs"), 40675.0)

    def test_dates(self):
        self.assertEqual(parse_date("2026-09-12", 0)[0], "2026-09-12")
        self.assertEqual(parse_date("23/09/2026", 0)[:2], ("2026-09-23", 0.95))
        value, conf, note = parse_date("09/23/2026", 0)
        self.assertEqual((value, conf), ("2026-09-23", 0.85))
        value, conf, note = parse_date("04/09/2026", 0)
        self.assertEqual((value, conf), ("2026-09-04", 0.7))
        self.assertIn("ambiguous", note)
        self.assertEqual(parse_date("04/09/2026", 3)[0], "2026-04-09")

    def test_bill_of_lading(self):
        doc_type, conf, _ = classify(BL)
        self.assertEqual(doc_type, "bill_of_lading")
        self.assertGreater(conf, 0.75)
        fields = extract(BL, doc_type)
        self.assertEqual(fields["containers"].value, ["CSQU3054383"])
        self.assertEqual(fields["gross_weight_kg"].value, 18443.4)
        self.assertEqual(fields["issue_date"].value, "2026-09-12")
        self.assertEqual(fields["port_of_loading"].value, "GBTIL")

    def test_ocr_lookalike_is_repaired_with_lower_confidence(self):
        fields = extract(BL.replace("CSQU3054383", "CSQU3O54383"), "bill_of_lading")
        self.assertEqual(fields["containers"].value, ["CSQU3054383"])
        self.assertEqual(fields["containers"].confidence, 0.75)

    def test_unreadable_field_abstains(self):
        fields = extract(BL.replace("120 PKGS", "[illegible]"), "bill_of_lading")
        self.assertIsNone(fields["packages"].value)
        self.assertEqual(fields["packages"].confidence, 0.0)

    def test_ocr_damaged_label_still_found(self):
        fields = extract(BL.replace("Consignee", "Consignce"), "bill_of_lading")
        self.assertEqual(fields["consignee"].value, "Oostveld Machinery NV")
        self.assertLess(fields["consignee"].confidence, 0.95)

    def test_non_freight_document_is_other(self):
        self.assertEqual(classify("PORT NEWSLETTER\nVolumes rose.\nVessel: MV Noordster")[0], "other")


class ValidateTest(unittest.TestCase):
    def test_clean_bill_passes(self):
        fields = extract(BL, "bill_of_lading")
        failed = [c.rule for c in check_document("bill_of_lading", fields, "2026-09-15") if not c.ok]
        self.assertEqual(failed, [])

    def test_wrong_check_digit_and_missing_seal(self):
        text = BL.replace("CSQU3054383", "CSQU3054384").replace("Seal no: SL1234567\n", "")
        fields = extract(text, "bill_of_lading")
        failed = {c.rule for c in check_document("bill_of_lading", fields, "2026-09-15") if not c.ok}
        self.assertEqual(failed, {"V01", "V03"})


class PipelineTest(unittest.TestCase):
    def test_policies_route_differently(self):
        docs = [{"id": "X", "received": "2026-09-15", "text": BL.replace("120 PKGS", "###")}]
        self.assertEqual(process(docs, policy=POLICIES["A"])[0].route, "auto")
        self.assertEqual(process(docs, policy=POLICIES["D"])[0].route, "review")

    def test_other_documents_go_to_manual(self):
        r = route(Result("X", "2026-09-15", "other", 0.9, {}), POLICIES["D"])
        self.assertEqual(r.route, "manual")

    def test_packing_list_without_bl_reference_links_by_container(self):
        pl = ("PACKING LIST\nPacking list no: PL-1\nContainer no: CSQU3054383\nPackages: 120\n"
              "Gross weight: 20.000 kg\nNet weight: 18.000 kg")
        docs = [{"id": "B", "received": "2026-09-15", "text": BL},
                {"id": "P", "received": "2026-09-15", "text": pl}]
        results = process(docs)
        self.assertEqual(link_shipments(results)["P"], "NSLU12345678")
        packing = next(r for r in results if r.id == "P")
        self.assertEqual(packing.route, "review")
        self.assertTrue(any(reason.startswith("V11") for reason in packing.reasons))

    def test_tms_record_only_for_auto(self):
        docs = [{"id": "B", "received": "2026-09-15", "text": BL}]
        out = process(docs)[0].as_dict()
        self.assertEqual(out["route"], "auto")
        self.assertEqual(out["tms_record"]["reference"], "NSLU12345678")


class EvalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report, _, _ = run()

    def test_gate_passes(self):
        failed = [c["check"] for c in self.report["gate"]["checks"] if not c["pass"]]
        self.assertEqual(failed, [])

    def test_each_layer_removes_escapes(self):
        escapes = [self.report["test_ablation"][k]["escapes"] for k in "ABCD"]
        self.assertEqual(escapes, sorted(escapes, reverse=True))
        self.assertGreater(escapes[0], 10 * max(escapes[-1], 1))

    def test_threshold_respects_floor_and_budget(self):
        rows = [{"threshold": 0.5, "stp_rate": 0.9, "error_escape_rate": 0.0},
                {"threshold": 0.75, "stp_rate": 0.7, "error_escape_rate": 0.0},
                {"threshold": 0.8, "stp_rate": 0.8, "error_escape_rate": 0.02}]
        self.assertEqual(pick_threshold(rows, 0.01, 0.75), 0.75)
        self.assertGreaterEqual(self.report["chosen_threshold"], THRESHOLDS["min_threshold"])

    def test_report_is_committed_and_current(self):
        from evals.run import EVALS
        committed = json.loads((EVALS / "report.json").read_text())
        self.assertEqual(committed["test"], json.loads(json.dumps(self.report["test"])))


class FakeClient:
    def __init__(self, payload, stop_reason="end_turn"):
        self.payload, self.stop_reason, self.calls = payload, stop_reason, []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls.append(kwargs)
        text = SimpleNamespace(type="text", text=json.dumps(self.payload))
        return SimpleNamespace(stop_reason=self.stop_reason, content=[text])


class ClaudeProviderTest(unittest.TestCase):
    PAYLOAD = {"document_type": "bill_of_lading", "fields": [
        {"name": "bl_number", "value": "NSLU12345678", "status": "read"},
        {"name": "gross_weight_kg", "value": "18.443,4 kg", "status": "read"},
        {"name": "packages", "value": "120", "status": "uncertain"},
        {"name": "seal_numbers", "value": "", "status": "unreadable"},
        {"name": "cmr_number", "value": "CMR1", "status": "read"},
    ]}

    def test_request_shape(self):
        client = FakeClient(self.PAYLOAD)
        ClaudeProvider(client=client).read(BL)
        call = client.calls[0]
        self.assertEqual(call["model"], "claude-opus-5-5")
        self.assertEqual(call["fallbacks"], "default")
        self.assertIn("server-side-fallback-2026-07-01", call["betas"])
        self.assertEqual(call["output_config"]["format"]["schema"], SCHEMA)
        self.assertIn("<document>", call["messages"][0]["content"])

    def test_model_reads_code_normalises(self):
        doc_type, _, fields = ClaudeProvider(client=FakeClient(self.PAYLOAD)).read(BL)
        self.assertEqual(doc_type, "bill_of_lading")
        self.assertEqual(fields["gross_weight_kg"].value, 18443.4)
        self.assertEqual(fields["packages"].confidence, 0.6)
        self.assertIsNone(fields["seal_numbers"].value)
        self.assertNotIn("cmr_number", fields)

    def test_refusal_goes_to_manual(self):
        provider = ClaudeProvider(client=FakeClient(self.PAYLOAD, stop_reason="refusal"))
        result = process([{"id": "X", "received": "2026-09-15", "text": BL}], provider=provider)[0]
        self.assertEqual(result.route, "manual")


class DataTest(unittest.TestCase):
    def test_sets_have_the_planned_mix(self):
        for name in ("dev", "test"):
            docs, truth = load(name)
            self.assertEqual(len(docs), 220)
            self.assertEqual(sum(t["type"] == "other" for t in truth.values()), 10)

    def test_rules_provider_never_sees_truth(self):
        import inspect
        import freightdoc.extract as extract_module
        self.assertNotIn("truth", inspect.getsource(extract_module))
        self.assertEqual(RulesProvider.name, "rules")


if __name__ == "__main__":
    unittest.main()
