from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from tools._shared import ROOT, err


TICKET_DIR = ROOT / "tickets"
ASSET_ID_PATTERN = re.compile(r"^(?:LT|DT|MB|PR|RM)-\d+$", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"""
    \b(?:password|passwd|token|api[ _-]?key|credential|recovery[ _-]?code)\b
    (?:\s*[:=]\s*|\s+(?:is|la|là)\s+)
    [A-Za-z0-9][A-Za-z0-9!@#$%^&*._-]{3,}
    |
    \b(?:mfa|otp)\b
    (?:\s*[:=]\s*|\s+(?:is|la|là|code)\s+)
    \d{4,8}\b
    """,
    re.IGNORECASE | re.VERBOSE,
)
BARE_SECRET_VALUE_PATTERN = re.compile(
    r"\b(?:password|passwd|token|api[ _-]?key|credential|recovery[ _-]?code)\b"
    r"\s+([A-Za-z0-9][A-Za-z0-9!@#$%^&*._-]{3,})\b",
    re.IGNORECASE,
)
BARE_MFA_CODE_PATTERN = re.compile(r"\b(?:mfa|otp)(?:\s+code)?\s+\d{4,8}\b", re.IGNORECASE)
SAFE_SECRET_CONTEXT_WORDS = {
    "access",
    "enroll",
    "enrolled",
    "enrollment",
    "expired",
    "expiry",
    "issue",
    "login",
    "policy",
    "problem",
    "request",
    "reset",
    "rotate",
    "rotation",
    "status",
    "workflow",
}


def _contains_sensitive_data(text: str) -> bool:
    if SECRET_VALUE_PATTERN.search(text) or BARE_MFA_CODE_PATTERN.search(text):
        return True
    for match in BARE_SECRET_VALUE_PATTERN.finditer(text):
        if match.group(1).casefold() not in SAFE_SECRET_CONTEXT_WORDS:
            return True
    return False


def create_ticket(
    summary: str = "",
    priority: str = "medium",
    asset_id: str = "",
    confirmed: bool = False,
) -> dict[str, Any]:
    if not isinstance(summary, str):
        return {"tool": "create_ticket", "error": "invalid_summary_type"}
    if not isinstance(priority, str):
        return {"tool": "create_ticket", "error": "invalid_priority_type"}
    if not isinstance(asset_id, str):
        return {"tool": "create_ticket", "error": "invalid_asset_id_type"}
    normalized_summary = (summary or "").strip()
    normalized_priority = (priority or "medium").strip().lower()
    if not normalized_summary:
        return {"tool": "create_ticket", "error": "missing_summary"}
    if len(normalized_summary) > 1000:
        return {"tool": "create_ticket", "error": "summary_too_long", "max_length": 1000}
    if normalized_priority not in {"low", "medium", "high", "critical"}:
        return {"tool": "create_ticket", "error": "invalid_priority", "priority": normalized_priority}
    normalized_asset = (asset_id or "").strip().upper()
    if normalized_asset and not ASSET_ID_PATTERN.fullmatch(normalized_asset):
        return {"tool": "create_ticket", "error": "invalid_asset_id"}
    if _contains_sensitive_data(normalized_summary):
        return {
            "tool": "create_ticket",
            "error": "restricted_sensitive_data",
            "message": "Remove credentials, tokens, MFA values, and recovery codes from the ticket summary.",
        }
    if confirmed is not True:
        return {
            "tool": "create_ticket",
            "status": "needs_confirmation",
            "message": "Create the ticket only after explicit user confirmation.",
        }
    try:
        now = datetime.now(timezone.utc)
        seed = f"{now.isoformat()}|{normalized_summary}|{normalized_priority}|{normalized_asset}"
        ticket_id = "LAB-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8].upper()
        payload = {
            "ticket_id": ticket_id,
            "summary": normalized_summary,
            "priority": normalized_priority,
            "asset_id": normalized_asset or None,
            "created_at": now.isoformat(),
            "source": "educational_local_mock",
        }
        TICKET_DIR.mkdir(parents=True, exist_ok=True)
        path = TICKET_DIR / f"{ticket_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"tool": "create_ticket", "status": "created", "ticket_id": ticket_id, "path": str(path)}
    except Exception as exc:
        return err("create_ticket", exc)
