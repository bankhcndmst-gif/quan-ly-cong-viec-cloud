import streamlit as st
import gspread

st.set_page_config(page_title="Test Google Sheet Access")

st.title("🧪 Test truy cập Google Sheet")

def test_access():
    creds = {
        "type": "service_account",
        "project_id": "dummy",
        "private_key_id": "dummy",
        "private_key": st.secrets["gdrive"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["gdrive"]["client_email"],
        "client_id": "dummy",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/dummy"
    }

    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
    return sh.title, [ws.title for ws in sh.worksheets()]

try:
    title, sheets = test_access()
    st.success("✅ TRUY CẬP GOOGLE SHEET THÀNH CÔNG")
    st.write("📄 Tên file:", title)
    st.write("📑 Các sheet:", sheets)
except Exception as e:
    st.error("❌ KHÔNG TRUY CẬP ĐƯỢC GOOGLE SHEET")
    st.exception(e)
