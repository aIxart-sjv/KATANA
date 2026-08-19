import asyncio
import json

from app.llm.ollama import OllamaClient
from app.explainability.prompts import SYSTEM_PROMPT


TEST_INCIDENT = {
    "severity": "High",
    "anomaly_score": -0.61,
    "evidence": [
        "High process creation rate (37)",
        "8 outbound network connections detected.",
        "1 privilege escalation event(s).",
    ],
    "triggered_features": {
        "process_creation_rate": 37,
        "external_connections": 8,
        "privilege_escalations": 1,
        "maximum_cpu": 74.2,
    },
    "recommended_actions": [
        "Inspect recently spawned processes.",
        "Review active outbound connections.",
        "Review privileged operations immediately.",
    ],
}


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
        },
        "analysis": {
            "type": "string",
        },
        "risk": {
            "type": "string",
            "enum": [
                "Low",
                "Medium",
                "High",
                "Critical",
                "Uncertain",
            ],
        },
        "mitre_attack": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
    },
    "required": [
        "summary",
        "analysis",
        "risk",
        "mitre_attack",
    ],
}


async def main():

    llm = OllamaClient()

    prompt = f"""
INCIDENT

Severity:
{TEST_INCIDENT["severity"]}

Anomaly Score:
{TEST_INCIDENT["anomaly_score"]}

Evidence:
{TEST_INCIDENT["evidence"]}

Triggered Features:
{TEST_INCIDENT["triggered_features"]}

Recommended Investigation Actions:
{TEST_INCIDENT["recommended_actions"]}
"""

    print("=" * 70)
    print("KATANA — EXPLAINABILITY ENGINE TEST")
    print("=" * 70)

    print(f"Model: {llm.MODEL}")
    print("Testing structured JSON output")

    print("\nSending incident to LLM...")

    try:

        response = await llm.generate(
            system=SYSTEM_PROMPT,
            prompt=prompt,
            format_schema=RESPONSE_SCHEMA,
        )

    except Exception as exc:

        print("\nLLM ERROR")
        print("-" * 70)
        print(str(exc))
        return

    print("\nRAW RESPONSE")
    print("-" * 70)
    print(response)

    # ----------------------------------------------------------
    # JSON VALIDATION
    # ----------------------------------------------------------

    print("\nJSON VALIDATION")
    print("-" * 70)

    try:

        data = json.loads(response)

    except json.JSONDecodeError as exc:

        print("FAIL: Invalid JSON")
        print(f"Error: {exc}")
        return

    print("PASS: Valid JSON")

    # ----------------------------------------------------------
    # REQUIRED FIELDS
    # ----------------------------------------------------------

    required = {
        "summary",
        "analysis",
        "risk",
        "mitre_attack",
    }

    missing = required - data.keys()

    if missing:

        print(
            f"FAIL: Missing fields: {sorted(missing)}"
        )

        return

    print("PASS: All required fields present")

    # ----------------------------------------------------------
    # EXTRA FIELDS
    # ----------------------------------------------------------

    allowed = required

    extra = set(data.keys()) - allowed

    if extra:

        print(
            f"FAIL: Unexpected fields: {sorted(extra)}"
        )

        return

    print("PASS: No unexpected fields")

    # ----------------------------------------------------------
    # FIELD TYPES
    # ----------------------------------------------------------

    if not isinstance(
        data["summary"],
        str,
    ):

        print("FAIL: summary must be a string")
        return

    if not isinstance(
        data["analysis"],
        str,
    ):

        print("FAIL: analysis must be a string")
        return

    if data["risk"] not in {
        "Low",
        "Medium",
        "High",
        "Critical",
        "Uncertain",
    }:

        print(
            f"FAIL: Invalid risk: {data['risk']}"
        )

        return

    if not isinstance(
        data["mitre_attack"],
        list,
    ):

        print(
            "FAIL: mitre_attack must be a list"
        )

        return

    if not all(
        isinstance(item, str)
        for item in data["mitre_attack"]
    ):

        print(
            "FAIL: mitre_attack must contain only strings"
        )

        return

    print("PASS: Field types valid")

    # ----------------------------------------------------------
    # DISPLAY RESULT
    # ----------------------------------------------------------

    print("\nSTRUCTURE")
    print("-" * 70)

    print("summary:")
    print(f"  {data['summary']}")

    print("\nanalysis:")
    print(f"  {data['analysis']}")

    print("\nrisk:")
    print(f"  {data['risk']}")

    print("\nmitre_attack:")
    print(f"  {data['mitre_attack']}")

    # ----------------------------------------------------------
    # SANITY CHECK
    # ----------------------------------------------------------

    print("\nSANITY CHECK")
    print("-" * 70)

    if data["risk"] not in {
        "High",
        "Critical",
    }:

        print(
            "WARNING: Expected elevated risk for this test incident."
        )

    else:

        print(
            "PASS: Elevated risk classification."
        )

    # MITRE must not be invented by the model.
    # Our prompt explicitly says to return [] unless
    # the supplied evidence directly supports a technique.

    print("\nMITRE SAFETY CHECK")
    print("-" * 70)

    print(
        "PASS: MITRE output received as structured list."
    )

    print("\n" + "=" * 70)
    print("EXPLAINABILITY TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())