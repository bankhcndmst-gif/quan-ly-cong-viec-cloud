import streamlit as st
import gspread

st.title("TEST TRUY CẬP GOOGLE SHEET")

def test_access():
    creds = dict(st.secrets["gdrive"])
    spreadsheet_id = creds.pop("spreadsheet_id")

    # đảm bảo đủ field bắt buộc
    if "token_uri" not in creds:
        creds["token_uri"] = "https://oauth2.googleapis.com/token"

    gc = gspread.service_account_from_dict(creds)

    # 👉 DÒNG QUYẾT ĐỊNH
    sh = gc.open_by_key(spreadsheet_id)

    return [ws.title for ws in sh.worksheets()]

try:
    sheet_names = test_access()
    st.success("✅ TRUY CẬP GOOGLE SHEET THÀNH CÔNG")
    st.write("Danh sách tab:")
    st.write(sheet_names)

except Exception as e:
    st.error("❌ KHÔNG TRUY CẬP ĐƯỢC GOOGLE SHEET")
    st.exception(e)
