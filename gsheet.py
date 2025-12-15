import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from config import REQUIRED_SHEETS

# =========================================================
# 🔌 KẾT NỐI (Dùng thư viện chuẩn Streamlit)
# =========================================================
def get_conn():
    """Tạo kết nối tới Google Sheet dùng st.connection"""
    return st.connection("gsheets", type=GSheetsConnection)

# =========================================================
# 🛠️ CÁC HÀM HỖ TRỢ (Thay thế utils.py)
# =========================================================
def clean_dataframe(df):
    """Làm sạch DataFrame: Xóa cột trống, chuẩn hóa ngày"""
    if df.empty: return df
    
    # 1. Chuẩn hóa tên cột (Viết hoa, xóa khoảng trắng)
    df.columns = df.columns.str.strip().str.upper()
    
    # 2. Xóa các cột không có tên (Cột trống trong Excel)
    df = df.loc[:, ~df.columns.str.contains('^UNNAMED', case=False)]
    
    # 3. Ép kiểu datetime cho các cột ngày tháng (dựa trên tên cột)
    for col in df.columns:
        # Nếu tên cột có chứa chữ NGAY, THOI_GIAN, HAN_CHOT...
        if any(x in col for x in ["NGAY", "TIME", "HAN", "DATE"]):
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except:
                pass
    return df

# =========================================================
# 📥 TẢI DỮ LIỆU (Load All Sheets)
# =========================================================
def load_all_sheets():
    """
    Đọc toàn bộ các sheet được khai báo trong config.py
    """
    conn = get_conn()
    all_data = {}
    
    # Duyệt qua danh sách sheet cần thiết trong Config
    for sheet_name in REQUIRED_SHEETS:
        try:
            # ttl=0: Luôn lấy dữ liệu mới nhất
            df = conn.read(worksheet=sheet_name, ttl=0)
            
            # Nếu đọc về là None hoặc rỗng
            if df is None: df = pd.DataFrame()
            
            # Làm sạch dữ liệu
            df = clean_dataframe(df)
            
            all_data[sheet_name] = df
            
        except Exception as e:
            # Nếu Sheet chưa có trong file, tạo bảng rỗng
            all_data[sheet_name] = pd.DataFrame()
            
    return all_data

# =========================================================
# 💾 LƯU DỮ LIỆU (Save Raw Sheet)
# =========================================================
def save_raw_sheet(sheet_name, df_new):
    """
    Ghi đè dữ liệu vào Sheet
    """
    conn = get_conn()
    try:
        # Chuẩn bị dữ liệu trước khi lưu (tránh lỗi JSON)
        df_save = df_new.copy()
        
        # Chuyển datetime về string để lưu lên Sheet không bị lỗi
        for col in df_save.columns:
            if pd.api.types.is_datetime64_any_dtype(df_save[col]):
                df_save[col] = df_save[col].dt.strftime('%Y-%m-%d').fillna("")
        
        # Hàm update của st-gsheets tự động clear và ghi đè
        conn.update(worksheet=sheet_name, data=df_save)
        return True
        
    except Exception as e:
        st.error(f"Lỗi khi lưu '{sheet_name}': {e}")
        raise e
