from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import TOOL_FUNCTIONS
from tools.create_ticket import tool as create_ticket_tool
from tools.search_device_info import tool as device_search_tool


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def test_create_ticket_dry_run_and_secret_rejection() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        original_ticket_dir = create_ticket_tool.TICKET_DIR
        create_ticket_tool.TICKET_DIR = Path(tmpdir)
        try:
            result = TOOL_FUNCTIONS["create_ticket"]("VPN dry run", "low", "LT-204", False)
            assert_equal(result.get("status"), "needs_confirmation", "dry-run status")
            assert_equal(list(Path(tmpdir).glob("*.json")), [], "dry-run files")

            non_secret_result = TOOL_FUNCTIONS["create_ticket"](
                "MFA enrollment issue on LT-204",
                "medium",
                "LT-204",
                False,
            )
            assert_equal(non_secret_result.get("status"), "needs_confirmation", "non-secret MFA summary")

            secret_result = TOOL_FUNCTIONS["create_ticket"](
                "VPN failure; user pasted OTP 123456",
                "medium",
                "LT-204",
                True,
            )
            assert_equal(secret_result.get("error"), "restricted_sensitive_data", "secret rejection")

            alpha_secret_result = TOOL_FUNCTIONS["create_ticket"](
                "Account issue; token abcdefgh should not be stored",
                "medium",
                "LT-204",
                True,
            )
            assert_equal(alpha_secret_result.get("error"), "restricted_sensitive_data", "alpha token rejection")

            bare_token_result = TOOL_FUNCTIONS["create_ticket"](
                "Account issue; token abc12345 should not be stored",
                "medium",
                "LT-204",
                True,
            )
            assert_equal(bare_token_result.get("error"), "restricted_sensitive_data", "bare token rejection")
            assert_equal(list(Path(tmpdir).glob("*.json")), [], "secret rejection files")
        finally:
            create_ticket_tool.TICKET_DIR = original_ticket_dir


def test_search_device_info_rejects_restricted_runtime_input_before_tavily() -> None:
    original_key = os.environ.get("TAVILY_API_KEY")
    original_post = device_search_tool.requests.post

    def fail_post(*_args, **_kwargs):
        raise AssertionError("Tavily must not be called for restricted input")

    os.environ["TAVILY_API_KEY"] = "tvly-test"
    device_search_tool.requests.post = fail_post
    try:
        result = TOOL_FUNCTIONS["search_device_info"](
            "Lenovo",
            "ThinkPad T14 Gen 4 password=Summer2026!",
            "drivers",
            2,
        )
        assert_equal(result.get("error"), "restricted_external_search_data", "secret external rejection")

        result = TOOL_FUNCTIONS["search_device_info"](
            "Lenovo",
            "ThinkPad T14 Gen 4 10.10.4.12",
            "drivers",
            2,
        )
        assert_equal(result.get("error"), "restricted_external_search_data", "internal IP rejection")

        result = TOOL_FUNCTIONS["search_device_info"](
            "Dell",
            "Latitude 7440 ticket LAB-2026-1001",
            "support",
            2,
        )
        assert_equal(result.get("error"), "restricted_external_search_data", "ticket id external rejection")

        result = TOOL_FUNCTIONS["search_device_info"](
            "Dell",
            "Latitude 7440 credential=abc12345",
            "support",
            2,
        )
        assert_equal(result.get("error"), "restricted_external_search_data", "credential external rejection")
    finally:
        device_search_tool.requests.post = original_post
        if original_key is None:
            os.environ.pop("TAVILY_API_KEY", None)
        else:
            os.environ["TAVILY_API_KEY"] = original_key


def test_lookup_ticket_status_valid_and_invalid() -> None:
    result = TOOL_FUNCTIONS["lookup_ticket_status"]("LAB-2026-1001")
    assert_equal(result.get("status"), "found", "ticket lookup status")
    assert_equal(result.get("ticket", {}).get("ticket_id"), "LAB-2026-1001", "ticket lookup id")

    missing = TOOL_FUNCTIONS["lookup_ticket_status"]("LAB-0000-9999")
    assert_equal(missing.get("error"), "ticket_not_found", "missing ticket error")
    assert_equal("available_ticket_ids" in missing, False, "missing ticket enumeration")

    invalid = TOOL_FUNCTIONS["lookup_ticket_status"]("../../../.env")
    assert_equal(invalid.get("error"), "invalid_ticket_id", "invalid ticket id error")


def test_eval_group_shape_and_bonus_case() -> None:
    path = Path(__file__).resolve().parents[1] / "data" / "eval_group.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    single_turn = [case for case in cases if "query" in case]
    multi_turn = [case for case in cases if "turns" in case]
    assert_equal(len(cases), 10, "group eval total cases")
    assert_equal(len(single_turn), 5, "group eval single-turn cases")
    assert_equal(len(multi_turn), 5, "group eval multi-turn cases")
    bonus_cases = [
        case for case in cases
        if any(call.get("name") == "lookup_ticket_status" for call in case.get("expect", {}).get("tool_calls", []))
    ]
    assert_equal(len(bonus_cases), 1, "bonus tool eval case count")


def main() -> None:
    tests = [
        test_create_ticket_dry_run_and_secret_rejection,
        test_search_device_info_rejects_restricted_runtime_input_before_tavily,
        test_lookup_ticket_status_valid_and_invalid,
        test_eval_group_shape_and_bonus_case,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")


if __name__ == "__main__":
    main()
