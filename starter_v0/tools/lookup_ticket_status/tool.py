from __future__ import annotations

import json
import re
from typing import Any

from tools._shared import ROOT, err


TICKET_STATUS_FILE = ROOT / "helpdesk_data" / "ticket_status.json"
TICKET_ID_PATTERN = re.compile(r"^LAB-\d{4}-\d{4}$", re.IGNORECASE)


def lookup_ticket_status(ticket_id: str = "", include_history: bool = False) -> dict[str, Any]:
    if not isinstance(ticket_id, str):
        return {"tool": "lookup_ticket_status", "error": "invalid_ticket_id_type"}
    if not isinstance(include_history, bool):
        return {"tool": "lookup_ticket_status", "error": "invalid_include_history_type"}

    normalized_ticket_id = (ticket_id or "").strip().upper()
    if not normalized_ticket_id:
        return {"tool": "lookup_ticket_status", "error": "missing_ticket_id"}
    if not TICKET_ID_PATTERN.fullmatch(normalized_ticket_id):
        return {"tool": "lookup_ticket_status", "ticket_id": normalized_ticket_id, "error": "invalid_ticket_id"}

    try:
        data = json.loads(TICKET_STATUS_FILE.read_text(encoding="utf-8"))
        ticket = next((item for item in data["tickets"] if item["ticket_id"] == normalized_ticket_id), None)
        if ticket is None:
            return {
                "tool": "lookup_ticket_status",
                "ticket_id": normalized_ticket_id,
                "error": "ticket_not_found",
            }

        visible_ticket = dict(ticket)
        if not include_history:
            visible_ticket.pop("history", None)
        return {
            "tool": "lookup_ticket_status",
            "status": "found",
            "ticket": visible_ticket,
            "snapshot_at": data["snapshot_at"],
        }
    except Exception as exc:
        return err("lookup_ticket_status", exc)
