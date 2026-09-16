from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from pypdf import PdfReader


DIRECTORIES = [
    "01_数据/00_原始",
    "01_数据/01_清洗",
    "01_数据/02_分析输出",
    "02_知识库/00_原始",
    "02_知识库/01_解析",
    "02_知识库/02_清洗",
    "02_知识库/03_索引",
    "03_研究/外部资料",
    "03_研究/开源项目",
    "04_方案与文档",
    "05_原型",
    "06_评测",
    "07_交付",
    "90_工具",
    "99_隔离区",
]


@dataclass(frozen=True)
class Finding:
    check: str
    status: str
    severity: str
    metric: float | int | str
    tolerance: str
    implication: str


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = unicodedata.normalize("NFKC", value)
    text = text.replace("\u00a0", " ").replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def safe_copytree(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def prepare_directories(project: Path) -> None:
    for relative in DIRECTORIES:
        (project / relative).mkdir(parents=True, exist_ok=True)


def clean_csv(source: Path, destination: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = source.read_bytes()
    raw.decode("utf-8", errors="strict")
    frame = pd.read_csv(source, encoding="utf-8-sig")
    original_rows, original_columns = frame.shape
    frame.columns = [normalize_text(column) for column in frame.columns]
    frame = frame.dropna(axis=0, how="all").dropna(axis=1, how="all")
    for column in frame.columns:
        if pd.api.types.is_string_dtype(frame[column].dtype):
            frame[column] = frame[column].map(normalize_text)
            frame[column] = frame[column].replace({"": pd.NA, "N/A": pd.NA, "n/a": pd.NA})
    destination.parent.mkdir(parents=True, exist_ok=True)
    # UTF-8 with BOM prevents mojibake in common Chinese Windows spreadsheet tools.
    frame.to_csv(destination, index=False, encoding="utf-8-sig", lineterminator="\n")
    profile = {
        "file": source.name,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "clean_sha256": sha256(destination),
        "rows_before": original_rows,
        "rows_after": len(frame),
        "columns_before": original_columns,
        "columns_after": len(frame.columns),
        "exact_duplicate_rows": int(frame.duplicated().sum()),
        "null_cells": int(frame.isna().sum().sum()),
        "encoding": "UTF-8 strict -> UTF-8-SIG",
    }
    return frame, profile


def candidate_key_for(name: str) -> list[str]:
    if "原材料消耗明细" in name:
        return ["工厂", "产品名称", "月份", "原材料名称"]
    if "制造费用明细" in name:
        return ["工厂", "产品名称", "月份", "费用类别"]
    if "人工工时明细" in name or "成本汇总" in name or "预算数据" in name:
        return ["工厂", "产品名称", "月份"]
    if "药材市场价格" in name:
        return ["药材名称", "规格等级"]
    if "行业成本基准" in name:
        return ["产品类别", "指标"]
    return []


def stage_and_clean_data(project: Path, package: Path) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    raw_root = project / "01_数据/00_原始"
    clean_root = project / "01_数据/01_清洗"
    sources = [package / "01_成本明细数据", package / "02_行业参考数据"]
    tables: dict[str, pd.DataFrame] = {}
    profiles: list[dict[str, Any]] = []
    for source_dir in sources:
        category = source_dir.name
        for source in sorted(source_dir.glob("*.csv")):
            raw_target = raw_root / category / source.name
            raw_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, raw_target)
            clean_target = clean_root / category / source.name
            frame, profile = clean_csv(raw_target, clean_target)
            key = candidate_key_for(source.name)
            profile["candidate_key"] = " + ".join(key) if key else "未定义"
            profile["duplicate_candidate_keys"] = (
                int(frame.duplicated(key).sum()) if key and set(key).issubset(frame.columns) else None
            )
            profiles.append(profile)
            tables[source.name] = frame
    profile_frame = pd.DataFrame(profiles)
    profile_frame.to_csv(project / "06_评测/数据文件质量概览.csv", index=False, encoding="utf-8-sig")
    return tables, profile_frame


def max_abs(series: pd.Series) -> float:
    return float(series.abs().max()) if not series.empty else 0.0


def check_close(name: str, error: pd.Series, tolerance: float, implication: str) -> Finding:
    observed = max_abs(error)
    passed = observed <= tolerance
    return Finding(
        check=name,
        status="PASS" if passed else "FAIL",
        severity="none" if passed else "high",
        metric=round(observed, 6),
        tolerance=f"≤ {tolerance}",
        implication=implication,
    )


def validate_cost_data(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    findings: list[Finding] = []
    summary_names = [name for name in tables if "成本汇总" in name]
    for name in summary_names:
        frame = tables[name]
        component_error = (
            frame["直接材料(元/盒)"] + frame["直接人工(元/盒)"] + frame["制造费用(元/盒)"]
            - frame["单位成本(元/盒)"]
        )
        findings.append(check_close(f"{name}: 三要素合计=单位成本", component_error, 0.011, "成本结构、瀑布图和贡献度的数值底座"))
        total_error = frame["单位成本(元/盒)"] * frame["产量(盒)"] - frame["总成本(元)"]
        findings.append(check_close(f"{name}: 单位成本×产量=总成本", total_error, 1.0, "总成本汇总与报告金额"))

    budget = tables["中药一厂_预算数据_2026年.csv"]
    budget_component_error = (
        budget["预算直接材料(元/盒)"] + budget["预算直接人工(元/盒)"] + budget["预算制造费用(元/盒)"]
        - budget["预算单位成本(元/盒)"]
    )
    findings.append(check_close("预算三要素合计=预算单位成本", budget_component_error, 0.011, "预算差异分析"))
    findings.append(
        check_close(
            "预算单位成本×预算产量=预算总成本",
            budget["预算单位成本(元/盒)"] * budget["预算产量(盒)"] - budget["预算总成本(元)"],
            1.0,
            "预算总额分析",
        )
    )

    current = tables["中药一厂_成本汇总_2026年1-6月.csv"]
    join_key = ["工厂", "产品名称", "产品规格", "月份", "产量(盒)"]
    material = (
        tables["中药一厂_原材料消耗明细_2026年1-6月.csv"]
        .groupby(join_key, as_index=False)["单位消耗成本(元/盒)"]
        .sum()
    )
    material_check = current.merge(material, on=join_key, how="left", validate="one_to_one")
    findings.append(
        check_close(
            "原材料明细合计=汇总直接材料",
            material_check["单位消耗成本(元/盒)"] - material_check["直接材料(元/盒)"],
            0.011,
            "原料下钻归因",
        )
    )

    overhead = (
        tables["中药一厂_制造费用明细_2026年1-6月.csv"]
        .groupby(join_key, as_index=False)["单位费用(元/盒)"]
        .sum()
    )
    overhead_check = current.merge(overhead, on=join_key, how="left", validate="one_to_one")
    findings.append(
        check_close(
            "制造费用明细合计=汇总制造费用",
            overhead_check["单位费用(元/盒)"] - overhead_check["制造费用(元/盒)"],
            0.011,
            "制造费用下钻归因",
        )
    )

    labor = tables["中药一厂_人工工时明细_2026年1-6月.csv"].copy()
    labor["人工单价复算"] = labor["直接人工总额(元)"] / labor["产量(盒)"]
    labor_check = current.merge(labor[join_key + ["人工单价复算"]], on=join_key, how="left", validate="one_to_one")
    findings.append(
        check_close(
            "人工总额÷产量=汇总直接人工",
            labor_check["人工单价复算"] - labor_check["直接人工(元/盒)"],
            0.011,
            "人工效率归因",
        )
    )

    material_rows = tables["中药一厂_原材料消耗明细_2026年1-6月.csv"].copy()
    share_sum = (
        material_rows.assign(share=material_rows["占总材料成本比例"].str.rstrip("%").astype(float))
        .groupby(["工厂", "产品名称", "月份"])["share"]
        .sum()
    )
    findings.append(check_close("原材料占比按产品月份合计≈100%", share_sum - 100.0, 0.2, "材料结构图"))

    for name, frame in tables.items():
        key = candidate_key_for(name)
        if key and set(key).issubset(frame.columns):
            duplicates = int(frame.duplicated(key).sum())
            findings.append(
                Finding(
                    check=f"{name}: 候选主键唯一",
                    status="PASS" if duplicates == 0 else "FAIL",
                    severity="none" if duplicates == 0 else "critical",
                    metric=duplicates,
                    tolerance="= 0",
                    implication="防止重复计数和连接膨胀",
                )
            )
    result = pd.DataFrame([finding.__dict__ for finding in findings])
    return result


def build_analysis_outputs(project: Path, tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    output = project / "01_数据/02_分析输出"
    output.mkdir(parents=True, exist_ok=True)
    current = tables["中药一厂_成本汇总_2026年1-6月.csv"].copy()
    prior = tables["中药一厂_成本汇总_2025年1-6月.csv"].copy()
    peer = tables["中药二厂_成本汇总_2026年1-6月.csv"].copy()
    budget = tables["中药一厂_预算数据_2026年.csv"].copy()
    for frame in (current, prior, peer, budget):
        frame["月序"] = frame["月份"].str[-2:].astype(int)

    current = current.sort_values(["产品名称", "月序"]).reset_index(drop=True)
    current["上月单位成本"] = current.groupby("产品名称")["单位成本(元/盒)"].shift(1)
    current["环比变动额"] = current["单位成本(元/盒)"] - current["上月单位成本"]
    current["环比变动率"] = current["环比变动额"] / current["上月单位成本"]

    prior_fields = ["产品名称", "月序", "单位成本(元/盒)", "直接材料(元/盒)", "直接人工(元/盒)", "制造费用(元/盒)"]
    prior_merge = prior[prior_fields].rename(columns={column: f"去年_{column}" for column in prior_fields[2:]})
    current = current.merge(prior_merge, on=["产品名称", "月序"], how="left", validate="one_to_one")
    current["同比变动额"] = current["单位成本(元/盒)"] - current["去年_单位成本(元/盒)"]
    current["同比变动率"] = current["同比变动额"] / current["去年_单位成本(元/盒)"]

    budget_fields = ["产品名称", "月序", "预算单位成本(元/盒)", "预算直接材料(元/盒)", "预算直接人工(元/盒)", "预算制造费用(元/盒)"]
    current = current.merge(budget[budget_fields], on=["产品名称", "月序"], how="left", validate="one_to_one")
    current["预算偏差额"] = current["单位成本(元/盒)"] - current["预算单位成本(元/盒)"]
    current["预算偏差率"] = current["预算偏差额"] / current["预算单位成本(元/盒)"]

    peer_fields = ["产品名称", "月序", "单位成本(元/盒)", "直接材料(元/盒)", "直接人工(元/盒)", "制造费用(元/盒)"]
    peer_merge = peer[peer_fields].rename(columns={column: f"二厂_{column}" for column in peer_fields[2:]})
    current = current.merge(peer_merge, on=["产品名称", "月序"], how="left", validate="one_to_one")
    current["对标差异额"] = current["单位成本(元/盒)"] - current["二厂_单位成本(元/盒)"]
    current["对标差异率"] = current["对标差异额"] / current["二厂_单位成本(元/盒)"]

    elements = ["直接材料(元/盒)", "直接人工(元/盒)", "制造费用(元/盒)"]
    for element in elements:
        label = element.split("(")[0]
        current[f"{label}_环比变动额"] = current.groupby("产品名称")[element].diff()
        denominator = current["环比变动额"].where(current["环比变动额"].abs() >= 0.005)
        current[f"{label}_环比贡献率"] = current[f"{label}_环比变动额"] / denominator

    current.to_csv(output / "产品月度成本指标.csv", index=False, encoding="utf-8-sig")

    alerts: list[dict[str, Any]] = []
    for _, row in current.iterrows():
        if pd.isna(row["上月单位成本"]):
            continue
        for element in elements:
            previous = row[element] - row[f"{element.split('(')[0]}_环比变动额"]
            rate = row[f"{element.split('(')[0]}_环比变动额"] / previous if previous else np.nan
            if pd.notna(rate) and abs(rate) >= 0.10:
                alerts.append({
                    "产品名称": row["产品名称"],
                    "月份": row["月份"],
                    "成本要素": element.split("(")[0],
                    "环比变动率": rate,
                    "环比变动额(元/盒)": row[f"{element.split('(')[0]}_环比变动额"],
                    "阈值": 0.10,
                })
    alerts_frame = pd.DataFrame(alerts)
    alerts_frame.to_csv(output / "成本波动阈值告警.csv", index=False, encoding="utf-8-sig")

    scenario_rows = current[current["月份"].isin(["2026-03", "2026-05"])].copy()
    scenario_rows = scenario_rows[
        ((scenario_rows["产品名称"] == "六味地黄胶囊") & (scenario_rows["月份"] == "2026-03"))
        | ((scenario_rows["产品名称"].isin(["银黄口服液", "板蓝根颗粒"])) & (scenario_rows["月份"] == "2026-05"))
    ]
    scenario_rows.to_csv(output / "推荐三场景指标.csv", index=False, encoding="utf-8-sig")

    return {"monthly": current, "alerts": alerts_frame, "scenarios": scenario_rows}


def classify_document(filename: str) -> tuple[str, str | None, str | None, str]:
    if "产品配方" in filename:
        product = filename.replace("产品配方文档_", "").replace(".pdf", "")
        return "产品配方", product, None, "赛事模拟企业资料"
    if "生产工艺" in filename:
        return "生产工艺", None, "中药一厂", "赛事模拟企业资料"
    if "设备清单" in filename:
        return "设备台账", None, "中药一厂", "赛事模拟企业资料"
    if "GMP" in filename or "质量管理规范" in filename:
        return "法规制度", None, None, "赛题提供法规副本，需与官方现行文本核验"
    return "其他", None, None, "赛事资料"


def split_page(text: str, target_size: int = 850, overlap: int = 100) -> Iterable[str]:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= target_size:
            current = f"{current}\n\n{paragraph}".strip()
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= target_size:
            current = paragraph
            continue
        start = 0
        while start < len(paragraph):
            end = min(start + target_size, len(paragraph))
            chunks.append(paragraph[start:end])
            if end == len(paragraph):
                break
            start = max(end - overlap, start + 1)
        current = ""
    if current:
        chunks.append(current)
    return chunks


def clean_repeated_page_lines(page_texts: list[str]) -> tuple[list[str], list[str], int]:
    """Remove page numbers and short lines repeated on most pages of one document."""
    normalized_pages: list[list[str]] = []
    frequency: Counter[str] = Counter()
    for text in page_texts:
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        normalized_pages.append(lines)
        candidates = {line for line in lines if 1 < len(line) <= 80}
        frequency.update(candidates)

    threshold = max(2, math.ceil(len(page_texts) * 0.60))
    repeated_lines = sorted(line for line, count in frequency.items() if count >= threshold)
    repeated_set = set(repeated_lines)
    page_number_pattern = re.compile(
        r"^(?:第\s*)?[-—–]?\s*\d+\s*[-—–]?(?:\s*页)?(?:\s*/\s*\d+\s*页?)?$",
        re.IGNORECASE,
    )
    cleaned_pages: list[str] = []
    removed_count = 0
    for lines in normalized_pages:
        kept: list[str] = []
        for line in lines:
            if line and (line in repeated_set or page_number_pattern.fullmatch(line)):
                removed_count += 1
                continue
            kept.append(line)
        cleaned = "\n".join(kept)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        cleaned_pages.append(cleaned)
    return cleaned_pages, repeated_lines, removed_count


def build_knowledge_corpus(project: Path, package: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    source_dir = package / "03_制药知识文档"
    raw_dir = project / "02_知识库/00_原始"
    parsed_dir = project / "02_知识库/01_解析"
    cleaned_dir = project / "02_知识库/02_清洗"
    index_dir = project / "02_知识库/03_索引"
    for directory in (raw_dir, parsed_dir, cleaned_dir, index_dir):
        directory.mkdir(parents=True, exist_ok=True)
    safe_copytree(source_dir, raw_dir)

    manifest: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    duplicate_chunks_removed = 0
    for pdf in sorted(raw_dir.glob("*.pdf")):
        reader = PdfReader(str(pdf))
        document_type, product, factory, authority = classify_document(pdf.name)
        raw_page_texts: list[str] = []
        low_text_pages: list[int] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = unicodedata.normalize("NFKC", text).replace("\u00a0", " ")
            text = re.sub(r"[ \t]+", " ", text)
            raw_page_texts.append(text.strip())
            if len(text.strip()) < 80:
                low_text_pages.append(page_number)

        cleaned_page_texts, repeated_lines, removed_line_count = clean_repeated_page_lines(raw_page_texts)
        document_chunks = 0
        for page_number, text in enumerate(cleaned_page_texts, start=1):
            for index, content in enumerate(split_page(text), start=1):
                content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                if content_hash in seen_hashes:
                    duplicate_chunks_removed += 1
                    continue
                seen_hashes.add(content_hash)
                chunks.append({
                    "chunk_id": f"{pdf.stem}-p{page_number:03d}-c{index:02d}",
                    "document_id": pdf.stem,
                    "source_file": pdf.name,
                    "source_sha256": sha256(pdf),
                    "document_type": document_type,
                    "product": product,
                    "factory": factory,
                    "authority": authority,
                    "page": page_number,
                    "content": content,
                    "content_sha256": content_hash,
                })
                document_chunks += 1
        parsed_path = parsed_dir / f"{pdf.stem}.md"
        parsed_pages = [f"## 第 {page_number} 页\n\n{text}" for page_number, text in enumerate(raw_page_texts, start=1)]
        parsed_path.write_text(f"# {pdf.stem}\n\n" + "\n\n".join(parsed_pages), encoding="utf-8")
        cleaned_path = cleaned_dir / f"{pdf.stem}.md"
        cleaned_pages = [f"## 第 {page_number} 页\n\n{text}" for page_number, text in enumerate(cleaned_page_texts, start=1)]
        cleaned_path.write_text(f"# {pdf.stem}\n\n" + "\n\n".join(cleaned_pages), encoding="utf-8")
        manifest.append({
            "document_id": pdf.stem,
            "source_file": pdf.name,
            "source_sha256": sha256(pdf),
            "pages": len(reader.pages),
            "raw_characters": sum(len(text) for text in raw_page_texts),
            "characters": sum(len(text) for text in cleaned_page_texts),
            "repeated_lines_removed": removed_line_count,
            "repeated_line_examples": " | ".join(repeated_lines[:5]),
            "low_text_pages": ",".join(map(str, low_text_pages)),
            "ocr_required": bool(low_text_pages),
            "document_type": document_type,
            "product": product,
            "factory": factory,
            "authority": authority,
            "chunks": document_chunks,
        })

    manifest_frame = pd.DataFrame(manifest)
    manifest_frame.to_csv(index_dir / "document_manifest.csv", index=False, encoding="utf-8-sig")
    with (index_dir / "chunks.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    summary = {
        "documents": len(manifest_frame),
        "pages": int(manifest_frame["pages"].sum()),
        "characters": int(manifest_frame["characters"].sum()),
        "chunks": len(chunks),
        "ocr_queue_documents": int(manifest_frame["ocr_required"].sum()),
        "duplicate_chunks_removed": duplicate_chunks_removed,
        "generated_at": datetime.now().astimezone().isoformat(),
    }
    (index_dir / "corpus_build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_frame, summary


def build_notebook(project: Path, package: Path, quality: pd.DataFrame, analysis: dict[str, pd.DataFrame], corpus: dict[str, Any]) -> Path:
    notebook_path = project / "03_研究/制药成本模拟数据深度分析.ipynb"
    def markdown_cell(source: str) -> dict[str, Any]:
        return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}

    def code_cell(source: str) -> dict[str, Any]:
        return {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": source.splitlines(keepends=True),
        }

    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        },
        "cells": [
        markdown_cell(
            "## tl;dr\n\n"
            f"- 已检查 10 张 CSV；质量规则 **{int((quality['status'] == 'PASS').sum())}/{len(quality)} 通过**。\n"
            f"- 知识库初始语料含 **{corpus['documents']} 份文档、{corpus['pages']} 页、{corpus['chunks']} 个可追溯切片**。\n"
            "- 推荐演示场景：银黄口服液 2026-05、板蓝根颗粒 2026-05、六味地黄胶囊 2026-03。\n"
            "- 原料表缺少独立采购价和实物消耗量，价格/数量效应不可被精确拆分；系统必须把市场行情仅作为佐证而非确定性因果。"
        ),
        markdown_cell(
            "## Context & Methods\n\n"
            "目标是验证模拟数据能否支撑环比、同比、预算差异、工厂对标、三要素贡献度、原料/费用下钻和知识库检索。\n\n"
            "### Key Assumptions\n\n"
            "- 金额单位以文件列名为准，月份按自然月，北京时间。\n"
            "- 单位成本贡献率只在总单位成本变化绝对值不小于 0.005 元/盒时解释。\n"
            "- 赛题模拟数据是比赛计算的控制来源；外部资料只做法规、方法和行业知识增强。"
        ),
        markdown_cell("## Data\n\n输入来自赛题 V1.1 净化解压副本；清洗版统一写为 UTF-8-SIG，便于 Windows Excel 正确显示中文。"),
        code_cell(
            "from pathlib import Path\n"
            "import pandas as pd\n\n"
            f"project = Path(r'''{project}''')\n"
            "profile = pd.read_csv(project / '06_评测/数据文件质量概览.csv', encoding='utf-8-sig')\n"
            "quality = pd.read_csv(project / '06_评测/数据一致性检查.csv', encoding='utf-8-sig')\n"
            "monthly = pd.read_csv(project / '01_数据/02_分析输出/产品月度成本指标.csv', encoding='utf-8-sig')\n"
            "profile[['file', 'rows_after', 'columns_after', 'exact_duplicate_rows', 'null_cells']]"
        ),
        markdown_cell("## Results\n\n### 1. 数据一致性"),
        code_cell("quality"),
        markdown_cell("### 2. 三个高信息量演示场景"),
        code_cell(
            "scenarios = pd.read_csv(project / '01_数据/02_分析输出/推荐三场景指标.csv', encoding='utf-8-sig')\n"
            "scenarios[['产品名称','月份','单位成本(元/盒)','环比变动率','同比变动率','预算偏差率','对标差异率']]"
        ),
        markdown_cell("### 3. 知识语料构建状态"),
        code_cell(
            "manifest = pd.read_csv(project / '02_知识库/03_索引/document_manifest.csv', encoding='utf-8-sig')\n"
            "manifest[['source_file','pages','characters','chunks','ocr_required','document_type']]"
        ),
        markdown_cell(
            "## Takeaways\n\n"
            "1. 汇总表与材料、人工、制造费用明细可形成可复验的确定性计算链。\n"
            "2. 应以三场景黄金集覆盖价格行情、工艺/设备事件和工厂对标。\n"
            "3. 大模型不得承担加减乘除、连接或阈值判断；它只接收已验证 JSON 和带页码证据。\n"
            "4. 后续应为每个场景人工标注关键事实、允许引用和禁止断言，形成检索与生成双层评测集。"
        ),
    ]}
    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    notebook_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    return notebook_path


def write_audit(project: Path, package: Path, profile: pd.DataFrame, quality: pd.DataFrame, corpus: dict[str, Any]) -> None:
    audit = {
        "source_package": str(package),
        "generated_at": datetime.now().astimezone().isoformat(),
        "data_files": int(len(profile)),
        "data_rows": int(profile["rows_after"].sum()),
        "quality_checks": int(len(quality)),
        "quality_passed": int((quality["status"] == "PASS").sum()),
        "knowledge_corpus": corpus,
        "policy": {
            "raw_preserved": True,
            "clean_csv_encoding": "UTF-8-SIG",
            "permanent_deletion": False,
            "quarantine_used": True,
        },
    }
    (project / "06_评测/数据治理审计.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare and validate the pharmaceutical cost competition package")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    package = args.package.resolve()
    if not project.exists() or not package.exists():
        raise FileNotFoundError("Project or package directory does not exist")
    if project not in package.parents:
        raise ValueError("Package must be contained inside the project directory")

    prepare_directories(project)
    tables, profile = stage_and_clean_data(project, package)
    quality = validate_cost_data(tables)
    quality.to_csv(project / "06_评测/数据一致性检查.csv", index=False, encoding="utf-8-sig")
    analysis = build_analysis_outputs(project, tables)
    _, corpus = build_knowledge_corpus(project, package)
    build_notebook(project, package, quality, analysis, corpus)
    write_audit(project, package, profile, quality, corpus)
    print(json.dumps({
        "data_files": len(profile),
        "rows": int(profile["rows_after"].sum()),
        "quality_checks": len(quality),
        "quality_passed": int((quality["status"] == "PASS").sum()),
        "knowledge": corpus,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
