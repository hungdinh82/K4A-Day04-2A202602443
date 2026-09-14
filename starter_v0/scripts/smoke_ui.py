"""Smoke test cho UI plumbing — không gọi model, không tốn quota.

Chạy:
    python scripts/smoke_ui.py

Kiểm tra ba thứ mà `app.py` phụ thuộc vào:
1. `run_model_tool_loop` trả đúng shape (rounds / tool_calls / tool_results / status)
   cho cả trường hợp answered lẫn clarify (waiting_for_user);
2. tool thật trong registry chạy được và trả result render ra được;
3. transcript ghi ra đúng schema của `chat.py` và đọc lại được;
4. `app.py` render được và trace hiện tool name/args/result/error (cần streamlit).
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chat import run_model_tool_loop, write_transcript  # noqa: E402
from providers.base import ModelResponse, ToolCall  # noqa: E402
from tools import load_tool_declarations, to_openai_tools  # noqa: E402


class ScriptedProvider:
    """Trả về tool call đã kịch bản hoá thay vì gọi API thật."""

    default_model = "scripted"

    def __init__(self, script: list[ModelResponse]) -> None:
        self.script = list(script)
        self.calls = 0

    def complete(self, messages, tools=None, *, model=None, temperature=0.0, tool_choice=None):
        self.calls += 1
        if self.script:
            return self.script.pop(0)
        return ModelResponse(text="Không còn bước nào trong script.")


def check(label: str, condition: bool) -> None:
    print(f"[{'ok ' if condition else 'FAIL'}] {label}")
    if not condition:
        raise SystemExit(1)


SAMPLE_TURN = {
    "turn_index": 1,
    "user": "Kiểm tra VPN trên LT-204.",
    "status": "answered",
    "assistant_text": "LT-204 ghi nhận AUTH_TIMEOUT.",
    "artifact_version": "v0+psmoke+tsmoke",
    "rounds": [{
        "round": 1,
        "assistant_text": None,
        "tool_calls": [
            {"name": "inspect_device", "args": {"asset_id": "LT-204", "check": "vpn"}},
            {"name": "check_service_status", "args": {"service": "vpn"}},
        ],
        "tool_results": [
            {"tool": "inspect_device", "args": {"asset_id": "LT-204"}, "result": {"diagnostics": {"vpn": "AUTH_TIMEOUT"}}},
            {"tool": "check_service_status", "args": {"service": "vpn"}, "result": {"error": "unknown_service"}},
        ],
    }],
    "tool_events": [{"tool": "check_service_status", "result": {"error": "unknown_service"}}],
}


def check_ui_render() -> None:
    """Render app.py headless bằng Streamlit AppTest (bỏ qua nếu chưa cài streamlit)."""
    try:
        from streamlit.testing.v1 import AppTest
    except ImportError:
        print("[skip] streamlit chưa cài — bỏ qua phần render UI")
        return

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    app.run()
    check("app.py render không có exception", not app.exception)
    check("có chat input", len(app.chat_input) == 1)

    app.session_state["turns"] = [SAMPLE_TURN]
    app.run()
    check("render turn không có exception", not app.exception)
    markdown = " ".join(block.value for block in app.markdown)
    check("trace hiện tool name", "inspect_device" in markdown and "check_service_status" in markdown)
    check("trace gắn cờ tool error", "error" in markdown)
    check("trace hiện round và artifact version", "round 1" in markdown and "artifact_version" in markdown)
    check("args + result đều được in ra", len(app.code) == 4)
    metrics = {m.label: m.value for m in app.metric}
    check("sidebar đếm tool error", metrics.get("Tool errors") == "1")


def main() -> None:
    tools = to_openai_tools(load_tool_declarations(ROOT / "artifacts" / "tools.yaml"))
    check("tools.yaml load được và có tool", len(tools) > 0)

    # 1. Luồng bình thường: một tool call thật -> model trả lời.
    provider = ScriptedProvider([
        ModelResponse(tool_calls=[ToolCall(name="check_service_status", args={"service": "vpn"})]),
        ModelResponse(text="VPN đang có sự cố đã biết."),
    ])
    result = run_model_tool_loop(
        provider=provider,
        messages=[{"role": "user", "content": "VPN có vấn đề gì không?"}],
        tools=tools,
        model=None,
        max_tool_rounds=4,
    )
    check("status == answered", result["status"] == "answered")
    check("có đúng 2 round", len(result["rounds"]) == 2)
    event = result["rounds"][0]["tool_results"][0]
    check("event có tool/args/result để UI render", {"tool", "args", "result"} <= set(event))
    check("tool result không rỗng", bool(event["result"]))

    # 2. Luồng clarify: loop phải dừng và trả câu hỏi cho người dùng.
    provider = ScriptedProvider([
        ModelResponse(tool_calls=[ToolCall(name="clarify", args={"question": "Asset ID của bạn là gì?"})]),
    ])
    result = run_model_tool_loop(
        provider=provider,
        messages=[{"role": "user", "content": "Máy tôi hỏng."}],
        tools=tools,
        model=None,
        max_tool_rounds=4,
    )
    check("status == waiting_for_user", result["status"] == "waiting_for_user")
    check("câu hỏi clarify được trả về", "Asset ID" in (result["assistant_text"] or ""))

    # 3. Transcript ghi/đọc lại được theo đúng schema chat.py.
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "smoke.transcript.json"
        write_transcript(path, {"transcript_id": "smoke", "surface": "streamlit_ui", "turns": [result]})
        data = json.loads(path.read_text(encoding="utf-8"))
        check("transcript có turns và updated_at", data["turns"] and data.get("updated_at"))

    # 4. Render thật của app.py.
    check_ui_render()

    print("\nSmoke UI OK — plumbing của app.py chạy được mà không cần API key.")


if __name__ == "__main__":
    main()
