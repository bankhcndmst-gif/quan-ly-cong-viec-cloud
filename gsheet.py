import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from utils import normalize_columns, remove_duplicate_and_empty_cols, parse_dates
from config import REQUIRED_SHEETS, DATE_COLS


# =========================================================
# ✅ 1. KẾT NỐI GOOGLE SHEETS (CÓ CACHE)
# =========================================================
@st.cache_resource(show_spinner=False)
def connect_gsheet():
    """
    Kết nối Google Sheets bằng service account trong st.secrets.
    Cache để tăng tốc độ.
    """
    creds_info = st.secrets["gdrive"]
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client


# =========================================================
# ✅ 2. TẢI 1 SHEET → DATAFRAME (CÓ CACHE)
# =========================================================
@st.cache_data(show_spinner=False)
def load_sheet_df(sheet_name: str) -> pd.DataFrame:
    """
    Tải 1 sheet từ Google Sheets → DataFrame.
    Tự động chuẩn hóa cột, loại bỏ cột rỗng, parse ngày.
    """
    try:
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_records()

        df = pd.DataFrame(data)

        if df.empty:
            return df

        # Chuẩn hóa cột
        df = normalize_columns(df)
        df = remove_duplicate_and_empty_cols(df)

        # Parse ngày
        df = parse_dates(df, DATE_COLS)

        return df

    except Exception as e:
        st.error(f"❌ Lỗi tải sheet '{sheet_name}': {e}")
        return pd.DataFrame()


# =========================================================
# ✅ 3. TẢI TẤT CẢ SHEET CẦN THIẾT
# =========================================================
def load_all_sheets() -> dict:
    """
    Tải toàn bộ sheet trong REQUIRED_SHEETS.
    Trả về dict: {sheet_name: DataFrame}
    """
    all_data = {}
    for sheet in REQUIRED_SHEETS:
        df = load_sheet_df(sheet)
        all_data[sheet] = df
    return all_data


# =========================================================
# ✅ 4. GHI ĐÈ 1 SHEET TỪ DATAFRAME
# =========================================================
def save_raw_sheet(sheet_name: str, df: pd.DataFrame):
    """
    Ghi đè toàn bộ sheet bằng DataFrame.
    Sau khi ghi → clear cache → reload app.
    """
    try:
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])

        # Nếu sheet chưa tồn tại → tạo mới
        try:
            ws = sh.worksheet(sheet_name)
        except:
            ws = sh.add_worksheet(title=sheet_name, rows=2000, cols=50)

        # Xóa sheet cũ
        ws.clear()

        # Chuẩn bị dữ liệu ghi
        df = df.fillna("")
        values = [df.columns.tolist()] + df.values.tolist()

        ws.update(values)

        # Xóa cache
        load_sheet_df.clear()
        load_all_sheets.clear()

        st.success(f"✅ Đã lưu dữ liệu vào sheet '{sheet_name}'")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Lỗi lưu sheet '{sheet_name}': {e}")
