import json
from decimal import Decimal

import pytest

from core import build_html, fetch_all, image_data_uri, normalize, user_initial


class FakeQuery:
    def __init__(self, rows):
        self.rows, self.lo, self.hi = rows, 0, None

    def select(self, *_):
        return self

    def order(self, *_):
        return self

    def range(self, lo, hi):
        self.lo, self.hi = lo, hi
        return self

    def execute(self):
        class R:  # noqa: D401
            pass
        r = R()
        r.data = self.rows[self.lo : self.hi + 1]
        return r


class FakeClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return FakeQuery(self.tables[name])


def test_normalize_converts_types_and_renames_check():
    inv = [{"invoice": "A", "date": "2026-01-02", "untaxed": Decimal("10.50"), "gst": "1.5", "total": 12, "sort_order": 0}]
    lines = [{"line_id": "L1", "invoice": "A", "date": "2026-01-02", "qty": Decimal("2.500"), "rate": "3.2",
              "untaxed": 1, "total": 2, "check_note": "look", "sort_order": 0}]
    d = normalize(inv, lines)
    assert d["invoices"][0]["untaxed"] == 10.5 and isinstance(d["invoices"][0]["gst"], float)
    assert d["lines"][0]["check"] == "look" and "check_note" not in d["lines"][0]
    assert d["lines"][0]["qty"] == 2.5
    assert "sort_order" not in d["lines"][0] and "sort_order" not in d["invoices"][0]


def test_normalize_keeps_line_gst_rate_as_text():
    d = normalize([], [{"line_id": "L", "gst": "5%", "sort_order": 0}])
    assert d["lines"][0]["gst"] == "5%"


def test_normalize_blank_check_becomes_empty_string():
    d = normalize([], [{"line_id": "L", "check_note": None, "sort_order": 0}])
    assert d["lines"][0]["check"] == ""


def test_normalize_orders_by_sort_order_without_mutating_input():
    rows = [{"line_id": "b", "sort_order": 2}, {"line_id": "a", "sort_order": 1}]
    d = normalize([], rows)
    assert [r["line_id"] for r in d["lines"]] == ["a", "b"]
    assert rows[0]["line_id"] == "b" and "sort_order" in rows[0]


def test_fetch_all_pages_past_the_limit():
    rows = [{"n": i} for i in range(2500)]
    got = fetch_all(FakeClient({"t": rows}), "t", "n", page_size=1000)
    assert got == rows


def test_fetch_all_exact_multiple_of_page_size():
    rows = [{"n": i} for i in range(2000)]
    assert len(fetch_all(FakeClient({"t": rows}), "t", "n", page_size=1000)) == 2000


def test_fetch_all_empty_table():
    assert fetch_all(FakeClient({"t": []}), "t", "n") == []


def test_template_has_single_placeholder(template):
    assert template.count("__DATA__") == 1


def test_build_html_injects_valid_json(template, source):
    html = build_html(template, source)
    assert "__DATA__" not in html
    start = html.index("const DATA = ") + len("const DATA = ")
    obj, _ = json.JSONDecoder().raw_decode(html[start:])
    assert obj == source


def test_build_html_escapes_script_close_tag(template):
    html = build_html(template, {"lines": [{"x": "</script><b>"}], "invoices": []})
    assert "</script><b>" not in html


def test_build_html_rejects_bad_template():
    with pytest.raises(ValueError):
        build_html("no placeholder", {})
    with pytest.raises(ValueError):
        build_html("__DATA__ __DATA__", {})


def test_template_keeps_branding_and_features(template):
    for needle in ("RRMCH 984.5 kWp rooftop solar", "Asase Energy", "id=\"drawer\"", "Invoice register", "data:image/png;base64"):
        assert needle in template


def test_template_is_responsive_and_fits_frame(template):
    assert "max-width:640px" in template and "max-width:380px" in template
    assert "min(340px,100%)" in template          # add-on cards never overflow a phone
    assert "window.frameElement" in template      # frame height follows the screen


def test_logo_file_is_a_png_and_data_uri_roundtrips():
    from pathlib import Path
    logo = Path(__file__).resolve().parent.parent / "assets" / "asase_logo.png"
    assert logo.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    uri = image_data_uri(logo)
    assert uri.startswith("data:image/png;base64,") and len(uri) > 1000


def test_user_initial():
    assert user_initial("priya@x.com") == "P"
    assert user_initial("  7bit@x.com") == "7"
    assert user_initial("") == "U" and user_initial("...") == "U"


def test_wide_layout_single_line_title_and_avatar_room(template):
    assert ".wrap{max-width:1560px;" in template and ".bb{max-width:1560px;" in template
    assert "max-width:22ch" not in template                      # title no longer forced to wrap
    assert "@media (min-width:1200px){h1{white-space:nowrap}}" in template
    assert ".bb{padding-right:76px}" in template                 # space for the avatar after the header text
