import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from config import REQUIRED_SHEETS

# =========================================================
# 🔌 KẾT NỐI (Dùng thư viện chuẩn Streamlit)
# =========================================================
def get_conn():
    return st.connection("gsheets", type=GSheetsConnection)

# =========================================================
# 📥 TẢI DỮ LIỆU (Load All Sheets)
# =========================================================
def load_all_sheets():
    conn = get_conn()
    all_data = {}
    
    for sheet_name in REQUIRED_SHEETS:
        try:
            # ttl=0: Luôn lấy dữ liệu mới nhất
            df = conn.read(worksheet=sheet_name, ttl=0)
            
            if df is None: df = pd.DataFrame()
            
            # --- XỬ LÝ LÀM SẠCH DỮ LIỆU ---
            if not df.empty:
                # 1. Chuẩn hóa tên cột (Viết hoa, xóa khoảng trắng)
                df.columns = df.columns.str.strip().str.upper()
                
                # 2. Xóa các cột tự sinh ra do lỗi (Unnamed)
                df = df.loc[:, ~df.columns.str.contains('^UNNAMED', case=False)]
                
                # 3. Ép kiểu chuỗi cho các cột quan trọng để tránh lỗi tìm kiếm
                for col in ["GMAIL", "PASSWORD", "MAT_KHAU", "HO_TEN", "VAI_TRO"]:
                    if col in df.columns:
                        df[col] = df[col].astype(str)

            all_data[sheet_name] = df
            
        except Exception as e:
            all_data[sheet_name] = pd.DataFrame()
            
    return all_data

# =========================================================
# 💾 LƯU DỮ LIỆU
# =========================================================
def save_raw_sheet(sheet_name, df_new):
    conn = get_conn()
    try:
        df_save = df_new.copy()
        # Chuyển ngày tháng về string
        for col in df_save.columns:
            if pd.api.types.is_datetime64_any_dtype(df_save[col]):
                df_save[col] = df_save[col].dt.strftime('%Y-%m-%d').fillna("")
            df_save[col] = df_save[col].fillna("")
        
        conn.update(worksheet=sheet_name, data=df_save)
        return True
    except Exception as e:
        raise e
