from pathlib import Path
import re

INDEX = Path(__file__).resolve().parents[1] / "index.html"
HTML = INDEX.read_text()


def test_conversation_intro_copy_is_removed_so_chat_owns_card_space():
    conversation = re.search(
        r'<section id="conversation" class="wrap">(?P<body>.*?)</section>',
        HTML,
        re.S,
    )
    assert conversation, "Missing conversation section"
    body = conversation.group("body")

    assert "Talk with my AI career companion" not in body
    assert "This custom chat is ready when the page loads" not in body
    assert 'class="section-head"' not in body


def test_chat_loader_expands_to_fill_removed_intro_space_on_mobile():
    base_rule = re.search(r"\.chat-loader \{(?P<body>.*?)\n    \}", HTML, re.S)
    assert base_rule, "Missing base .chat-loader rule"
    assert "margin: 0;" in base_rule.group("body")

    mobile_rule = re.search(
        r"@media \(max-width: 860px\) \{(?P<body>.*?)\n    \}\n  </style>",
        HTML,
        re.S,
    )
    assert mobile_rule, "Missing mobile media rule"
    mobile_body = mobile_rule.group("body")

    assert ".chat-loader { margin: 0;" in mobile_body
    assert ".custom-chat { height: min(760px, 88vh); min-height: 620px; }" in mobile_body
