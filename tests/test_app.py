"""UI flow tests using Streamlit's AppTest. Supabase is replaced by a fake, so no network or keys are needed."""
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("streamlit.testing.v1")
from streamlit.proto.TextInput_pb2 import TextInput  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parent.parent / "app.py")
GOOD = ("user@example.com", "right-password")


class FakeAuth:
    def sign_in_with_password(self, creds):
        if (creds["email"], creds["password"]) != GOOD:
            raise Exception("Invalid login credentials")
        return SimpleNamespace(user=SimpleNamespace(email=creds["email"]))

    def sign_out(self):
        pass


class FakeQuery:
    def __init__(self, rows):
        self.rows, self.lo, self.hi = rows, 0, None

    def select(self, *_): return self
    def order(self, *_): return self
    def range(self, lo, hi):
        self.lo, self.hi = lo, hi
        return self
    def execute(self):
        return SimpleNamespace(data=self.rows[self.lo : self.hi + 1])


class FakeClient:
    auth = FakeAuth()

    def table(self, name):
        return FakeQuery([])  # empty tables are enough for the UI flow


@pytest.fixture
def app(monkeypatch):
    import streamlit as st

    st.cache_data.clear()
    monkeypatch.setattr("supabase.create_client", lambda *a, **k: FakeClient())
    monkeypatch.setattr("streamlit.components.v1.html", lambda *a, **k: None)
    at = AppTest.from_file(APP, default_timeout=30)
    at.secrets["SUPABASE_URL"] = "https://example.supabase.co"
    at.secrets["SUPABASE_ANON_KEY"] = "anon"
    return at.run()


def submit(at, email, password):
    at.text_input[0].set_value(email)
    at.text_input[1].set_value(password)
    at.button[0].click()
    return at.run()


def test_login_screen_shows_title_and_fields(app):
    assert not app.exception
    html = " ".join(m.value for m in app.markdown)
    assert "Solar EPC · Project Cost Explorer" in html
    assert "RRMCH Plant" in html
    assert 'alt="Asase Energy"' in html          # logo kept on the login page
    assert len(app.text_input) == 2
    assert app.text_input[1].label == "Password"
    assert app.text_input[1].proto.type == TextInput.PASSWORD   # masked input


def test_wrong_password_shows_error_and_stays_on_login(app):
    at = submit(app, GOOD[0], "wrong")
    assert any("Invalid email or password" in e.value for e in at.error)
    assert "sb" not in at.session_state


def test_correct_login_opens_report(app):
    at = submit(app, *GOOD)
    assert not at.exception
    assert "sb" in at.session_state
    assert at.session_state["user_email"] == GOOD[0]
    assert any(GOOD[0] in m.value for m in at.markdown)   # email is shown inside the avatar menu


def test_sign_out_returns_to_login(app):
    at = submit(app, *GOOD)
    next(b for b in at.button if b.label == "Sign out").click()
    at.run()
    assert "sb" not in at.session_state
    assert len(at.text_input) == 2
