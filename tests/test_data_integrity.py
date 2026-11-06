"""The source data must be internally consistent (line items add up to invoice headers)."""
import pytest

TOL = 1.0  # rupees; invoices are rounded per line


def test_counts(source):
    assert len(source["invoices"]) == 18
    assert len(source["lines"]) == 133


def test_scope_split(source):
    inv, lines = source["invoices"], source["lines"]
    assert sum(i["scope"] == "EPC" for i in inv) == 11
    assert sum(i["scope"] == "Additional" for i in inv) == 7
    assert sum(l["scope"] == "EPC" for l in lines) == 114


def test_unique_keys(source):
    assert len({i["invoice"] for i in source["invoices"]}) == 18
    assert len({l["line_id"] for l in source["lines"]}) == 133


def test_every_line_has_an_invoice(source):
    ids = {i["invoice"] for i in source["invoices"]}
    assert all(l["invoice"] in ids for l in source["lines"])


def test_line_matches_invoice_date_and_scope(source):
    by = {i["invoice"]: i for i in source["invoices"]}
    for l in source["lines"]:
        assert l["date"] == by[l["invoice"]]["date"], l["line_id"]
        assert l["scope"] == by[l["invoice"]]["scope"], l["line_id"]


def test_invoice_header_is_untaxed_plus_gst(source):
    for i in source["invoices"]:
        assert i["untaxed"] + i["gst"] == pytest.approx(i["total"], abs=TOL), i["invoice"]


def test_lines_sum_to_invoice_header(source):
    for i in source["invoices"]:
        ls = [l for l in source["lines"] if l["invoice"] == i["invoice"]]
        assert ls, f"{i['invoice']} has no lines"
        assert sum(l["untaxed"] for l in ls) == pytest.approx(i["untaxed"], abs=TOL), i["invoice"]
        assert sum(l["total"] for l in ls) == pytest.approx(i["total"], abs=TOL), i["invoice"]


def test_line_total_not_below_untaxed(source):
    assert all(l["total"] >= l["untaxed"] for l in source["lines"])


def test_epc_lines_have_category_numbers(source):
    cats = {(l["cat_no"], l["category"]) for l in source["lines"] if l["scope"] == "EPC"}
    assert cats == {
        (1, "Solar panels"), (2, "Inverters"), (3, "Structure"),
        (4, "Electrical"), (5, "Labour"), (6, "Cranes, lifting & shifting"),
    }


def test_register_is_oldest_first(source):
    dates = [i["date"] for i in source["invoices"]]
    assert dates == sorted(dates)
