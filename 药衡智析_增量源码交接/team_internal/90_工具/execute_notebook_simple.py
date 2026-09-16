from __future__ import annotations

import argparse
import ast
import contextlib
import io
import json
import traceback
from pathlib import Path
from typing import Any


def source_text(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def execute_cell(code: str, namespace: dict[str, Any]) -> tuple[str, Any | None]:
    tree = ast.parse(code, mode="exec")
    final_expression = None
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        final_expression = ast.Expression(tree.body.pop().value)
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        if tree.body:
            exec(compile(tree, "<notebook-cell>", "exec"), namespace)
        result = eval(compile(final_expression, "<notebook-cell>", "eval"), namespace) if final_expression else None
    return stream.getvalue(), result


def display_data(value: Any) -> dict[str, Any]:
    text = repr(value)
    html = None
    if hasattr(value, "_repr_html_"):
        try:
            html = value._repr_html_()
        except Exception:
            html = None
    data: dict[str, Any] = {"text/plain": text}
    if html:
        data["text/html"] = html
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute a simple nbformat-4 Python notebook top-to-bottom")
    parser.add_argument("notebook", type=Path)
    args = parser.parse_args()
    path = args.notebook.resolve()
    notebook = json.loads(path.read_text(encoding="utf-8"))
    if notebook.get("nbformat") != 4 or not isinstance(notebook.get("cells"), list):
        raise ValueError("Notebook is not a supported nbformat-4 document")

    namespace: dict[str, Any] = {"__name__": "__main__"}
    execution_count = 0
    for cell in notebook["cells"]:
        if cell.get("cell_type") != "code":
            continue
        execution_count += 1
        cell["execution_count"] = execution_count
        cell["outputs"] = []
        try:
            stream, value = execute_cell(source_text(cell), namespace)
            if stream:
                cell["outputs"].append({"name": "stdout", "output_type": "stream", "text": stream})
            if value is not None:
                cell["outputs"].append({
                    "data": display_data(value),
                    "execution_count": execution_count,
                    "metadata": {},
                    "output_type": "execute_result",
                })
        except Exception as error:
            cell["outputs"].append({
                "ename": type(error).__name__,
                "evalue": str(error),
                "output_type": "error",
                "traceback": traceback.format_exc().splitlines(),
            })
            path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
            raise
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Executed {execution_count} code cells: {path}")


if __name__ == "__main__":
    main()
