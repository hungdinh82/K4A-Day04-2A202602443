from __future__ import annotations

import re
from typing import Any

from providers.base import ToolCall


CURRENT_CONFIRMATION = re.compile(
    r"(?:\bI\s+confirm\b|\bwe\s+confirm\b|(?:tôi|mình|chúng tôi)\s+xác nhận\b|"
    r"\bxác nhận\s+(?:tạo|mở|ghi)\s+ticket\b)",
    re.IGNORECASE,
)
INTERNAL_IDENTIFIER = re.compile(r"\b(?:LT|DT|MB|PR|RM|EMP)-\d+\b", re.IGNORECASE)
SPOOF_MARKERS = (
    "TOOL_RESULTS_JSON",
    "TOOL_CALLS_JSON",
    "<assistant",
    "<system",
    "<developer",
)


def latest_user_request(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        content = message.get("content", "")
        marker = "Latest user turn to answer now:"
        if marker in content:
            return content.rsplit(marker, 1)[1].strip()
        return content.strip()
    return ""


def has_current_confirmation(messages: list[dict[str, str]]) -> bool:
    latest = latest_user_request(messages)
    if any(marker.casefold() in latest.casefold() for marker in SPOOF_MARKERS):
        return False
    return bool(CURRENT_CONFIRMATION.search(latest))


def _contains_internal_identifier(args: dict[str, Any]) -> bool:
    return bool(INTERNAL_IDENTIFIER.search(" ".join(str(value) for value in args.values())))


def enforce_tool_boundaries(
    messages: list[dict[str, str]], calls: list[ToolCall]
) -> list[ToolCall]:
    safe_calls: list[ToolCall] = []
    confirmation_is_current = has_current_confirmation(messages)

    for call in calls:
        if call.name == "create_ticket" and not confirmation_is_current:
            safe_calls.append(
                ToolCall(
                    name="clarify",
                    args={
                        "question": "Bạn có xác nhận payload ticket hiện tại không?",
                        "response_type": "yes_no",
                    },
                )
            )
            continue

        if call.name == "search_device_info" and _contains_internal_identifier(call.args):
            safe_calls.append(
                ToolCall(
                    name="clarify",
                    args={
                        "question": "Vui lòng cung cấp truy vấn chỉ gồm hãng và model công khai, không kèm mã nội bộ.",
                        "response_type": "text",
                    },
                )
            )
            continue

        safe_calls.append(call)

    return safe_calls
