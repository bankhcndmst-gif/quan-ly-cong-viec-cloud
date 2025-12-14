# =========================================================
# APP.PY — FILE CHÍNH CỦA ỨNG DỤNG STREAMLIT
# =========================================================

import streamlit as st

from gsheet import load_all_sheets
from report import render_report_tab
from new_task import render_new_task_tab
from data_manager import render_data_tab


# ---------------------------------------------------------
# HÀM MAIN
# ---------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Quản lý công việc EVNGENCO1",
        layout="wide"
    )

    st.title("⚡ Hệ thống Quản lý Công việc EVNGENCO1")

    # -----------------------------------------------------
    # TẢI TẤT CẢ SHEET
    # -----------------------------------------------------
    all_sheets = load_all_sheets()

    df_cv = all_sheets["7_CONG_VIEC"]
    df_ns = all_sheets["1_NHAN_SU"]
    df_dv = all_sheets["2_DON_VI"]

    # -----------------------------------------------------
    # TABS GIAO DIỆN
    # -----------------------------------------------------
    tab1, tab2, tab3 = st.tabs([
        "📊 Báo cáo",
        "📝 Giao việc mới",
        "📁 Dữ liệu gốc"
    ])

    with tab1:
        render_report_tab(all_sheets, df_cv, df_ns, df_dv)

    with tab2:
        render_new_task_tab(all_sheets, df_cv, df_ns, df_dv)

    with tab3:
        render_data_tab(all_sheets)


# ---------------------------------------------------------
# CHẠY ỨNG DỤNG
# ---------------------------------------------------------
if __name__ == "__main__":
    main()
