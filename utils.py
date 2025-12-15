import pandas as pd
import streamlit as st
from datetime import datetime

# =========================================================
# 🛠️ CÁC HÀM XỬ LÝ DỮ LIỆU BỔ TRỢ (UTILITIES)
# =========================================================

def format_date_vn(date_obj):
    """Chuyển đổi datetime sang string dd/mm/yyyy an toàn."""
    if pd.isnull(date_obj):
        return ""
    try:
        # Nếu là chuỗi, thử parse
        if isinstance(date_obj, str):
            # Nếu chuỗi rỗng
            if not date_obj.strip(): return ""
            # Thử convert sang datetime rồi format lại
            temp = pd.to_datetime(date_obj, dayfirst=True, errors='coerce')
            if pd.notnull(temp):
                return temp.strftime("%d/%m/%Y")
            return date_obj # Trả về nguyên gốc nếu không parse được
            
        # Nếu là datetime object
        if hasattr(date_obj, "strftime"):
            return date_obj.strftime("%d/%m/%Y")
            
        return str(date_obj)
    except:
        return ""

def get_unique_list(df, col_name):
    """Lấy danh sách giá trị duy nhất (để làm filter)."""
    if df.empty or col_name not in df.columns:
        return []
    return df[col_name].dropna().unique().tolist()

def lookup_display(id_val, ref_df, id_col, display_cols):
    """Tìm ID và trả về Tên hiển thị (Ví dụ: ID001 -> Nguyễn Văn A)."""
    if pd.isnull(id_val) or str(id_val).strip() == "":
        return ""
        
    if ref_df.empty or id_col not in ref_df.columns:
        return str(id_val)
        
    # Tìm dòng có ID khớp
    # Chuyển cả 2 về string để so sánh cho chắc ăn
    row = ref_df[ref_df[id_col].astype(str) == str(id_val)]
    
    if row.empty:
        return str(id_val)
    
    # Ghép các cột hiển thị (VD: HOTEN + CHUCVU)
    displays = []
    for col in display_cols:
        if col in row.columns:
            val = row.iloc[0][col]
            if pd.notnull(val) and str(val).strip():
                 displays.append(str(val))
    
    return " - ".join(displays) if displays else str(id_val)

def get_display_list_multi(df, id_col, cols, prefix="Chọn..."):
    """
    Tạo danh sách hiển thị cho Dropdown.
    Trả về: (list_hien_thi, dictionary_map)
    """
    if df.empty:
        return [prefix], {}

    display_list = [prefix]
    mapping = {} # Key: Tên hiển thị -> Value: ID thực

    for _, row in df.iterrows():
        # Lấy ID
        id_val = row.get(id_col, "")
        if pd.isnull(id_val) or str(id_val).strip() == "":
            continue # Bỏ qua dòng không có ID
            
        # Tạo chuỗi hiển thị: "Tên việc (Hạn chót)"
        parts = []
        for col in cols:
            if col in df.columns:
                val = row[col]
                
                # 🛠️ FIX LỖI NAT TYPE Ở ĐÂY:
                # Kiểm tra xem có phải cột ngày tháng không
                if pd.api.types.is_datetime64_any_dtype(df[col]) or isinstance(val, (pd.Timestamp, datetime)):
                    val = format_date_vn(val) # Dùng hàm an toàn ở trên
                
                if pd.notnull(val) and str(val).strip() != "":
                    parts.append(str(val))
        
        display_text = " - ".join(parts) if parts else str(id_val)
        
        # Lưu vào map
        display_list.append(display_text)
        mapping[display_text] = id_val

    return display_list, mapping
