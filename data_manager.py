# =========================================================
# DATA_MANAGER.PY — TAB QUẢN LÝ DỮ LIỆU GỐC (BẢN NÂNG CẤP)
# =========================================================

import streamlit as st
from utils import lookup_display, get_display_list_multi, format_date_vn
from gsheet import save_raw_sheet
from config import LINK_CONFIG_RAW
import pandas as pd


# ---------------------------------------------------------
# FORM THÊM DÒNG MỚI (CÓ DROPDOWN ID + MÔ TẢ)
# ---------------------------------------------------------
def render_add_row_form(sheet_name, df_goc, all_sheets):
    st.subheader("➕ Thêm dòng mới")

    new_row = {}

    # Lấy danh sách cột
    cols = df_goc.columns.tolist()

    with st.form(f"add_row_form_{sheet_name}"):
        for col in cols:
            # Nếu cột có liên kết ID → tạo dropdown
            if sheet_name in LINK_CONFIG_RAW and col in LINK_CONFIG_RAW[sheet_name]:
                ref_sheet, id_col, desc_cols = LINK_CONFIG_RAW[sheet_name][col]
                df_ref = all_sheets[ref_sheet]

                list_display, map_display = get_display_list_multi(
                    df_ref, id_col, desc_cols, prefix="Chọn"
                )

                selected_display = st.selectbox(f"{col} (ID)", list_display)
                selected_id = map_display.get(selected_display, "")

                new_row[col] = selected_id

                # Hiển thị mô tả ngay bên dưới
                if selected_id:
                    st.caption("➡ " + lookup_display(selected_id, df_ref, id_col, desc_cols))

            # Nếu là cột ngày
            elif "NGAY" in col.upper():
                new_date = st.date_input(f"{col}", None)
                new_row[col] = new_date.strftime("%Y-%m-%d") if new_date else ""

            # Cột thường
            else:
                new_row[col] = st.text_input(f"{col}")

        submitted = st.form_submit_button("✅ Thêm dòng mới")

        if submitted:
            df_new = pd.DataFrame([new_row])
            df_final = pd.concat([df_goc, df_new], ignore_index=True)
            save_raw_sheet(sheet_name, df_final)
            st.success("✅ Đã thêm dòng mới!")
            st.rerun()


# ---------------------------------------------------------
# TAB QUẢN LÝ DỮ LIỆU GỐC (BẢN NÂNG CẤP)
# ---------------------------------------------------------
def render_data_tab(all_sheets):
    st.header("📁 Quản lý dữ liệu gốc (Bản nâng cấp)")

    st.warning(
        "⚠️ Khi bấm LƯU, toàn bộ Sheet sẽ bị ghi đè. "
        "Hãy sao lưu Google Sheet trước khi chỉnh sửa."
    )

    # Danh sách sheet cho phép chỉnh sửa (trừ 7_CONG_VIEC)
    editable_sheets = [
        s for s in all_sheets.keys()
        if s not in ["7_CONG_VIEC"]
    ]

    sheet_name = st.selectbox("Chọn Sheet dữ liệu:", editable_sheets)

    df_goc = all_sheets[sheet_name].copy()

    # ---------------------------------------------------------
    # ÁP DỤNG LIÊN KẾT MÔ TẢ (lookup_display)
    # ---------------------------------------------------------
    if sheet_name in LINK_CONFIG_RAW:
        link_map = LINK_CONFIG_RAW[sheet_name]

        for col, (ref_sheet, id_col, desc_cols) in link_map.items():
            if col in df_goc.columns:
                df_ref = all_sheets.get(ref_sheet, None)
                if df_ref is not None:
                    df_goc[col + "_MO_TA"] = df_goc[col].apply(
                        lambda x: lookup_display(x, df_ref, id_col, desc_cols)
                    )

    # ---------------------------------------------------------
    # HIỂN THỊ BẢNG DỮ LIỆU
    # ---------------------------------------------------------
    st.subheader(f"📄 Nội dung Sheet: {sheet_name}")

    st.dataframe(df_goc, use_container_width=True)

    # ---------------------------------------------------------
    # FORM THÊM DÒNG MỚI
    # ---------------------------------------------------------
    render_add_row_form(sheet_name, df_goc, all_sheets)

    # ---------------------------------------------------------
    # CHỈNH SỬA TRỰC TIẾP
    # ---------------------------------------------------------
    st.subheader("✏️ Chỉnh sửa trực tiếp")

    edited_df = st.data_editor(
        df_goc.drop(columns=[c for c in df_goc.columns if c.endswith("_MO_TA")]),
        num_rows="dynamic",
        use_container_width=True,
        key=f"data_editor_{sheet_name}",
    )

    if st.button(f"💾 LƯU CẬP NHẬT CHO SHEET {sheet_name}", type="primary"):
        save_raw_sheet(sheet_name, edited_df)
