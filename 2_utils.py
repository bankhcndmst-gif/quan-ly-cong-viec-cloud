import pandas as pd
import streamlit as st
from datetime import datetime


# =========================================================
# ✅ 1. CHUẨN HÓA TÊN CỘT
# =========================================================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Chuẩn hóa tên cột:
    - Loại bỏ khoảng trắng đầu/cuối
    - Thay thế khoảng trắng kép
    - Loại bỏ ký tự lạ (NBSP)
    - Viết hoa đồng nhất
    """
    df.columns = (
        df.columns
        .str.replace("\u00A0", " ", regex=False)  # NBSP
        .str.strip()
        .str.replace("  ", " ")
        .str.upper()
    )
    return df


# =========================================================
# ✅ 2. LOẠI BỎ CỘT TRỐNG & CỘT TRÙNG
# =========================================================
def remove_duplicate_and_empty_cols(df: pd.DataFrame) -> pd.DataFrame:
    """
    - Xóa cột trùng tên
    - Xóa cột toàn giá trị rỗng
    """
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.dropna(axis=1, how="all")
    return df


# =========================================================
# ✅ 3. PARSE CÁC CỘT NGÀY
# =========================================================
def parse_dates(df: pd.DataFrame, date_cols: list) -> pd.DataFrame:
    """
    Parse các cột ngày theo danh sách DATE_COLS.
    Hỗ trợ nhiều định dạng: dd/mm/yyyy, yyyy-mm-dd, mm/dd/yyyy.
    """
    for col in date_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

            def try_parse(x):
                if x in ["", "nan", "None", None]:
                    return None
                for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
                    try:
                        return datetime.strptime(x, fmt)
                    except:
                        pass
                return None

            df[col] = df[col].apply(try_parse)

    return df


# =========================================================
# ✅ 4. FORMAT NGÀY THEO DẠNG VIỆT NAM
# =========================================================
def format_date_vn(value):
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    return str(value)


# =========================================================
# ✅ 5. TẠO DANH SÁCH DROPDOWN CHO FILTER
# =========================================================
def get_unique_list(df: pd.DataFrame, col: str, prefix: str = "") -> list:
    """
    Tạo danh sách unique cho dropdown lọc.
    prefix = "Tất cả" hoặc "Chọn ..."
    """
    if col not in df.columns:
        return [prefix]

    values = df[col].dropna().astype(str).unique().tolist()
    values.sort()

    if prefix:
        return [prefix] + values
    return values


# =========================================================
# ✅ 6. TẠO DANH SÁCH HIỂN THỊ CHO DROPDOWN (ID + MÔ TẢ)
# =========================================================
def get_display_list_multi(df, id_col, cols, prefix=""):
    """
    Tạo danh sách hiển thị dạng:
    "ID | Tên | Mô tả | Ngày"
    Dùng cho dropdown chọn dự án, gói thầu, hợp đồng, văn bản...
    """
    if id_col not in df.columns:
        return [prefix], {}

    display_list = []
    mapping = {}

    for _, row in df.iterrows():
        id_val = str(row[id_col]).strip()
        if not id_val:
            continue

        parts = [id_val]

        for c in cols:
            if c in df.columns:
                val = row[c]
                if isinstance(val, datetime):
                    val = val.strftime("%d/%m/%Y")
                parts.append(str(val))

        text = " | ".join(parts)
        display_list.append(text)
        mapping[text] = id_val

    display_list.sort()

    if prefix:
        display_list = [prefix] + display_list

    return display_list, mapping


# =========================================================
# ✅ 7. LOOKUP ID → MÔ TẢ HIỂN THỊ
# =========================================================
def lookup_display(id_value, df, id_col, cols):
    """
    Từ ID trả về chuỗi mô tả dạng:
    "ID | Tên | Mô tả | Ngày"
    """
    if id_value in ["", None]:
        return ""

    row = df[df[id_col] == id_value]
    if row.empty:
        return id_value

    row = row.iloc[0]

    parts = [id_value]
    for c in cols:
        if c in df.columns:
            val = row[c]
            if isinstance(val, datetime):
                val = val.strftime("%d/%m/%Y")
            parts.append(str(val))

    return " | ".join(parts)
