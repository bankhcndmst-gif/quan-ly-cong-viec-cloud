import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

from utils import remove_duplicate_and_empty_cols, parse_dates

# =========================================================
# 🔌 KẾT NỐI GOOGLE SHEET (CHUẨN)
# =========================================================
def connect_gsheet():
    creds_dict = dict(st.secrets["gdrive"])

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# =========================================================
# 📥 LOAD TOÀN BỘ SHEET
# =========================================================
@st.cache_data(ttl=60, show_spinner=False)
def load_all_sheets() -> dict:
    try:
        client = connect_gsheet()
        spreadsheet_id = st.secrets["gdrive"]["spreadsheet_id"]

        sh = client.open_by_key(spreadsheet_id)

        all_data = {}

        for ws in sh.worksheets():
            raw = ws.get_all_values()

            if not raw:
                all_data[ws.title] = pd.DataFrame()
                continue

            headers = raw[0]
            rows = raw[1:]

            df = pd.DataFrame(rows, columns=headers)

            df = remove_duplicate_and_empty_cols(df)
            df = parse_dates(df)

            all_data[ws.title] = df

        return all_data

    except Exception as e:
        st.error(f"❌ Không thể tải dữ liệu từ Google Sheet. Lỗi: {e}")
        return {}

# =========================================================
# 💾 GHI ĐÈ SHEET
# =========================================================
def save_raw_sheet(sheet_name: str, df_new: pd.DataFrame):
    client = connect_gsheet()
    spreadsheet_id = st.secrets["gdrive"]["spreadsheet_id"]

    sh = client.open_by_key(spreadsheet_id)
    ws = sh.worksheet(sheet_name)

    df_save = df_new.fillna("")

    ws.clear()
    ws.update([df_save.columns.tolist()] + df_save.values.tolist())
