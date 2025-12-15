import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from utils import normalize_columns, remove_duplicate_and_empty_cols, parse_dates

# =========================================================
# 🔌 KẾT NỐI GOOGLE SHEET (CHUẨN STREAMLIT CLOUD)
# =========================================================

def get_connection():
    """
    Lấy connection Google Sheets theo chuẩn Streamlit Cloud.
    KHÔNG dùng st.secrets["gdrive"].
    """
    return st.connection("gsheets", type=GSheetsConnection)

# =========================================================
# 📥 TẢI TOÀN BỘ SHEET
# =========================================================

@st.cache_data(show_spinner=False, ttl=60)
def load_all_sheets() -> dict:
    """
    Đọc toàn bộ các worksheet trong Google Spreadsheet.
    Trả về: dict {sheet_name: DataFrame}
    """
    all_data = {}

    try:
        conn = get_connection()
        sheet_names = conn.list_worksheets()

        for sheet_name in sheet_names:
            try:
                df = conn.read(
                    worksheet=sheet_name,
                    ttl=0
                )

                # Nếu sheet trống hoàn toàn
                if df.empty and len(df.columns) == 0:
                    all_data[sheet_name] = pd.DataFrame()
                    continue

                # ==== LÀM SẠCH DỮ LIỆU (GIỮ LOGIC CŨ CỦA ANH) ====
                df = remove_duplicate_and_empty_cols(df)
                df = parse_dates(df)

                all_data[sheet_name] = df

            except Exception as e:
                st.warning(f"⚠️ Không đọc được sheet `{sheet_name}`: {e}")

        return all_data

    except Exception as e:
        st.error(f"❌ Không thể tải dữ liệu từ Google Sheet. Lỗi: {e}")
        return {}

# =========================================================
# 💾 GHI ĐÈ TOÀN BỘ SHEET (RAW SAVE)
# =========================================================

def save_raw_sheet(sheet_name: str, df_new: pd.DataFrame):
    """
    Ghi đè toàn bộ DataFrame về worksheet.
    Dùng cho ADMIN + data_editor.
    """
    try:
        conn = get_connection()

        # Chuẩn hoá dữ liệu trước khi ghi
        df_save = df_new.copy()

        for col in df_save.columns:
            # Datetime → string
            if pd.api.types.is_datetime64_any_dtype(df_save[col]):
                df_save[col] = df_save[col].dt.strftime("%Y-%m-%d").fillna("")
            else:
                df_save[col] = df_save[col].fillna("")

        conn.update(
            worksheet=sheet_name,
            data=df_save
        )

    except Exception as e:
        raise RuntimeError(f"Lỗi ghi Sheet `{sheet_name}`: {e}")
