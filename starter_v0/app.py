"""Streamlit UI for the IT Helpdesk Agent.

The UI deliberately reuses `run_model_tool_loop` from `chat.py` so the CLI, the
eval evidence and this UI all exercise the SAME agent loop. It also writes the
same transcript schema as `chat.py`, so any UI session doubles as transcript
evidence for the report.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chat import (  # noqa: E402 - sys.path bootstrap must run first
    json_text,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from env_loader import load_lab_env  # noqa: E402
from providers import make_provider  # noqa: E402
from tools import load_tool_declarations, to_openai_tools  # noqa: E402
from versioning import artifact_version_dict, build_artifact_version  # noqa: E402

ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
EVIDENCE_DIR = ROOT / "evidence" / "transcripts"

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini"]

# Tên env var mà từng provider adapter đọc (xem providers/*.py).
PROVIDER_ENV = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

KEY_ENV_VARS = [*PROVIDER_ENV.values(), "TAVILY_API_KEY"]


def refresh_env() -> None:
    """Nạp lại .env nhưng không để dòng rỗng xoá key đã export ngoài shell.

    `env_loader.load_lab_env` dùng override=True, nên `OPENROUTER_API_KEY=` rỗng
    trong .env sẽ ghi đè giá trị thật trong môi trường. Giữ lại value non-empty.
    """
    preserved = {name: os.environ.get(name) for name in KEY_ENV_VARS}
    load_lab_env(ROOT)
    for name, value in preserved.items():
        if value and not os.environ.get(name):
            os.environ[name] = value

SAMPLE_PROMPTS = [
    "VPN của tôi không kết nối được, kiểm tra giúp tôi.",
    "Kiểm tra tình trạng máy LT-204 và dịch vụ VPN.",
    "Tra cứu thiết bị được cấp cho nhân viên EMP-1042.",
    "Tạo ticket cho sự cố máy in ở tầng 3.",
]

# status -> (nhãn hiển thị, css class)
STATUS_META = {
    "answered": ("answered", "ok"),
    "waiting_for_user": ("waiting for user", "warn"),
    "max_tool_rounds": ("max tool rounds", "warn"),
    "provider_error": ("provider error", "bad"),
}

CSS = """
<style>
:root {
  --cream: #FBF8F1;
  --cream-2: #F4F0E6;
  --ink: #2B2D2A;
  --muted: #6F7268;
  --green: #2F5D53;
  --line: #E4DED0;
}
.stApp { background: var(--cream); }
.block-container { padding-top: 2.2rem; max-width: 1080px; }
section[data-testid="stSidebar"] { background: var(--cream-2); border-right: 1px solid var(--line); }

.hd-brand { display:flex; align-items:baseline; gap:.6rem; margin-bottom:.2rem; }
.hd-brand h1 { font-size: 2.1rem; font-weight: 800; letter-spacing:-.02em; color: var(--ink); margin:0; }
.hd-brand h1 em { font-style: normal; color: var(--green); }
.hd-sub { color: var(--muted); font-size: .96rem; margin: 0 0 1.1rem 0; }

.hd-hero { text-align:center; padding: 2.4rem 1rem 1.2rem 1rem; }
.hd-hero h2 { font-size: 2.6rem; font-weight: 800; letter-spacing:-.03em; color: var(--ink); margin:0 0 .4rem 0; line-height:1.15; }
.hd-hero h2 em { font-style: normal; color: var(--green); }
.hd-hero p { color: var(--muted); font-size: 1.02rem; margin:0; }

.hd-badge {
  display:inline-block; padding:.16rem .6rem; border-radius:999px;
  font-size:.74rem; font-weight:700; letter-spacing:.01em; border:1px solid transparent;
}
.hd-badge.ok   { background:#E7F0EA; color:#2F5D53; border-color:#CADCD1; }
.hd-badge.warn { background:#FBF0DC; color:#8A6314; border-color:#EDDCB6; }
.hd-badge.bad  { background:#FAE6E3; color:#9B3226; border-color:#EFCCC6; }
.hd-badge.tool { background:#EDEAE0; color:#3F4239; border-color:#DED8C8; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }
.hd-badge.round{ background:#FFFFFF; color:var(--muted); border-color:var(--line); }

.hd-card { background:#FFFFFF; border:1px solid var(--line); border-radius:16px; padding:.85rem 1rem; margin-bottom:.7rem; }
.hd-card .hd-head { display:flex; align-items:center; gap:.45rem; flex-wrap:wrap; margin-bottom:.15rem; }
.hd-label { font-size:.72rem; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); font-weight:700; margin:.5rem 0 .15rem 0; }

.hd-meta { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.76rem; color:var(--muted); word-break:break-all; }

div.stButton > button {
  border-radius:999px; border:1px solid var(--line); background:#FFFFFF; color:var(--ink);
  font-weight:600; padding:.42rem 1rem;
}
div.stButton > button:hover { border-color:var(--green); color:var(--green); }
div.stButton > button[kind="primary"] { background:var(--ink); color:#FFF; border-color:var(--ink); }
[data-testid="stChatInput"] { border-radius:20px; border:1px solid var(--line); background:#FFFFFF; }
details[data-testid="stExpander"] { border:1px solid var(--line); border-radius:14px; background:#FFFFFF; }
</style>
"""


def badge(text: str, kind: str = "round") -> str:
    return f'<span class="hd-badge {kind}">{text}</span>'


@st.cache_resource(show_spinner=False)
def get_provider(name: str):
    return make_provider(name)


def load_interface(tools_path: Path) -> list[dict[str, Any]]:
    return to_openai_tools(load_tool_declarations(tools_path))


def init_session(version: str, provider_name: str) -> None:
    if "transcript" in st.session_state:
        return
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), "ui", timestamp])
    st.session_state.transcript_id = transcript_id
    st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        "surface": "streamlit_ui",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    st.session_state.history = []
    st.session_state.turns = []
    st.session_state.turn_index = 0


def reset_session() -> None:
    for key in ("transcript", "transcript_id", "transcript_path", "history", "turns", "turn_index", "pending"):
        st.session_state.pop(key, None)


def split_envelope(text: str | None) -> tuple[str, dict[str, Any] | None]:
    """Tách JSON envelope mà prompt v0 yêu cầu ra khỏi phần người dùng đọc.

    UI không giấu envelope: phần `reply` hiện ra cho dễ đọc, JSON gốc vẫn nằm
    nguyên trong tool trace để dùng làm evidence.
    """
    if not text:
        return "", None
    stripped = text.strip()
    if not stripped.startswith("{"):
        return text, None
    try:
        payload = json.loads(stripped)
    except (ValueError, TypeError):
        return text, None
    if not isinstance(payload, dict) or "reply" not in payload:
        return text, None
    reply = payload.get("reply")
    return (reply if isinstance(reply, str) else json_text(reply)), payload


def result_kind(result: Any) -> str:
    """Classify a tool result so the trace shows error/pause, not just JSON."""
    if isinstance(result, dict):
        if result.get("error"):
            return "bad"
        if result.get("awaiting_user"):
            return "warn"
        if not result:
            return "warn"
    if result in (None, [], {}):
        return "warn"
    return "ok"


def render_tool_event(event: dict[str, Any]) -> None:
    result = event.get("result")
    kind = result_kind(result)
    note = {"bad": "error", "warn": "needs manual review", "ok": "ok"}[kind]
    st.markdown(
        '<div class="hd-card"><div class="hd-head">'
        + badge(event.get("tool", "?"), "tool")
        + badge(note, kind)
        + "</div></div>",
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="hd-label">args</div>', unsafe_allow_html=True)
        st.code(json_text(event.get("args", {})), language="json")
    with right:
        st.markdown('<div class="hd-label">result</div>', unsafe_allow_html=True)
        st.code(json_text(result, max_chars=4000), language="json")


def render_trace(turn: dict[str, Any]) -> None:
    rounds = turn.get("rounds") or []
    total_calls = sum(len(r.get("tool_calls") or []) for r in rounds)
    label, kind = STATUS_META.get(turn.get("status", ""), (turn.get("status", "?"), "warn"))
    header = f"Tool trace — {total_calls} call · {len(rounds)} round · status: {label}"
    with st.expander(header, expanded=True):
        if turn.get("error"):
            st.error(turn["error"])
        if not rounds:
            st.caption("Không có tool call nào trong lượt này.")
        for record in rounds:
            st.markdown(
                '<div class="hd-head">'
                + badge(f"round {record.get('round')}", "round")
                + badge(label, kind)
                + "</div>",
                unsafe_allow_html=True,
            )
            if record.get("assistant_text"):
                st.caption(record["assistant_text"])
            results = record.get("tool_results") or []
            for event in results:
                render_tool_event(event)
            # Một call có thể chưa có result nếu loop dừng sớm (clarify / lỗi).
            for call in (record.get("tool_calls") or [])[len(results):]:
                st.markdown(
                    '<div class="hd-card"><div class="hd-head">'
                    + badge(call.get("name", "?"), "tool")
                    + badge("no result — loop stopped", "warn")
                    + "</div></div>",
                    unsafe_allow_html=True,
                )
        _, envelope = split_envelope(turn.get("assistant_text"))
        if envelope is not None:
            st.markdown('<div class="hd-label">assistant envelope (raw)</div>', unsafe_allow_html=True)
            st.code(json_text(envelope), language="json")
        st.markdown(
            f'<div class="hd-meta">artifact_version: {turn.get("artifact_version", "?")}</div>',
            unsafe_allow_html=True,
        )


def render_turn(turn: dict[str, Any]) -> None:
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant"):
        display_text, envelope = split_envelope(turn.get("assistant_text"))
        st.markdown(display_text or "_(không có câu trả lời)_")
        if envelope is not None:
            fields = " · ".join(
                f"{key}: {envelope.get(key)}" for key in ("intent", "action", "evidence_ids") if key in envelope
            )
            if fields:
                st.markdown(f'<div class="hd-meta">{fields}</div>', unsafe_allow_html=True)
        render_trace(turn)


def run_turn(user_text: str, config: dict[str, Any]) -> None:
    st.session_state.turn_index += 1
    messages = [
        {"role": "system", "content": config["system_prompt"]},
        *trim_history(st.session_state.history, config["history_window"]),
        {"role": "user", "content": user_text},
    ]
    turn: dict[str, Any] = {
        "turn_index": st.session_state.turn_index,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
        **artifact_version_dict(config["artifact_version"]),
        "provider": config["provider_name"],
        "model": config["model"],
    }
    try:
        result = run_model_tool_loop(
            provider=config["provider"],
            messages=messages,
            tools=config["tools"],
            model=config["model"],
            max_tool_rounds=config["max_tool_rounds"],
        )
        turn.update(result)
        st.session_state.history.append({"role": "user", "content": user_text})
        st.session_state.history.append({"role": "assistant", "content": result["assistant_text"]})
    except Exception as exc:  # provider/network failure is evidence too
        turn.update({
            "status": "provider_error",
            "error": f"{type(exc).__name__}: {exc}",
            "assistant_text": None,
        })

    turn["ended_at"] = now_iso()
    st.session_state.turns.append(turn)
    st.session_state.transcript["turns"].append(turn)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)


def main() -> None:
    st.set_page_config(page_title="IT Helpdesk Agent", page_icon="🛠️", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    # Nạp lại .env mỗi lần rerun: sửa key xong chỉ cần bấm lại, không phải restart server.
    refresh_env()

    with st.sidebar:
        st.markdown("### Run config")
        # Mặc định chọn provider đã có key trong .env thay vì luôn chọn openrouter.
        ready = [name for name in PROVIDERS if os.getenv(PROVIDER_ENV[name])]
        provider_name = st.selectbox(
            "Provider",
            PROVIDERS,
            index=PROVIDERS.index(ready[0]) if ready else 0,
            format_func=lambda name: f"{name} ✓" if os.getenv(PROVIDER_ENV[name]) else name,
            help="Dấu ✓ = env var tương ứng đã có giá trị trong .env.",
        )
        model = st.text_input("Model", value="", placeholder="để trống = default của provider") or None
        version = st.text_input("Version label", value="v0", help="Nhãn ghi vào transcript, ví dụ v0/v1/v2/v3.")
        system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
        tools_path = ARTIFACTS_DIR / "tools.yaml"
        history_window = st.slider("History window (cặp user/assistant)", 1, 10, 5)
        max_tool_rounds = st.slider("Max tool rounds", 1, 8, 4)

        artifact_version = build_artifact_version(version, system_prompt_path, tools_path)
        st.markdown("### Artifact version")
        st.markdown(
            f'<div class="hd-card"><div class="hd-meta">'
            f'{artifact_version.artifact_version}<br>'
            f'prompt_hash: {artifact_version.prompt_hash[:16]}…<br>'
            f'tools_hash: {artifact_version.tools_hash[:16]}…'
            f"</div></div>",
            unsafe_allow_html=True,
        )

        init_session(version, provider_name)
        turns = st.session_state.turns
        tool_calls = sum(len(t.get("tool_events") or []) for t in turns)
        tool_errors = sum(
            1
            for t in turns
            for e in (t.get("tool_events") or [])
            if result_kind(e.get("result")) == "bad"
        )
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Turns", len(turns))
        col_b.metric("Tool calls", tool_calls)
        col_c.metric("Tool errors", tool_errors)

        st.markdown("### Transcript")
        st.markdown(
            f'<div class="hd-meta">{st.session_state.transcript_path}</div>',
            unsafe_allow_html=True,
        )
        if st.button("Pin làm evidence", use_container_width=True, disabled=not turns):
            EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
            target = EVIDENCE_DIR / st.session_state.transcript_path.name
            shutil.copyfile(st.session_state.transcript_path, target)
            st.success(f"Đã copy vào {target.relative_to(ROOT)}")
        st.markdown("### Provider key")
        env_var = PROVIDER_ENV.get(provider_name, "")
        if os.getenv(env_var):
            st.markdown(f'{badge(env_var + " đã nạp", "ok")}', unsafe_allow_html=True)
        else:
            st.markdown(f'{badge(env_var + " chưa có", "bad")}', unsafe_allow_html=True)
        if st.button("Kiểm tra lại key", use_container_width=True):
            refresh_env()
            st.rerun()

        if st.button("Phiên mới", use_container_width=True):
            reset_session()
            st.rerun()

    st.markdown(
        '<div class="hd-brand"><h1>IT Helpdesk <em>Agent</em></h1></div>'
        '<p class="hd-sub">Mọi lượt chat đều chạy qua <code>run_model_tool_loop</code> của chat.py '
        "và được ghi lại theo đúng schema transcript của lab.</p>",
        unsafe_allow_html=True,
    )

    try:
        tools = load_interface(tools_path)
    except Exception as exc:
        st.error(f"Không đọc được tools.yaml: {type(exc).__name__}: {exc}")
        return

    config = {
        "system_prompt": system_prompt_path.read_text(encoding="utf-8"),
        "tools": tools,
        "provider_name": provider_name,
        "model": model,
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "artifact_version": artifact_version,
    }

    if not st.session_state.turns:
        st.markdown(
            '<div class="hd-hero"><h2>Hỏi gì đó về <em>máy, tài khoản hoặc dịch vụ IT</em></h2>'
            "<p>Agent sẽ chọn tool, và toàn bộ tool call · args · result hiện ngay dưới câu trả lời.</p></div>",
            unsafe_allow_html=True,
        )
        cols = st.columns(len(SAMPLE_PROMPTS))
        for col, prompt in zip(cols, SAMPLE_PROMPTS):
            if col.button(prompt, use_container_width=True):
                st.session_state.pending = prompt
                st.rerun()

    for turn in st.session_state.turns:
        render_turn(turn)

    env_var = PROVIDER_ENV.get(provider_name, "")
    key_missing = not os.getenv(env_var)
    if key_missing:
        st.warning(
            f"Chưa có **{env_var}**. Mở `starter_v0/.env`, điền giá trị cho `{env_var}=`, "
            "lưu lại rồi bấm **Kiểm tra lại key** ở sidebar. "
            "File `.env` đã được gitignore nên key không bị commit."
        )

    typed = st.chat_input(
        "Mô tả sự cố hoặc yêu cầu của bạn…" if not key_missing else f"Điền {env_var} vào .env để bắt đầu",
        disabled=key_missing,
    )
    pending = st.session_state.pop("pending", None)
    user_text = typed or pending
    if not user_text:
        return

    with st.chat_message("user"):
        st.markdown(user_text)
    with st.chat_message("assistant"):
        with st.spinner("Agent đang chọn tool…"):
            try:
                config["provider"] = get_provider(provider_name)
            except Exception as exc:
                st.error(f"Không khởi tạo được provider: {type(exc).__name__}: {exc}")
                return
            run_turn(user_text, config)
    st.rerun()


if __name__ == "__main__":
    main()
