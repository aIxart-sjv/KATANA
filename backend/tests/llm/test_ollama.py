import asyncio
import json
import time

from app.llm.ollama import OllamaClient
from app.explainability.prompts import SYSTEM_PROMPT


INCIDENTS = [
    {
        "name": "BENIGN",
        "incident": """
Severity: Low
Anomaly Score: -0.31

Evidence:
- Process creation rate: 2
- External connections: 1
- Privilege escalations: 0
- Maximum CPU: 34.2%

Triggered Features:
{
    "process_creation_rate": 2,
    "external_connections": 1,
    "privilege_escalations": 0,
    "maximum_cpu": 34.2
}

Recommended Investigation Actions:
- Continue monitoring system behavior.
""",
    },
    {
        "name": "SUSPICIOUS",
        "incident": """
Severity: High
Anomaly Score: -0.61

Evidence:
- High process creation rate (27)
- 8 outbound network connections detected.
- 1 privilege escalation event(s).

Triggered Features:
{
    "process_creation_rate": 27,
    "external_connections": 8,
    "privilege_escalations": 1,
    "maximum_cpu": 72.4
}

Recommended Investigation Actions:
- Inspect recently spawned processes.
- Review active outbound connections.
- Review privileged operations immediately.
""",
    },
    {
        "name": "CRITICAL",
        "incident": """
Severity: Critical
Anomaly Score: -0.82

Evidence:
- High process creation rate (47)
- 21 outbound network connections detected.
- 3 privilege escalation event(s).
- Maximum CPU usage reached 97.3%.

Triggered Features:
{
    "process_creation_rate": 47,
    "external_connections": 21,
    "privilege_escalations": 3,
    "maximum_cpu": 97.3
}

Recommended Investigation Actions:
- Inspect recently spawned processes.
- Review active outbound connections.
- Review privileged operations immediately.
""",
    },
    {
        "name": "INSUFFICIENT_EVIDENCE",
        "incident": """
Severity: High
Anomaly Score: -0.59

Evidence:
[]

Triggered Features:
{
    "process_creation_rate": 3,
    "external_connections": 0,
    "privilege_escalations": 0,
    "maximum_cpu": 22.1
}

Recommended Investigation Actions:
[]
""",
    },
]


REQUIRED_FIELDS = {
    "summary",
    "analysis",
    "risk",
    "mitre_attack",
}


def validate_response(data):

    print("\nJSON VALIDATION")
    print("-" * 70)

    missing = REQUIRED_FIELDS - data.keys()

    if missing:
        print(f"FAIL: Missing fields: {sorted(missing)}")
        return False

    if not isinstance(data["summary"], str):
        print("FAIL: summary must be a string")
        return False

    if not isinstance(data["analysis"], str):
        print("FAIL: analysis must be a string")
        return False

    if not isinstance(data["risk"], str):
        print("FAIL: risk must be a string")
        return False

    if not isinstance(data["mitre_attack"], list):
        print("FAIL: mitre_attack must be a list")
        return False

    print("PASS: All required fields present")
    print("PASS: Field types valid")

    return True


async def main():

    llm = OllamaClient()

    print("=" * 70)
    print("KATANA — STANDALONE LLM EVALUATION")
    print("=" * 70)
    print(f"Model: {llm.MODEL}")
    print("Expected output: 4-field compact JSON")
    print("Max output tokens: 180")
    print("=" * 70)

    total_time = 0
    passed = 0

    for test in INCIDENTS:

        print("\n")
        print("=" * 70)
        print(f"TEST: {test['name']}")
        print("=" * 70)

        start = time.perf_counter()

        try:
            response = await llm.generate(
                system=SYSTEM_PROMPT,
                prompt=test["incident"],
            )

        except Exception as exc:

            elapsed = time.perf_counter() - start

            print(f"\nLLM ERROR: {exc}")
            print(f"Response time: {elapsed:.2f}s")

            continue

        elapsed = time.perf_counter() - start
        total_time += elapsed

        print(f"\nResponse time: {elapsed:.2f}s")
        print(f"Response length: {len(response)} characters")

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

            continue

        print("PASS: Valid JSON")

        if not validate_response(data):
            continue

        print("\nSTRUCTURE")
        print("-" * 70)

        print(f"summary:")
        print(f"  {data['summary']}")

        print(f"\nanalysis:")
        print(f"  {data['analysis']}")

        print(f"\nrisk:")
        print(f"  {data['risk']}")

        print(f"\nmitre_attack:")
        print(f"  {data['mitre_attack']}")

        # ----------------------------------------------------------
        # Basic sanity checks
        # ----------------------------------------------------------

        print("\nSANITY CHECKS")
        print("-" * 70)

        if test["name"] == "INSUFFICIENT_EVIDENCE":

            if len(data["mitre_attack"]) == 0:
                print("PASS: No unsupported MITRE technique")
            else:
                print(
                    "WARNING: MITRE techniques returned despite "
                    "insufficient evidence"
                )

        if test["name"] == "BENIGN":

            if data["risk"].lower() in {
                "low",
                "uncertain",
            }:
                print("PASS: Benign risk classification reasonable")
            else:
                print(
                    f"WARNING: Unexpected benign risk: "
                    f"{data['risk']}"
                )

        if test["name"] in {"SUSPICIOUS", "CRITICAL"}:

            if data["risk"].lower() in {
                "high",
                "critical",
            }:
                print("PASS: Elevated risk classification")
            else:
                print(
                    f"WARNING: Unexpected risk: "
                    f"{data['risk']}"
                )

        passed += 1

    print("\n")
    print("=" * 70)
    print("LLM EVALUATION SUMMARY")
    print("=" * 70)

    print(f"Tests passed : {passed}/{len(INCIDENTS)}")

    if passed:
        print(
            f"Average response time: "
            f"{total_time / passed:.2f}s"
        )

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
