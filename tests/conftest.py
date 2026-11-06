import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def source():
    """Original data extracted from the HTML report."""
    return json.loads((ROOT / "data" / "source_data.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def template():
    return (ROOT / "templates" / "explorer.html").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def seed_rows():
    """Load supabase/seed.sql into an in-memory SQLite DB and return the rows as the app would receive them."""
    sql = (ROOT / "supabase" / "seed.sql").read_text(encoding="utf-8")
    for junk in ("begin;", "commit;", "truncate invoice_lines, invoices cascade;"):
        sql = sql.replace(junk, "")
    sql = "\n".join(l for l in sql.split("\n") if not l.startswith("--"))
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(
        "create table invoices(invoice,date,sales_order,customer,main_category,untaxed,gst,total,"
        "scope,scope_note,work_order,work_order_title,sort_order)"
    )
    con.execute(
        "create table invoice_lines(line_id,cat_no,category,sub_no,subcategory,item_no,bom_item,make,"
        "invoice,date,invoice_text,hsn,qty,uom,rate,gst,untaxed,total,check_note,scope,sort_order)"
    )
    con.executescript(sql)
    invoices = [dict(r) for r in con.execute("select * from invoices")]
    lines = [dict(r) for r in con.execute("select * from invoice_lines")]
    return invoices, lines
