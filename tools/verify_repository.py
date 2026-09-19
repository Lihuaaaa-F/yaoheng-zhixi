"""Read-only repository contracts; not an application or human acceptance test."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "药衡智析_增量源码交接/public_source_candidate"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def scenario_ids(record: dict) -> dict[str, str]:
    rows = record["scenarios"]
    result = {row["id"]: row["job_id"] for row in rows}
    if len(result) != len(rows):
        raise ValueError("duplicate scenario id")
    return result


def verify() -> list[str]:
    errors: list[str] = []
    docs = APP / "docs"
    current = read_json(docs / "current_run.json")
    manifest = read_json(docs / current["public_manifest"])
    verification = read_json(docs / current["verification_receipt"])
    for label, other in [("manifest", manifest), ("verification", verification)]:
        for key in ("run_id", "commit"):
            if current[key] != other[key]:
                errors.append(f"{label}: {key} differs from current index")
        if scenario_ids(current) != scenario_ids(other):
            errors.append(f"{label}: scenario/job mapping differs from current index")
    if set(current["required_scenarios"]) != set(scenario_ids(current)):
        errors.append("required scenario coverage differs from index")
    if current.get("competition_ready") and current.get("human_review") != "PASS":
        errors.append("competition_ready requires recorded human acceptance")

    facts = read_json(ROOT / "docs/repository/media_facts.json")
    for entry in facts["files"]:
        path = APP / facts["directory"] / entry["name"]
        if not path.is_file():
            errors.append(f"missing media: {entry['name']}")
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            errors.append(f"media checksum differs: {entry['name']}")

    # Current entry points only: historical audit prose is not a navigation contract.
    documents = [ROOT / "README.md", ROOT / "CONTRIBUTING.md"]
    documents += sorted((ROOT / "docs/repository").glob("*.md"))
    documents += [APP / "README.md", docs / "evaluation_report.md",
                  APP / "07_交付/demo_20260918/README.md"]
    for document in documents:
        content = document.read_text(encoding="utf-8")
        content = re.sub(r"```.*?```", "", content, flags=re.S)
        for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", content):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path = (document.parent / unquote(parsed.path)).resolve()
            if not path.is_relative_to(ROOT) or not path.exists():
                errors.append(f"{document.relative_to(ROOT)}: broken local link {target}")
    return errors


if __name__ == "__main__":
    try:
        failures = verify()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        failures = [f"repository contract cannot be read: {exc}"]
    print(json.dumps({"check": "repository_contracts", "status": "FAIL" if failures else "PASS",
                      "scope": "navigation, scenario index, media identity; no app/model/human validation",
                      "errors": failures}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if failures else 0)
