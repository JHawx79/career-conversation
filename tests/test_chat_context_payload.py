from pathlib import Path
import re

INDEX = Path(__file__).resolve().parents[1] / "index.html"
HTML = INDEX.read_text()


def extract_build_payload_message_body() -> str:
    match = re.search(
        r"function buildPayloadMessage\(visibleMessage, context\) \{(?P<body>.*?)\n    \}",
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

    assert body.index("${visibleMessage}") < body.index("<context")
    assert "<context" in body
    assert "</context>" in body


def test_hidden_context_never_pushed_to_visible_chat_history():
    assert "chatHistory.push({ role: 'user', content: visibleMessage })" in HTML
    assert "chatHistory.push({ role: 'user', content: payloadMessage })" not in HTML


def test_chat_is_ready_on_page_load_without_manual_cover():
    assert "id=\"loadChat\"" not in HTML
    assert "Load conversation" not in HTML
    assert "function initializeChat" in HTML
    assert "document.addEventListener('DOMContentLoaded', initializeChat)" in HTML
