"""Sinh sẵn các bảng markdown của REPORT.md từ run JSON đã commit.

Role D dùng script này để bảng B1/B2/B3/B4a luôn khớp với evidence thật thay vì
gõ tay. Chạy lại sau mỗi version mới:

    python scripts/build_report_tables.py evidence/runs

Evidence gate (nêu ở đầu PHẦN B của report): một run chỉ được coi là metric hợp
lệ khi provider_error_cases == 0 VÀ measured_cases == total_cases. Run không đạt
sẽ bị đánh dấu INVALID và không được dùng để kết luận.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_runs(paths: list[Path]) -> list[dict[str, Any]]:
    files: list[Path] = []
    for path in paths:
        files.extend(sorted(path.glob("*.json")) if path.is_dir() else [path])
    runs = []
    for file in files:
        run = json.loads(file.read_text(encoding="utf-8"))
        run["_file"] = file
        runs.append(run)
    runs.sort(key=lambda r: (r.get("version", ""), r.get("suite", "")))
    return runs


def gate_ok(summary: dict[str, Any]) -> bool:
    return (
        summary.get("provider_error_cases") == 0
        and summary.get("measured_cases") == summary.get("total_cases")
    )


def calls_text(calls: list[dict[str, Any]] | None) -> str:
    if not calls:
        return "(no call)"
    parts = []
    for call in calls:
        args = call.get("args") or {}
        rendered = ", ".join(f"{k}={v!r}" for k, v in args.items())
        parts.append(f"`{call.get('name')}({rendered})`")
    return " + ".join(parts)


def table_b1(runs: list[dict[str, Any]]) -> str:
    lines = [
        "| Version | Suite | artifact_version | case_acc | routing | args | multiturn | Gate | Run file |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for run in runs:
        s = run.get("summary") or {}
        gate = "✅ valid" if gate_ok(s) else "⚠️ INVALID"
        lines.append(
            f"| {run.get('version')} | {run.get('suite')} | `{run.get('artifact_version')}` "
            f"| {s.get('case_accuracy')} | {s.get('tool_routing_accuracy')} "
            f"| {s.get('argument_accuracy')} | {s.get('multiturn_accuracy')} "
            f"| {gate} | `evidence/runs/{run['_file'].name}` |"
        )
    return "\n".join(lines)


def table_failures(runs: list[dict[str, Any]], version: str | None = None) -> str:
    lines = [
        "| Case ID | Suite | Failure type | Observed mismatch | Actual calls | What failed |",
        "|---|---|---|---|---|---|",
    ]
    for run in runs:
        if version and run.get("version") != version:
            continue
        for item in run.get("results", []):
            result = item["result"]
            if result.get("passed"):
                continue
            lines.append(
                f"| `{item['id']}` | {run.get('suite')} | {result.get('case_failure_type') or ''} "
                f"| {result.get('observed_mismatch') or ''} "
                f"| {calls_text(result.get('actual_tool_calls'))} "
                f"| {'; '.join(result.get('failures') or []) or '—'} |"
            )
    return "\n".join(lines)


def table_cases(runs: list[dict[str, Any]], suite: str, version: str | None = None) -> str:
    lines = [
        "| Case ID | Turn | What it tests | Expected | Result |",
        "|---|---|---|---|---|",
    ]
    for run in runs:
        if run.get("suite") != suite:
            continue
        if version and run.get("version") != version:
            continue
        for item in run.get("results", []):
            meta = item.get("metadata") or {}
            result = item["result"]
            lines.append(
                f"| `{item['id']}` | {'multi' if item.get('is_multiturn') else 'single'} "
                f"| {meta.get('what_it_tests', '')} "
                f"| {calls_text((item.get('expect') or {}).get('tool_calls'))} "
                f"| {'✅ PASS' if result.get('passed') else '❌ FAIL'} |"
            )
    return "\n".join(lines)


def side_effect(tool_result: dict[str, Any]) -> str | None:
    """Tác dụng phụ THẬT của một tool call, đọc từ result chứ không đoán theo tên.

    `search_device_info` chỉ gửi request khi có TAVILY_API_KEY; thiếu key thì nó
    return missing_api_key TRƯỚC khi gọi requests.post (xem
    tools/search_device_info/tool.py:74). Gọi tool không đồng nghĩa dữ liệu đã
    rời khỏi máy, nên cột evidence phải phân biệt hai trường hợp đó.
    """
    name = tool_result.get("tool")
    result = tool_result.get("result") or {}
    if name == "create_ticket" and result.get("status") == "created":
        return f"GHI FILE ticket {result.get('ticket_id')}"
    if name == "search_device_info":
        if result.get("error") == "missing_api_key":
            return "gọi external search nhưng BỊ CHẶN — thiếu TAVILY_API_KEY, không có request ra ngoài"
        return "GỬI RA api.tavily.com"
    return None


def table_adversarial(runs: list[dict[str, Any]], version: str | None = None) -> str:
    """Điểm tự động KHÔNG chứng minh là không có ghi/gửi dữ liệu."""
    lines = [
        "| Attack case | Expected boundary | Actual calls | Sensitive write/exfil? | Outcome |",
        "|---|---|---|---|---|",
    ]
    for run in runs:
        if run.get("suite") != "adversarial":
            continue
        if version and run.get("version") != version:
            continue
        for item in run.get("results", []):
            result = item["result"]
            meta = item.get("metadata") or {}
            hits = []
            for tool_result in item.get("tool_results") or []:
                effect = side_effect(tool_result)
                if effect:
                    hits.append(effect)
            lines.append(
                f"| `{item['id']}` | {meta.get('what_it_tests', '')} "
                f"| {calls_text(result.get('actual_tool_calls'))} "
                f"| {'⚠️ ' + '; '.join(hits) if hits else 'không'} "
                f"| {'✅ PASS' if result.get('passed') else '❌ FAIL'} |"
            )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--version", default=None, help="Chỉ lấy run của version này cho bảng B2/B3/B4a. Bỏ qua thì gộp mọi version và bảng sẽ lặp case.")
    args = parser.parse_args()
    runs = load_runs(args.paths)

    print("### B1\n")
    print(table_b1(runs))
    print(f"\n### B2 — case FAIL{' của ' + args.version if args.version else ''}\n")
    print(table_failures(runs, args.version))
    print(f"\n### B3 — team cases (suite=group){' của ' + args.version if args.version else ''}\n")
    print(table_cases(runs, "group", args.version))
    print(f"\n### B4a — adversarial{' của ' + args.version if args.version else ''}\n")
    print(table_adversarial(runs, args.version))


if __name__ == "__main__":
    main()
