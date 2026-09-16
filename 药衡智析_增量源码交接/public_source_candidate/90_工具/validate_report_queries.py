from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def execute(sql: str) -> list[dict[str, object]]:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute(sql).fetchall()]
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
    datasets = artifact["snapshot"]["datasets"]
    checked: dict[str, int] = {}
    for section in ("charts", "tables"):
        for asset in artifact["manifest"].get(section, []):
            sql = asset.get("source", {}).get("query", {}).get("sql")
            if not sql:
                raise AssertionError(f"{section}/{asset['id']} has no executable SQL source")
            dataset = asset["dataset"]
            rows = execute(sql)
            if rows != datasets[dataset]:
                raise AssertionError(f"{section}/{asset['id']} SQL output differs from dataset {dataset}")
            checked[asset["id"]] = len(rows)
    print(json.dumps(checked, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

