# =========================================================
# DATA_MANAGER.PY — TAB QUẢN LÝ DỮ LIỆU GỐC
# =========================================================

import streamlit as st
from config import LINK_CONFIG_RAW
from utils import lookup_display
from gsheet import save_raw_sheet


# ---------------------------------------------------------
# TAB QUẢN LÝ DỮ LIỆU GỐC
# ---------------------------------------------------------
def render_data_tab(all_sheets):
    st.header("📁 Quản lý dữ liệu gốc (Thêm / Sửa / Xóa)")

    st.warning(
        "⚠️ Lưu ý: Khi bấm LƯU, toàn bộ Sheet sẽ bị ghi đè. "
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
                    df_goc[col] = df_goc[col].apply(
                        lambda x: lookup_display(x, df_ref, id_col, desc_cols)
                    )

    # ---------------------------------------------------------
    # HIỂN THỊ BẢNG DỮ LIỆU
    # ---------------------------------------------------------
    st.markdown(
        f"**Nội dung Sheet: {sheet_name}** "
        f"(Tổng số dòng: {len(df_goc)})"
    )

    edited_df = st.data_editor(
        df_goc,
        num_rows="dynamic",
        use_container_width=True,
        key=f"data_editor_{sheet_name}",
    )

    # ---------------------------------------------------------
    # LƯU DỮ LIỆU
    # ---------------------------------------------------------
    if st.button(f"💾 LƯU CẬP NHẬT CHO SHEET {sheet_name}", type="primary"):
        save_raw_sheet(sheet_name, edited_df)
