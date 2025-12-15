import streamlit as st
import pandas as pd
from gsheet import load_all_sheets, save_raw_sheet
from utils import (
    format_date_vn,
    get_display_list_multi,
)
from config import LINK_CONFIG_RAW, DATE_COLS


# =========================================================
# ✅ HÀM HIỂN THỊ TAB QUẢN LÝ DỮ LIỆU GỐC
# =========================================================
def render_data_manager_tab():
    st.header("📁 Quản lý dữ liệu gốc")

    # -----------------------------------------------------
    # ✅ Tải toàn bộ dữ liệu
    # -----------------------------------------------------
    all_sheets = load_all_sheets()

    sheet_names = list(all_sheets.keys())
    selected_sheet = st.selectbox("Chọn sheet để quản lý:", sheet_names)

    df = all_sheets[selected_sheet].copy()

    if df.empty:
        st.warning("Sheet này chưa có dữ liệu.")
        return

    st.subheader(f"📄 Dữ liệu trong sheet: **{selected_sheet}**")

    # -----------------------------------------------------
    # ✅ Hiển thị dữ liệu (có cột mô tả nếu có liên kết)
    # -----------------------------------------------------
    df_display = df.copy()

    # Nếu sheet có cấu hình liên kết → tạo cột mô tả
    if selected_sheet in LINK_CONFIG_RAW:
        cfg = LINK_CONFIG_RAW[selected_sheet]

        if "LINK_COLS" in cfg:
            for col, (ref_sheet, ref_id) in cfg["LINK_COLS"].items():
                if col in df_display.columns:
                    ref_df = all_sheets.get(ref_sheet, pd.DataFrame())
                    if not ref_df.empty:
                        df_display[col + "_MO_TA"] = df_display[col].apply(
                            lambda x: lookup_display_safe(x, ref_df, ref_id)
                        )

    st.dataframe(df_display, use_container_width=True)

    st.markdown("---")
    st.subheader("➕ Thêm dòng mới")

    # -----------------------------------------------------
    # ✅ Form thêm dòng mới
    # -----------------------------------------------------
    new_row = {}

    for col in df.columns:
        # Nếu là cột ngày → date_input
        if col in DATE_COLS:
            new_row[col] = st.date_input(f"{col}", value=None)

        # Nếu là cột liên kết → dropdown
        elif selected_sheet in LINK_CONFIG_RAW and \
             "LINK_COLS" in LINK_CONFIG_RAW[selected_sheet] and \
             col in LINK_CONFIG_RAW[selected_sheet]["LINK_COLS"]:

            ref_sheet, ref_id = LINK_CONFIG_RAW[selected_sheet]["LINK_COLS"][col]
            ref_df = all_sheets.get(ref_sheet, pd.DataFrame())

            if not ref_df.empty:
                display_list, mapping = get_display_list_multi(
                    ref_df,
                    id_col=ref_id,
                    cols=LINK_CONFIG_RAW[ref_sheet]["DISPLAY_COLS"],
                    prefix="Chọn..."
                )
                choice = st.selectbox(f"{col}", display_list)
                new_row[col] = mapping.get(choice, "")

            else:
                new_row[col] = st.text_input(f"{col}")

        # Cột thường → text_input
        else:
            new_row[col] = st.text_input(f"{col}")

    # -----------------------------------------------------
    # ✅ Nút lưu dòng mới
    # -----------------------------------------------------
    if st.button("✅ Thêm dòng mới", type="primary"):
        df_new = df.copy()
        df_new.loc[len(df_new)] = new_row
        save_raw_sheet(selected_sheet, df_new)


# =========================================================
# ✅ HÀM LOOKUP AN TOÀN (KHÔNG LỖI KHI TRỐNG)
# =========================================================
def lookup_display_safe(id_value, df_ref, id_col):
    """
    Trả về mô tả từ ID, nếu không có thì trả về ID.
    """
    if not id_value:
        return ""

    row = df_ref[df_ref[id_col] == id_value]
    if row.empty:
        return id_value

    row = row.iloc[0]
    parts = [id_value]

    for c in df_ref.columns:
        if c != id_col:
            val = row[c]
            if isinstance(val, pd.Timestamp):
                val = val.strftime("%d/%m/%Y")
            parts.append(str(val))

    return " | ".join(parts)
