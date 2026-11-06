"""supabase/seed.sql and schema.sql must reproduce the source data exactly."""
from pathlib import Path

from core import normalize

ROOT = Path(__file__).resolve().parent.parent


def test_seed_loads_expected_row_counts(seed_rows):
    invoices, lines = seed_rows
    assert (len(invoices), len(lines)) == (18, 133)


def test_seed_roundtrips_to_source_exactly(seed_rows, source):
    data = normalize(*seed_rows)
    assert data["invoices"] == source["invoices"]
    assert data["lines"] == source["lines"]


def test_schema_defines_tables_and_rls():
    sql = (ROOT / "supabase" / "schema.sql").read_text(encoding="utf-8").lower()
    assert "create table if not exists invoices" in sql
    assert "create table if not exists invoice_lines" in sql
    assert "alter table invoices       enable row level security" in sql
    assert "alter table invoice_lines  enable row level security" in sql
    assert "to authenticated" in sql


def test_schema_has_no_write_policies():
    sql = (ROOT / "supabase" / "schema.sql").read_text(encoding="utf-8").lower()
    for verb in ("for insert", "for update", "for delete", "for all"):
        assert verb not in sql


def test_schema_columns_match_seed_columns():
    schema = (ROOT / "supabase" / "schema.sql").read_text(encoding="utf-8")
    seed = (ROOT / "supabase" / "seed.sql").read_text(encoding="utf-8")
    for col in ("check_note", "sort_order", "work_order_title", "scope_note"):
        assert col in schema and col in seed
