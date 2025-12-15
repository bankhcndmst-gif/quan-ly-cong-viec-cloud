import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from utils import normalize_columns, remove_duplicate_and_empty_cols, parse_dates

# =========================================================
# 🔌 KẾT NỐI GOOGLE SHEET
# =========================================================
def connect_gsheet():
    """Kết nối và trả về client gspread"""
    # Lấy thông tin từ secrets.toml
    secrets = st.secrets["gdrive"]
    
    # Tạo scope (quyền truy cập)
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Tạo credentials từ thông tin trong secrets
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secrets, scope)
    client = gspread.authorize(creds)
    return client

# =========================================================
# 📥 TẢI DỮ LIỆU (Load All Sheets)
# =========================================================
@st.cache_data(show_spinner=False, ttl=60) # Tự làm mới sau 60s
def load_all_sheets() -> dict:
    """
    Đọc toàn bộ các sheet trong file Google Sheet.
    Trả về: Dictionary {'TEN_SHEET': DataFrame, ...}
    """
    try:
        client = connect_gsheet()
        spreadsheet_id = st.secrets["gdrive"]["spreadsheet_id"]
        sh = client.open_by_key(spreadsheet_id)
        
        all_data = {}
        worksheets = sh.worksheets()
        
        for ws in worksheets:
            sheet_name = ws.title
            
            # 1. Lấy toàn bộ dữ liệu thô (List of Lists)
            # Cách này an toàn hơn dùng pd.read_csv
            raw_data = ws.get_all_values()
            
            if not raw_data:
                # Nếu sheet trắng tinh, tạo DataFrame rỗng
                all_data[sheet_name] = pd.DataFrame()
                continue
                
            # 2. Tách Tiêu đề (Dòng 1) và Dữ liệu (Dòng 2 trở đi)
            headers = raw_data[0] # Luôn lấy dòng đầu làm tiêu đề
            rows = raw_data[1:] if len(raw_data) > 1 else []
            
            # 3. Tạo DataFrame
            df = pd.DataFrame(rows, columns=headers)
            
            # 4. Làm sạch dữ liệu (Dùng các hàm từ utils.py)
            # - Chuẩn hóa tên cột (Viết hoa, bỏ dấu cách thừa)
            # df = normalize_columns(df) -> Tạm tắt để tôn trọng tên cột gốc của bạn
            
            # - Xóa cột trống vô nghĩa
            df = remove_duplicate_and_empty_cols(df)
            
            # - Xử lý ngày tháng (để tránh lỗi NaT/ValueError)
            df = parse_dates(df)
            
            all_data[sheet_name] = df
            
        return all_data

    except Exception as e:
        # Nếu lỗi, in ra console để debug nhưng không làm sập app
        print(f"❌ Lỗi tải dữ liệu: {e}")
        st.error(f"Không thể tải dữ liệu từ Google Sheet. Lỗi: {e}")
        return {}

# =========================================================
# 💾 LƯU DỮ LIỆU (Save Raw Sheet)
# =========================================================
def save_raw_sheet(sheet_name, df_new):
    """
    Ghi đè DataFrame mới vào Google Sheet.
    """
    try:
        client = connect_gsheet()
        spreadsheet_id = st.secrets["gdrive"]["spreadsheet_id"]
        sh = client.open_by_key(spreadsheet_id)
        ws = sh.worksheet(sheet_name)
        
        # 1. Xử lý dữ liệu trước khi lưu
        # Chuyển đổi datetime thành string để Google Sheet không bị lỗi format
        df_save = df_new.copy()
        for col in df_save.columns:
            # Nếu là ngày tháng, chuyển thành chuỗi yyyy-mm-dd
            if pd.api.types.is_datetime64_any_dtype(df_save[col]):
                df_save[col] = df_save[col].dt.strftime('%Y-%m-%d').fillna("")
            # Thay thế NaN/None bằng chuỗi rỗng
            df_save[col] = df_save[col].fillna("")
            
        # 2. Cập nhật dữ liệu
        # clear() xóa cũ, update() ghi mới
        ws.clear()
        
        # Chuẩn bị list of lists: [ [Header], [Row1], [Row2]... ]
        data_to_write = [df_save.columns.tolist()] + df_save.values.tolist()
        ws.update(data_to_write)
        
        return True
    except Exception as e:
        raise e
