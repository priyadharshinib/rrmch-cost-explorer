# RRMCH Project Cost Explorer (Streamlit + Supabase)

Login-protected version of the RRMCH 984.5 kWp Project Cost Explorer. The design is the original
HTML (`templates/explorer.html`); the data comes from Supabase. Free tier only.

## Layout
```
app.py                  Streamlit UI (login + report)
core.py                 data logic (fetch, normalize, inject into template)
templates/explorer.html original report, with a __DATA__ placeholder
supabase/schema.sql     tables + Row Level Security
supabase/seed.sql       the 18 invoices / 133 lines
scripts/create_user.py  add / list / delete login users
tests/                  pytest suite (run with: pytest)
data/source_data.json   original extract (backup)
```

## 1. Supabase
1. New project (free plan).
2. SQL Editor: run `supabase/schema.sql`, then `supabase/seed.sql`.
3. Project Settings > API: copy the **Project URL**, the **anon** key and the **service_role** key.

## 2. Create login users
Users do NOT appear in Table Editor. They live under **Authentication > Users**.

Option A, dashboard: Authentication > Users > Add user > Create new user, tick **Auto Confirm User**.

Option B, script (from this folder):
```
cp .env.example .env            # fill SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
pip install -r requirements.txt
python scripts/create_user.py add you@example.com "YourPassword#123"
python scripts/create_user.py list
```
You choose the email and password. The service_role key stays in `.env` only (git-ignored).

## 3. Run the app
```
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # URL + anon key
streamlit run app.py
```

## 4. Run the tests
```
pip install -r requirements-dev.txt
pytest
```
No Supabase connection or keys are needed: tests check data integrity, the seed/schema SQL,
the data logic, and the login flow with a fake Supabase.

## Notes
- Supabase free projects pause after ~1 week idle; open the dashboard to resume.
- Data is cached 5 minutes per user.
