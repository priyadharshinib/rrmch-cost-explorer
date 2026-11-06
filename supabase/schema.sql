-- RRMCH Solar Project Cost Explorer: schema (Supabase free tier)
-- Run this first in Supabase > SQL Editor.

create table if not exists invoices (
  invoice            text primary key,
  date               date    not null,
  sales_order        text    default '',
  customer           text    default '',
  main_category      text    default '',
  untaxed            numeric(16,2) not null,
  gst                numeric(16,2) not null,
  total              numeric(16,2) not null,
  scope              text    not null check (scope in ('EPC','Additional')),
  scope_note         text    default '',
  work_order         text    default '',
  work_order_title   text    default '',
  sort_order         int     not null default 0
);

create table if not exists invoice_lines (
  line_id        text primary key,
  cat_no         int     not null,
  category       text    not null,
  sub_no         text    not null,
  subcategory    text    not null,
  item_no        text    not null,
  bom_item       text    not null,
  make           text    default '',
  invoice        text    not null references invoices(invoice) on delete cascade,
  date           date    not null,
  invoice_text   text    default '',
  hsn            text    default '',
  qty            numeric(16,3) not null,
  uom            text    default '',
  rate           numeric(16,2) not null,
  gst            text    default '',
  untaxed        numeric(16,2) not null,
  total          numeric(16,2) not null,
  check_note     text    default '',
  scope          text    not null check (scope in ('EPC','Additional')),
  sort_order     int     not null default 0
);

create index if not exists idx_lines_invoice on invoice_lines(invoice);
create index if not exists idx_lines_cat     on invoice_lines(cat_no, sub_no, item_no);

-- Row Level Security: only logged-in users can read; nobody can write via the API
alter table invoices       enable row level security;
alter table invoice_lines  enable row level security;

drop policy if exists "auth read invoices" on invoices;
drop policy if exists "auth read lines"    on invoice_lines;
create policy "auth read invoices" on invoices       for select to authenticated using (true);
create policy "auth read lines"    on invoice_lines  for select to authenticated using (true);
-- No insert/update/delete policies = writes are blocked for anon/authenticated keys.
-- Edit data from the Supabase Table Editor or SQL editor (service role / dashboard).
