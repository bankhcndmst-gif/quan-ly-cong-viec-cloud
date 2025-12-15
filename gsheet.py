import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from config import REQUIRED_SHEETS
from utils import normalize_columns, remove_duplicate_and_empty_cols, parse_dates 

# =========================================================
# 🔌 KẾT NỐI (Dùng thư viện chuẩn Streamlit)
# =========================================================
def get_conn():
    """Tạo kết nối tới Google Sheet dùng st.connection"""
    return st.connection("gsheets", type=GSheetsConnection)

# =========================================================
# 📥 TẢI DỮ LIỆU (Load All Sheets)
# =========================================================
def load_all_sheets():
    """
    Đọc toàn bộ các sheet được khai báo trong config.py, áp dụng làm sạch dữ liệu.
    """
    conn = get_conn()
    all_data = {}
    
    # Duyệt qua danh sách sheet cần thiết trong Config
    for sheet_name in REQUIRED_SHEETS:
        try:
            df = conn.read(worksheet=sheet_name, ttl=0) # ttl=0: Luôn lấy dữ liệu mới nhất
            
            if df is None: df = pd.DataFrame()
            
            # --- GỌI CÁC HÀM LÀM SẠCH TỪ UTILS.PY ---
            if not df.empty:
                # 1. Chuẩn hóa tên cột (Viết hoa, bỏ dấu, thay khoảng trắng)
                df = normalize_columns(df) 
                
                # 2. Xóa cột trùng tên và cột trống vô nghĩa
                df = remove_duplicate_and_empty_cols(df)

                # 3. Xử lý ngày tháng
                df = parse_dates(df)
            
            all_data[sheet_name] = df
            
        except Exception as e:
            # Nếu Sheet chưa có trong file, tạo bảng rỗng
            all_data[sheet_name] = pd.DataFrame()
            
    return all_data

# =========================================================
# 💾 LƯU DỮ LIỆU
# =========================================================
def save_raw_sheet(sheet_name, df_new):
    """
    Ghi đè dữ liệu vào Sheet
    """
    conn = get_conn()
    try:
        df_save = df_new.copy()
        
        # Chuyển datetime về string 'YYYY-MM-DD' để lưu lên Sheet không bị lỗi
        for col in df_save.columns:
            if pd.api.types.is_datetime64_any_dtype(df_save[col]):
                # Lưu dưới định dạng yyyy-mm-dd
                df_save[col] = df_save[col].dt.strftime('%Y-%m-%d').fillna("")
            df_save[col] = df_save[col].fillna("") # Thay NaN/None bằng chuỗi rỗng
        
        # Hàm update của st-gsheets tự động clear và ghi đè
        conn.update(worksheet=sheet_name, data=df_save)
        return True
        
    except Exception as e:
        raise e
