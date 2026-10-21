"""Claude as the reading step. Same interface as RulesProvider.

Division of labour: the model reads (type, field values, what it could not
read); deterministic code normalises every value with the same parsers as the
offline provider and computes the confidence the router uses. A model's own
confidence numbers are not calibrated, so we do not ask for them: we ask for
a status per field and calibrate the threshold per provider in evals/run.py.

Needs `pip install anthropic` and credentials (ANTHROPIC_API_KEY or
`ant auth login`). Every document is one API call and costs money.
"""

import json
import os
from pathlib import Path

from ..extract import Field, locale_hint, parse_value
from ..reference import DOC_TYPES, FIELDS

MODEL = os.environ.get("FREIGHTDOC_MODEL", "claude-opus-5-5")
PROMPT_FILE = Path(__file__).resolve().parents[2] / "prompts" / "extract.md"
ALL_FIELDS = sorted({name for spec in FIELDS.values() for name in spec})

SCHEMA = {
    "type": "object",
    "properties": {
        "document_type": {"type": "string", "enum": list(DOC_TYPES) + ["other"]},
        "fields": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "enum": ALL_FIELDS},
                    "value": {"type": "string"},
                    "status": {"type": "string", "enum": ["read", "uncertain", "unreadable"]},
                },
                "required": ["name", "value", "status"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["document_type", "fields"],
    "additionalProperties": False,
}

STATUS_CAP = {"read": 1.0, "uncertain": 0.6, "unreadable": 0.0}


class ClaudeProvider:
    name = "claude"

    def __init__(self, client=None, model=MODEL):
        if client is None:
            import anthropic  # optional dependency, only needed for this provider
            client = anthropic.Anthropic()
        self.client = client
        self.model = model
        self.system = PROMPT_FILE.read_text(encoding="utf-8")

    def request(self, text):
        return dict(
            model=self.model,
            max_tokens=8192,
            # Safety classifiers can decline; "default" re-runs a declined
            # request on the fallback model Anthropic recommends.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium",
                           "format": {"type": "json_schema", "schema": SCHEMA}},
            system=self.system,
            messages=[{"role": "user", "content": f"<document>\n{text}\n</document>"}],
        )

    def read(self, text):
        response = self.client.beta.messages.create(**self.request(text))
        if response.stop_reason == "refusal":
            return "other", 0.0, {}          # routes to manual handling
        body = next(b.text for b in response.content if b.type == "text")
        return self.parse(json.loads(body), text)

    def parse(self, data, text):
        doc_type = data["document_type"]
        if doc_type == "other":
            return "other", 0.9, {}
        spec = FIELDS[doc_type]
        hint = locale_hint(text)
        fields = {}
        for item in data["fields"]:
            name = item["name"]
            if name not in spec:
                continue                      # a field this document type does not have
            if item["status"] == "unreadable" or not item["value"].strip():
                fields[name] = Field(None, 0.0, item["value"], "unreadable")
                continue
            parsed = parse_value(spec[name][0], item["value"], hint)
            cap = STATUS_CAP[item["status"]]
            if parsed.confidence > cap:
                parsed.confidence = cap
                parsed.note = "; ".join(x for x in (parsed.note, "model marked it uncertain") if x)
            fields[name] = parsed
        return doc_type, 0.95, fields
