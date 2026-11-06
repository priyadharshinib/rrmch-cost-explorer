"""Headline figures shown in the report (same maths as the page's JavaScript)."""
import pytest

CAPACITY_WP = 984_500


def figs(source):
    inv = source["invoices"]
    epc = [i for i in inv if i["scope"] == "EPC"]
    add = [i for i in inv if i["scope"] != "EPC"]
    s = lambda a, k: sum(x[k] for x in a)
    return {
        "all": s(inv, "total"),
        "epc_total": s(epc, "total"),
        "epc_untaxed": s(epc, "untaxed"),
        "epc_gst": s(epc, "gst"),
        "add_total": s(add, "total"),
    }


def test_headline_totals(source):
    f = figs(source)
    assert f["all"] == pytest.approx(40_213_863.55, abs=0.5)
    assert f["epc_total"] == pytest.approx(35_636_563.64, abs=0.5)
    assert f["epc_untaxed"] == pytest.approx(31_888_067.93, abs=0.5)
    assert f["add_total"] == pytest.approx(4_577_299.91, abs=0.5)


def test_epc_plus_addons_equals_all(source):
    f = figs(source)
    assert f["epc_total"] + f["add_total"] == pytest.approx(f["all"], abs=0.01)


def test_epc_cost_per_wp(source):
    assert figs(source)["epc_total"] / CAPACITY_WP == pytest.approx(36.20, abs=0.01)


def test_five_addon_work_order_groups(source):
    add = [i for i in source["invoices"] if i["scope"] != "EPC"]
    assert len({i["work_order"] or i["work_order_title"] for i in add}) == 5
