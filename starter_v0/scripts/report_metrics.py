"""Sinh bảng B1 (version evidence) cho REPORT.md từ các run JSON.

Chạy:
    python scripts/report_metrics.py evidence/runs
    python scripts/report_metrics.py runs --markdown-only

Script cũng gác điều kiện evidence của README:
    provider_error_cases == 0  và  measured_cases == total_cases
Run nào không đạt sẽ bị đánh dấu INVALID và không nên đưa vào report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

METRICS = ["case_accuracy", "tool_routing_accuracy", "argument_accuracy", "multiturn_accuracy"]


def iter_runs(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.glob("*.json")))
        else:
            files.append(path)
    return files


def is_valid(summary: dict[str, Any]) -> bool:
    return (
        summary.get("provider_error_cases") == 0
        and summary.get("measured_cases") == summary.get("total_cases")
    )


def tool_error_cases(run: dict[str, Any]) -> list[str]:
    """Case có tool result lỗi/rỗng — README yêu cầu review thủ công dù đã PASS."""
    flagged = []
    for item in run.get("results", []):
        for event in item.get("tool_results") or []:
            result = event.get("result")
            if not result or (isinstance(result, dict) and result.get("error")):
                flagged.append(item.get("id"))
                break
    return flagged


def main() -> None:
    parser = argparse.ArgumentParser(description="Tổng hợp metric từ run JSON cho REPORT.md.")
    parser.add_argument("paths", nargs="+", type=Path, help="File run JSON hoặc thư mục chứa run JSON.")
    parser.add_argument("--markdown-only", action="store_true", help="Chỉ in bảng markdown.")
    args = parser.parse_args()

    rows = []
    for path in iter_runs(args.paths):
        run = json.loads(path.read_text(encoding="utf-8"))
        summary = run.get("summary", {})
        rows.append({
            "path": path,
            "run": run,
            "summary": summary,
            "valid": is_valid(summary),
            "needs_review": tool_error_cases(run),
        })

    if not rows:
        raise SystemExit("Không tìm thấy run JSON nào.")

    rows.sort(key=lambda r: (str(r["run"].get("version")), str(r["run"].get("suite"))))

    print("| Version | Suite | Artifact version | " + " | ".join(METRICS) + " | Run file |")
    print("|---|---|---|" + "---|" * len(METRICS) + "---|")
    for row in rows:
        run, summary = row["run"], row["summary"]
        cells = []
        for name in METRICS:
            value = summary.get(name)
            cells.append("—" if value is None else f"{value:.3f}" if isinstance(value, float) else str(value))
        flag = "" if row["valid"] else " ⚠️INVALID"
        print(
            f"| {run.get('version')}{flag} | {run.get('suite')} | `{run.get('artifact_version')}` | "
            + " | ".join(cells)
            + f" | `{row['path']}` |"
        )

    if args.markdown_only:
        return

    print("\n## Evidence gate")
    for row in rows:
        summary = row["summary"]
        status = "OK" if row["valid"] else "INVALID — không dùng làm evidence"
        print(
            f"- {row['path'].name}: {status} "
            f"(total={summary.get('total_cases')}, measured={summary.get('measured_cases')}, "
            f"provider_errors={summary.get('provider_error_cases')})"
        )
        if row["needs_review"]:
            ids = ", ".join(row["needs_review"][:8])
            more = "…" if len(row["needs_review"]) > 8 else ""
            print(f"  - cần review thủ công tool result ({len(row['needs_review'])} case): {ids}{more}")

    print("\n## Failure counts")
    for row in rows:
        counts = row["summary"].get("failure_counts") or {}
        if counts:
            pairs = ", ".join(f"{k}={v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
            print(f"- {row['run'].get('version')}/{row['run'].get('suite')}: {pairs}")


if __name__ == "__main__":
    main()
