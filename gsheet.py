# =========================================================
# GSHEET.PY — KẾT NỐI GOOGLE SHEETS + LOAD + SAVE
# =========================================================

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

from config import REQUIRED_SHEETS
from utils import (
    normalize_columns,
    remove_duplicate_and_empty_cols,
    parse_dates
)


# ---------------------------------------------------------
# KẾT NỐI GOOGLE SHEETS
# ---------------------------------------------------------
@st.cache_resource
def connect_gsheet():
    """
    Kết nối Google Sheets bằng service account trong st.secrets.
    """
    creds_dict = dict(st.secrets["gdrive"])

    # Bổ sung các trường bắt buộc nếu thiếu
    creds_dict.setdefault("token_uri", "https://oauth2.googleapis.com/token")
    creds_dict.setdefault("auth_uri", "https://accounts.google.com/o/oauth2/auth")
    creds_dict.setdefault(
        "auth_provider_x509_cert_url",
        "https://www.googleapis.com/oauth2/v1/certs",
    )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)


# ---------------------------------------------------------
# LOAD 1 SHEET
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def load_sheet_df(sheet_name: str) -> pd.DataFrame:
    """
    Tải dữ liệu từ 1 sheet → DataFrame.
    Tự động chuẩn hóa cột, loại cột trùng, parse ngày.
    """
    try:
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)

        values = ws.get_all_values()
        if len(values) < 2:
            return pd.DataFrame()

        df = pd.DataFrame(values[1:], columns=values[0])

        df = normalize_columns(df)
        df = remove_duplicate_and_empty_cols(df)
        df = parse_dates(df)

        # Chuẩn hóa text
        for col in df.columns:
            if col not in df.columns:
                continue
            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str).str.strip()

        return df

    except Exception as e:
        st.error(f"❌ Lỗi tải Sheet '{sheet_name}': {e}")
        return pd.DataFrame()


# ---------------------------------------------------------
# LOAD TẤT CẢ SHEET
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def load_all_sheets():
    """
    Tải toàn bộ sheet trong REQUIRED_SHEETS.
    """
    sheets = {}
    for name in REQUIRED_SHEETS:
        sheets[name] = load_sheet_df(name)
    return sheets


# ---------------------------------------------------------
# GHI ĐÈ 1 SHEET
# ---------------------------------------------------------
def save_raw_sheet(sheet_name: str, edited_df: pd.DataFrame):
    """
    Ghi đè toàn bộ sheet bằng DataFrame mới.
    """
    try:
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)

        ws.clear()

        data_to_write = [edited_df.columns.tolist()] + edited_df.fillna("").values.tolist()
        ws.append_rows(data_to_write, value_input_option="USER_ENTERED")

        st.success(f"✅ Đã lưu Sheet '{sheet_name}' thành công!")

        # Xóa cache để load lại dữ liệu mới
        st.cache_data.clear()
        st.rerun()

    except Exception as e:
        st.error(f"❌ Lỗi khi ghi vào Sheet '{sheet_name}': {e}")
