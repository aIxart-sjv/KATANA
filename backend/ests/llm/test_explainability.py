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

    print(f"\nMODEL: {llm.MODEL}")

    print("\nSending incident to LLM...")

    response = await llm.generate(
        system=SYSTEM_PROMPT,
        prompt=prompt,
    )

    print("\nRAW RESPONSE")
    print("-" * 70)
    print(response)

    print("\nJSON VALIDATION")
    print("-" * 70)

    try:
        data = json.loads(response)

    except json.JSONDecodeError as exc:

        print("FAIL: Invalid JSON")
        print(f"Error: {exc}")
        return

    print("PASS: Valid JSON")

    required = {
        "summary",
        "analysis",
        "risk",
        "mitre_attack",
    }

    missing = required - data.keys()

    if missing:

        print(f"FAIL: Missing fields: {sorted(missing)}")
        return

    print("PASS: All required fields present")

    if not isinstance(data["summary"], str):
        print("FAIL: summary must be a string")
        return

    if not isinstance(data["analysis"], str):
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
            f"FAIL: Invalid risk value: {data['risk']}"
        )
        return

    if not isinstance(data["mitre_attack"], list):
        print("FAIL: mitre_attack must be a list")
        return

    print("PASS: Field types valid")

    print("\nSTRUCTURE")
    print("-" * 70)

    print(f"summary:")
    print(f"  {data['summary']}")

    print(f"\nanalysis:")
    print(f"  {data['analysis']}")

    print(f"\nrisk:")
    print(f"  {data['risk']}")

    print(f"\nmitre_attack:")
    for technique in data["mitre_attack"]:
        print(f"  - {technique}")

    print("\n" + "=" * 70)
    print("EXPLAINABILITY TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())