"""安全合并 team_internal 到 public_source_candidate 工作副本。

与v1（dirs_exist_ok=True 无条件覆盖，旧sha 74b13024ffb56b2c94f45173610a7dd6ce5591e442351b086989f9981cce079d）不同：
- 先按包根 SHA256.json 核验包完整性，损坏即退出，不做部分合并。
- 逐文件合并：目标缺失才复制；内容相同跳过；内容不同保留队员文件，
  送入文件以 <name>.incoming-<sha8> 并列保留并记录，绝不覆盖。
- 幂等：重复执行不改变已合并结果。
- 跳过 04_baseline（历史恢复基线证据，只读）。
运行：python prepare_team_workspace.py   报告：public_source_candidate/merge_report.json
"""
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "SHA256.json"
SRC = ROOT / "team_internal"
DST = ROOT / "public_source_candidate"
SKIP_TOP = {"04_baseline"}
SKIP_NAMES = {"merge_report.json"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_package() -> int:
    # 自身即本次修复对象，按文档头记录的旧哈希另行说明，不参与核验。
    self_rel = Path(__file__).resolve().relative_to(ROOT).as_posix()
    with MANIFEST.open(encoding="utf-8") as f:
        manifest = json.load(f)
    problems = []
    for rel, expected in manifest.items():
        if rel == self_rel:
            continue
        p = ROOT / rel
        if not p.exists():
            problems.append(f"MISSING {rel}")
        elif sha256_file(p) != expected:
            problems.append(f"MISMATCH {rel}")
    if problems:
        print("包完整性核验失败，拒绝合并：")
        for line in problems[:20]:
            print(" ", line)
        sys.exit(1)
    return len(manifest)


def main() -> None:
    count = verify_package()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest_verified": count,
        "skipped_top_level": sorted(SKIP_TOP),
        "actions": {"copied": [], "skipped_same": [], "conflict_kept_member": []},
        "note": "目标文件内容与送入不同时保留队员文件并列保存incoming副本；重复执行幂等。",
    }
    for item in sorted(SRC.iterdir()):
        if item.name in SKIP_TOP:
            continue
        if item.is_file():
            files = [item]
            base_rel = item.name
        else:
            files = [p for p in item.rglob("*") if p.is_file()]
            base_rel = item.name
        for src_file in files:
            rel = Path(base_rel) / (src_file.relative_to(item) if item.is_dir() else Path())
            if any(part in SKIP_NAMES for part in rel.parts):
                continue
            target = DST / rel
            if target.exists():
                if sha256_file(target) == sha256_file(src_file):
                    report["actions"]["skipped_same"].append(rel.as_posix())
                    continue
                side = target.with_name(
                    target.name + ".incoming-" + sha256_file(src_file)[:8]
                )
                if not side.exists():
                    shutil.copy2(src_file, side)
                report["actions"]["conflict_kept_member"].append(
                    {"path": rel.as_posix(), "incoming_saved_as": side.name}
                )
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, target)
            report["actions"]["copied"].append(rel.as_posix())
    (DST / "merge_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    a = report["actions"]
    print(
        f"包核验{count}项通过。合并完成：新增{len(a['copied'])}，"
        f"同内容跳过{len(a['skipped_same'])}，冲突保留队员文件{len(a['conflict_kept_member'])}。"
    )
    print("工作副本：public_source_candidate（含内部资料，不可公开）。详见 merge_report.json。")


if __name__ == "__main__":
    main()
