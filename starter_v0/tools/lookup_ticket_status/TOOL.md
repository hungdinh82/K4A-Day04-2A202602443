---
name: lookup_ticket_status
track: bonus
kind: local_status
provider: mock_ticket_status
requires_env: []
inputs: [ticket_id, include_history]
outputs: [status, ticket, snapshot_at]
side_effect: false
---
# lookup_ticket_status

Looks up one existing mock helpdesk ticket by ticket ID and returns its current
state, priority, owner group, asset ID, last update, and next step. It is
read-only and must not create, edit, or delete tickets. Use it when the user
asks for the status or progress of a known ticket ID such as `LAB-2026-1001`.
Do not use it for new incidents, ticket creation, missing ticket IDs, or
requests that only provide an asset ID.
