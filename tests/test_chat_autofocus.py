from pathlib import Path
import re

INDEX = Path(__file__).resolve().parents[1] / "index.html"
HTML = INDEX.read_text()


def extract_initialize_chat_body() -> str:
    match = re.search(
        r"function initializeChat\(\) \{(?P<body>.*?)\n    \}\n\n    document\.addEventListener\('DOMContentLoaded', initializeChat\)",
        HTML,
        re.S,
    )
    assert match, "Missing initializeChat function"
    return match.group("body")


def test_chat_initialization_does_not_autofocus_input_on_page_load():
    body = extract_initialize_chat_body()

    assert ".focus(" not in body
    assert "autofocus" not in body.lower()
