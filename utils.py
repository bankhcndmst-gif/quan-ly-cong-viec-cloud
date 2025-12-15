import pandas as pd
import streamlit as st
from datetime import datetime
import re

# =========================================================
# 🧹 PHẦN 1: CÁC HÀM XỬ LÝ DỮ LIỆU (CHO GSHEET.PY)
# =========================================================

def normalize_columns(df):
    """Chuẩn hóa tên cột: Viết hoa, bỏ dấu, thay khoảng trắng bằng _"""
    if df.empty: return df
    
    new_cols = []
    for col in df.columns:
        s = str(col).strip().upper()
        # Bỏ dấu tiếng Việt
        s = re.sub(r'[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]', 'A', s)
        s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
        s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
        s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
        s = re.sub(r'[ÙÚỤỦŨƯỪỨỰỬỮ]', 'U', s)
        s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
        s = re.sub(r'[Đ]', 'D', s)
        # Thay ký tự đặc biệt bằng _
        s = re.sub(r'[^A-Z0-9_]', '_', s)
        # Xóa _ thừa
        s = re.sub(r'_+', '_', s)
        s = s.strip('_')
        new_cols.append(s)
    
    df.columns = new_cols
    return df

def remove_duplicate_and_empty_cols(df):
    """Xóa cột trùng tên và cột Unnamed"""
    if df.empty: return df
    
    df = df.loc[:, ~df.columns.duplicated()]
    cols_to_keep = [c for c in df.columns if "UNNAMED" not in str(c).upper() and str(c).strip() != ""]
    return df[cols_to_keep]

def parse_dates(df, date_cols=None):
    """Chuyển đổi các cột ngày tháng sang datetime object"""
    if df.empty: return df
    
    if not date_cols:
        date_cols = [c for c in df.columns if any(x in c for x in ['NGAY', 'HAN', 'THOI_GIAN'])]
    
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
    return df

# =========================================================
# 🎨 PHẦN 2: CÁC HÀM HIỂN THỊ & FORMAT (CHO GIAO DIỆN)
# =========================================================

def format_date_vn(date_obj):
    """Chuyển đổi datetime sang string dd/mm/yyyy an toàn."""
    if pd.isnull(date_obj):
        return ""
    try:
        if hasattr(date_obj, "strftime"):
            return date_obj.strftime("%d/%m/%Y")
            
        if isinstance(date_obj, str):
            if not date_obj.strip(): return ""
            temp = pd.to_datetime(date_obj, dayfirst=True, errors='coerce')
            if pd.notnull(temp):
                return temp.strftime("%d/%m/%Y")
            return date_obj
            
        return str(date_obj)
    except:
        return ""

def lookup_display(id_val, ref_df, id_col, display_cols):
    """Tìm ID và trả về Tên hiển thị."""
    if pd.isnull(id_val) or str(id_val).strip() == "":
        return ""
        
    if ref_df.empty or id_col not in ref_df.columns:
        return str(id_val)
        
    row = ref_df[ref_df[id_col].astype(str) == str(id_val)]
    
    if row.empty:
        return str(id_val)
    
    displays = []
    for col in display_cols:
        if col in row.columns:
            val = row.iloc[0][col]
            if pd.notnull(val) and str(val).strip():
                 displays.append(str(val))
    
    return " - ".join(displays) if displays else str(id_val)

def get_display_list_multi(df, id_col, cols, prefix="Chọn..."):
    """
    Tạo danh sách hiển thị cho Dropdown: 'ID | Tên - Mô tả' và map ID ngược lại.
    """
    if df.empty or id_col not in df.columns:
        return [prefix], {prefix: ""}

    display_list = [prefix]
    mapping = {prefix: ""}

    valid_cols = [c for c in cols if c in df.columns]

    for _, row in df.iterrows():
        id_val = row.get(id_col, "")
        if pd.isnull(id_val) or str(id_val).strip() == "":
            continue
            
        parts = []
        for col in valid_cols:
            val = row[col]
            
            if isinstance(val, (pd.Timestamp, datetime)):
                val = format_date_vn(val)
            
            if pd.notnull(val) and str(val).strip() != "":
                parts.append(str(val))
        
        display_text = f"{id_val} | " + " - ".join(parts) if parts else str(id_val)
        
        display_list.append(display_text)
        mapping[display_text] = id_val

    return display_list, mapping
