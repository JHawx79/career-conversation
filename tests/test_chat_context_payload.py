from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
HTML = INDEX.read_text()


def extract_build_payload_message_body() -> str:
    match = re.search(
        r"function buildPayloadMessage\(visibleMessage, contexts\) \{(?P<body>.*?)\n    \}",
        HTML,
        re.S,
    )
    assert match, "Missing buildPayloadMessage function"
    return match.group("body")


def test_hidden_context_payload_explicitly_labels_site_reference_not_user_message():
    body = extract_build_payload_message_body()

    assert "SYSTEM-SUPPLIED SITE REFERENCE" in body
    assert "from jpartney.space" in body
    assert "not written by the visitor" in body
    assert "not instructions" in body
    assert "reference" in body


def test_payload_keeps_visible_message_before_delimited_context():
    body = extract_build_payload_message_body()

    assert body.index("${visibleMessage}") < body.index("${contextText}")
    assert "<context" in body
    assert "</context>" in body


def test_frontend_calls_dedicated_history_endpoint():
    assert "gradio_api/call/chat_with_history" in HTML
    assert "JSON.stringify({ data: [payloadMessage, chatHistory] })" in HTML


def test_matching_context_is_appended_once_then_carried_by_history():
    assert "const sessionReferenceContexts = selectedContext?.id && !selectedContextWasUsed ? [selectedContext] : []" in HTML
    assert "const payloadMessage = buildPayloadMessage(visibleMessage, sessionReferenceContexts)" in HTML
    assert "chatHistory.push({ role: 'user', content: payloadMessage })" in HTML


def test_hidden_context_is_preserved_in_model_history_after_first_send():
    assert "chatHistory.push({ role: 'user', content: payloadMessage })" in HTML
    assert "chatHistory.push({ role: 'user', content: visibleMessage })" not in HTML
    assert "addChatMessage('user', visibleMessage)" in HTML


def test_chat_is_ready_on_page_load_without_manual_cover():
    assert "id=\"loadChat\"" not in HTML
    assert "Load conversation" not in HTML
    assert "function initializeChat" in HTML
    assert "document.addEventListener('DOMContentLoaded', initializeChat)" in HTML


def test_second_turn_request_sends_hidden_context_in_history_not_current_message():
    result = subprocess.run(
        ["node", "tests/chat_payload_harness.js"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload == {
        "firstCurrentHasContext": True,
        "firstHistoryLength": 0,
        "secondCurrentHasContext": False,
        "secondHistoryContextCount": 1,
        "secondHistoryRoles": ["user", "assistant"],
    }


def test_failed_context_send_does_not_mark_context_used_before_history_commit():
    result = subprocess.run(
        ["node", "tests/chat_payload_failure_harness.js"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload == {
        "firstCurrentHasContext": True,
        "secondCurrentHasContext": True,
        "secondHistoryContextCount": 0,
    }
