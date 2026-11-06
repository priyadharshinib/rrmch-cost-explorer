"""Pure data logic for the RRMCH Cost Explorer (no Streamlit import, easy to test)."""
import json
from typing import Any

INVOICE_NUM = ("untaxed", "gst", "total")   # gst is an amount here
LINE_NUM = ("untaxed", "total", "qty", "rate")  # gst is text like "5%" here, keep as is
PAGE_SIZE = 1000


def fetch_all(client: Any, table: str, order: str, page_size: int = PAGE_SIZE) -> list[dict]:
    """Read a whole table from Supabase, paging past the 1000-row API limit."""
    rows: list[dict] = []
    start = 0
    while True:
        res = (
            client.table(table)
            .select("*")
            .order(order)
            .range(start, start + page_size - 1)
            .execute()
        )
        rows += res.data
        if len(res.data) < page_size:
            return rows
        start += page_size


def normalize(invoices: list[dict], lines: list[dict]) -> dict:
    """Turn database rows into the exact DATA shape the HTML report expects."""
    invoices = [dict(r) for r in invoices]
    lines = [dict(r) for r in lines]
    for recs, fields in ((invoices, INVOICE_NUM), (lines, LINE_NUM)):
        for rec in recs:
            for k in fields:
                if k in rec and rec[k] is not None:
                    rec[k] = float(rec[k])
            if rec.get("date") is not None:
                rec["date"] = str(rec["date"])[:10]
    for rec in lines:
        rec["check"] = rec.pop("check_note", "") or ""
    invoices.sort(key=lambda r: r.get("sort_order", 0))
    lines.sort(key=lambda r: r.get("sort_order", 0))
    for rec in invoices + lines:
        rec.pop("sort_order", None)
    return {"lines": lines, "invoices": invoices}


def load_report_data(client: Any) -> dict:
    return normalize(
        fetch_all(client, "invoices", "sort_order"),
        fetch_all(client, "invoice_lines", "sort_order"),
    )


def build_html(template: str, data: dict) -> str:
    """Inject the data into the HTML template. '</' is escaped so data can never close the script tag."""
    if template.count("__DATA__") != 1:
        raise ValueError("template must contain exactly one __DATA__ placeholder")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return template.replace("__DATA__", payload)


def image_data_uri(path, mime: str = "image/png") -> str:
    """Read an image file and return a data: URI (so it can be used in inline HTML)."""
    import base64
    from pathlib import Path

    return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode("ascii")


def user_initial(email: str) -> str:
    """One capital letter for the avatar icon."""
    for ch in (email or "").strip():
        if ch.isalnum():
            return ch.upper()
    return "U"
