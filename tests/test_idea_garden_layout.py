from pathlib import Path
import re

INDEX = Path(__file__).resolve().parents[1] / "index.html"
HTML = INDEX.read_text()


def css_rule(selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*{{(?P<body>.*?)}}", HTML, re.S)
    assert match, f"Missing CSS rule for {selector}"
    return match.group("body")


def css_number(rule: str, property_name: str) -> float:
    match = re.search(rf"{re.escape(property_name)}\s*:\s*([0-9.]+)", rule)
    assert match, f"Missing numeric CSS property {property_name} in {rule}"
    return float(match.group(1))


def test_page_wrap_supports_wide_idea_posts():
    wrap = css_rule(".wrap")
    assert "min(1280px" in wrap or "min(1320px" in wrap


def test_idea_garden_uses_roomier_card_and_inner_spacing():
    garden = css_rule(".idea-garden")
    list_rule = css_rule(".idea-list")
    toggle = css_rule(".idea-toggle")
    content = css_rule(".idea-content")

    assert "margin: 0 18px 28px" in garden
    assert css_number(list_rule, "padding") >= 16
    assert "padding: 22px 24px" in toggle
    assert "padding: 0 24px 26px" in content


def test_mobile_idea_garden_remains_edge_safe():
    mobile_block = re.search(r"@media \(max-width: 860px\)\s*{(?P<body>.*?)\n\s*}\n\s*</style>", HTML, re.S)
    assert mobile_block, "Missing mobile media query"
    mobile_css = mobile_block.group("body")
    assert ".idea-garden" in mobile_css
    assert "margin: 0 12px 18px" in mobile_css
    assert ".idea-toggle" in mobile_css
    assert "padding: 16px" in mobile_css
