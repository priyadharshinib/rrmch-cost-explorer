"""Solar EPC · Project Cost Explorer (RRMCH Plant): Streamlit + Supabase, login required."""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client

from core import build_html, image_data_uri, load_report_data, user_initial

BASE = Path(__file__).parent
TEMPLATE = BASE / "templates" / "explorer.html"
LOGO = BASE / "assets" / "asase_logo.png"
APP_TITLE = "Solar EPC · Project Cost Explorer"

st.set_page_config(
    page_title=f"{APP_TITLE} | Asase Energy",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_CSS = """
<style>
  #MainMenu, footer, [data-testid="stAppDeployButton"], .stDeployButton {display:none !important;}
  [data-testid="stHeader"] {background:transparent;}
  .stApp {background:#EEF1F3;}
</style>
"""

LOGIN_CSS = """
<style>
  /* centred, narrow card that works from phone to desktop (no column tricks) */
  .block-container {max-width:460px !important; margin:0 auto; padding:3.5rem 1rem 2rem !important;}
  .login-brand {background:#fff; border:1px solid #D6DCE0; border-bottom:0; border-radius:14px 14px 0 0;
                padding:22px 24px 16px; text-align:center; position:relative;}
  .login-brand img {width:min(300px,86%); height:auto; display:inline-block;}
  .login-brand::after {content:""; position:absolute; left:0; right:0; bottom:0; height:4px;
                       background:linear-gradient(90deg,#2B8CBF 0%,#2B8CBF 55%,#92C941 100%);}
  .login-head {background:#fff; border:1px solid #D6DCE0; border-top:0; border-bottom:0; padding:22px 24px 4px; text-align:center;}
  .login-title {font-size:clamp(20px,5.2vw,26px); font-weight:600; line-height:1.25; margin:0; color:#13232F;}
  .login-plant {color:#1F5F84; font-weight:600; margin-top:6px; letter-spacing:.02em;}
  .login-sub {color:#5C6B76; font-size:14px; margin-top:4px;}
  [data-testid="stForm"] {background:#fff; border:1px solid #D6DCE0 !important; border-top:0 !important;
                          border-radius:0 0 14px 14px !important; padding:8px 24px 22px !important;
                          box-shadow:0 10px 30px rgba(19,35,47,.08);}
  [data-testid="stForm"] button[kind="secondaryFormSubmit"],
  [data-testid="stForm"] button[kind="primaryFormSubmit"] {background:#2B8CBF; color:#fff; border:0; font-weight:600; min-height:44px;}
  [data-testid="stForm"] button:hover {background:#1F79AA; color:#fff;}
  .login-foot {text-align:center; color:#5C6B76; font-size:12px; margin-top:14px;}
</style>
"""

REPORT_CSS = """
<style>
  /* the report owns the whole page: no Streamlit header, no padding, no gaps */
  [data-testid="stHeader"] {display:none !important;}
  .block-container {max-width:100% !important; padding:0 !important;}
  [data-testid="stVerticalBlock"] {gap:0 !important;}
  /* user avatar: round icon pinned to the top-right corner of the report header,
     lined up with the right edge of the content (1560px = the report's max width) */
  [data-testid="stPopover"] {position:fixed; top:16px; right:max(16px, calc((100vw - 1560px)/2 + 32px));
      z-index:1000; width:auto; margin:0;}
  [data-testid="stPopover"] button {
      width:40px; height:40px; min-height:40px; padding:0; border-radius:50%;
      background:#2B8CBF; color:#fff; border:2px solid #fff; font-weight:700; font-size:16px;
      box-shadow:0 2px 8px rgba(19,35,47,.25);}
  [data-testid="stPopover"] button:hover {background:#1F79AA; color:#fff;}
  [data-testid="stPopover"] button svg, [data-testid="stPopover"] button [data-testid="stIconMaterial"] {display:none;}
  .who-label {font-size:12px; color:#5C6B76; margin:0;}
  .who-email {font-weight:600; word-break:break-all; margin:0 0 .5rem;}
</style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)


def login_view():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
    st.markdown(
        f'<div class="login-brand"><img src="{image_data_uri(LOGO)}" alt="Asase Energy"></div>'
        f'<div class="login-head">'
        f'<div class="login-title">{APP_TITLE}</div>'
        f'<div class="login-plant">RRMCH Plant</div>'
        f'<div class="login-sub">Sign in to view the report</div></div>',
        unsafe_allow_html=True,
    )
    with st.form("login"):
        email = st.text_input("Email", placeholder="you@company.com")
        password = st.text_input("Password", type="password")
        ok = st.form_submit_button("Sign in", use_container_width=True)
    st.markdown('<div class="login-foot">Asase Energy · authorised users only</div>', unsafe_allow_html=True)
    if ok:
        try:
            # one client per browser session so users never share a token
            client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])
            res = client.auth.sign_in_with_password({"email": email.strip(), "password": password})
            st.session_state["sb"] = client
            st.session_state["user_email"] = res.user.email
        except Exception:
            st.error("Invalid email or password.")
            return
        st.rerun()


@st.cache_data(ttl=300, show_spinner="Loading data…")
def load_data(_client, user_email: str):
    # user_email is part of the cache key so each user gets their own cached copy
    return load_report_data(_client)


def report_view():
    st.markdown(REPORT_CSS, unsafe_allow_html=True)
    client = st.session_state["sb"]
    email = st.session_state["user_email"]

    with st.popover(user_initial(email)):
        st.markdown('<p class="who-label">Signed in as</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="who-email">{email}</p>', unsafe_allow_html=True)
        if st.button("Sign out", use_container_width=True):
            try:
                client.auth.sign_out()
            finally:
                st.session_state.clear()
            st.rerun()

    try:
        data = load_data(client, email)
    except Exception:
        st.session_state.clear()
        st.error("Could not load data. Your session may have expired, please sign in again.")
        st.stop()
    html = build_html(TEMPLATE.read_text(encoding="utf-8"), data)
    components.html(html, height=900, scrolling=True)


if "sb" in st.session_state:
    report_view()
else:
    login_view()
