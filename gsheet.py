import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from utils import normalize_columns, remove_duplicate_and_empty_cols, parse_dates
from config import REQUIRED_SHEETS, DATE_COLS

# =========================================================
# ✅ 1. KẾT NỐI (CACHE RESOURCE)
# =========================================================
@st.cache_resource(show_spinner=False)
def connect_gsheet():
    creds_info = st.secrets["gdrive"]
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client

# =========================================================
# ✅ 2. TẢI 1 SHEET (CACHE DATA) - ĐÃ SỬA LỖI ARROW
# =========================================================
@st.cache_data(show_spinner=False)
def load_sheet_df(sheet_name: str) -> pd.DataFrame:
    try:
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_records()
        
        df = pd.DataFrame(data)

        if df.empty:
            return df

        # Chuẩn hóa tên cột
        df = normalize_columns(df)
        df = remove_duplicate_and_empty_cols(df)

        # ---------------------------------------------------------
        # 🛠️ FIX LỖI CRASH: Ép kiểu String cho các cột dễ gây lỗi
        # ---------------------------------------------------------
        force_str_cols = [
            "DIEN_THOAI", "SDT", "MOBILE", 
            "SO_TAI_KHOAN", "STK", 
            "MA_SO_THUE", "MST", 
            "CCCD", "CMND",
            "ID_NHAN_SU", "ID_DON_VI" # Các cột ID cũng nên là string
        ]
        
        for col in force_str_cols:
            if col in df.columns:
                # Chuyển sang string và xử lý NaN
                df[col] = df[col].astype(str).replace("nan", "")

        # Parse ngày
        df = parse_dates(df, DATE_COLS)

        return df

    except Exception as e:
        # Log lỗi nhưng trả về DataFrame rỗng để app không sập hoàn toàn
        print(f"❌ Lỗi tải sheet '{sheet_name}': {e}")
        return pd.DataFrame()

# =========================================================
# ✅ 3. TẢI TẤT CẢ SHEET
# =========================================================
@st.cache_data(show_spinner=False)
def load_all_sheets() -> dict:
    all_data = {}
    for sheet in REQUIRED_SHEETS:
        df = load_sheet_df(sheet)
        all_data[sheet] = df
    return all_data

# =========================================================
# ✅ 4. GHI DỮ LIỆU
# =========================================================
def save_raw_sheet(sheet_name: str, df: pd.DataFrame):
    try:
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])

        try:
            ws = sh.worksheet(sheet_name)
        except:
            ws = sh.add_worksheet(title=sheet_name, rows=2000, cols=50)

        ws.clear()

        # Chuẩn bị dữ liệu ghi
        df = df.fillna("")
        
        # Chuyển tất cả về string trước khi ghi để tránh lỗi JSON
        df_to_save = df.astype(str)
        
        values = [df.columns.tolist()] + df_to_save.values.tolist()

        ws.update(values)

        # Xóa cache
        load_sheet_df.clear()
        load_all_sheets.clear()

        st.success(f"✅ Đã lưu dữ liệu vào sheet '{sheet_name}'")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Lỗi lưu sheet '{sheet_name}': {e}")
