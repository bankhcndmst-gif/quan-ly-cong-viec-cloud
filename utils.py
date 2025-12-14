# =========================================================
# UTILS.PY — CÁC HÀM XỬ LÝ DỮ LIỆU DÙNG CHUNG
# =========================================================

import pandas as pd
from config import DATE_COLS


# ---------------------------------------------------------
# CHUẨN HÓA TÊN CỘT
# ---------------------------------------------------------
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\u00a0", "", regex=False)  # loại bỏ ký tự NBSP
    )
    return df


# ---------------------------------------------------------
# LOẠI BỎ CỘT TRỐNG / TRÙNG
# ---------------------------------------------------------
def remove_duplicate_and_empty_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.loc[:, df.columns != ""]
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    return df


# ---------------------------------------------------------
# CHUYỂN CỘT NGÀY SANG DATETIME
# ---------------------------------------------------------
def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for c in DATE_COLS:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


# ---------------------------------------------------------
# ĐỊNH DẠNG NGÀY dd/mm/yyyy
# ---------------------------------------------------------
def format_date_vn(value):
    if pd.isna(value):
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    return str(value)


# ---------------------------------------------------------
# TẠO DANH SÁCH CHỌN (SELECTBOX)
# ---------------------------------------------------------
def get_unique_list(df: pd.DataFrame, col_name: str, prefix="Tất cả"):
    if df.empty or col_name not in df.columns:
        return [prefix]
    unique_list = df[col_name].dropna().astype(str).unique().tolist()
    return [prefix] + sorted(unique_list)


# ---------------------------------------------------------
# TẠO DANH SÁCH HIỂN THỊ MÔ TẢ (NHIỀU CỘT)
# Dùng cho Selectbox: Người nhận, Dự án, Gói thầu, Hợp đồng...
# ---------------------------------------------------------
def get_display_list_multi(df, id_col, cols, prefix="Chọn"):
    """
    Trả về:
    - list hiển thị dạng mô tả
    - mapping mô tả → ID
    """
    if df.empty or any(c not in df.columns for c in [id_col] + cols):
        return [prefix], {}

    df_temp = df[[id_col] + cols].fillna("")

    # Ghép mô tả: Cột1 | Cột2 | Cột3
    df_temp["DISPLAY"] = df_temp[cols[0]].astype(str)
    for c in cols[1:]:
        df_temp["DISPLAY"] += " | " + df_temp[c].astype(str)

    mapping = dict(zip(df_temp["DISPLAY"], df_temp[id_col]))
    lst = [prefix] + df_temp["DISPLAY"].tolist()

    return lst, mapping


# ---------------------------------------------------------
# TRA CỨU MÔ TẢ TỪ ID
# ---------------------------------------------------------
def lookup_display(id_value, df, id_col, cols):
    """
    Trả về mô tả dạng:
    HO_TEN – CHUC_VU – DIEN_THOAI
    hoặc
    TEN_DU_AN – MO_TA – NGAY_BD
    """
    if not id_value or df.empty or id_col not in df.columns:
        return ""

    row = df[df[id_col].astype(str) == str(id_value)]
    if row.empty:
        return ""

    parts = []
    for c in cols:
        if c in row.columns:
            v = row.iloc[0][c]
            if isinstance(v, pd.Timestamp):
                parts.append(format_date_vn(v))
            else:
                parts.append(str(v))

    return " – ".join(parts)
