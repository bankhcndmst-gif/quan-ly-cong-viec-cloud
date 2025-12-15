import streamlit as st
import pandas as pd
from datetime import datetime

from gsheet import load_all_sheets, save_raw_sheet
from gemini_memory_parser import parse_memory_from_chat


# =========================================================
# ✅ TAB TRÍ NHỚ AI
# =========================================================
def render_memory_tab():
    st.header("🧠 Trí nhớ AI")

    # -----------------------------------------------------
    # ✅ Tải dữ liệu
    # -----------------------------------------------------
    all_sheets = load_all_sheets()
    df_memory = all_sheets["10_TRI_NHO_AI"].copy()
    df_config = all_sheets["8_CAU_HINH"].copy()

    # -----------------------------------------------------
    # ✅ Lấy API key
    # -----------------------------------------------------
    if "GEMINI_API_KEY" not in df_config.columns:
        st.error("❌ Không tìm thấy GEMINI_API_KEY trong sheet 8_CAU_HINH.")
        return

    api_key = df_config["GEMINI_API_KEY"].iloc[0]
    if not api_key:
        st.error("❌ GEMINI_API_KEY đang để trống.")
        return

    # -----------------------------------------------------
    # ✅ Nhập mô tả trí nhớ
    # -----------------------------------------------------
    st.subheader("✏️ Nhập mô tả để lưu vào trí nhớ AI")

    user_message = st.text_area(
        "Nhập mô tả (nhắc việc, biên bản họp, việc đã làm…):",
        height=200
    )

    if st.button("🚀 Phân tích bằng Gemini", type="primary"):
        if not user_message.strip():
            st.error("❌ Vui lòng nhập nội dung.")
            return

        df_parsed = parse_memory_from_chat(api_key, user_message, all_sheets)

        if df_parsed.empty:
            st.error("❌ Không phân tích được trí nhớ AI.")
            return

        st.session_state["memory_parsed"] = df_parsed
        st.success("✅ Đã phân tích xong! Kiểm tra bản nháp bên dưới.")

    # -----------------------------------------------------
    # ✅ Hiển thị bản nháp trí nhớ
    # -----------------------------------------------------
    if "memory_parsed" in st.session_state:
        st.subheader("📄 Bản nháp trí nhớ AI")

        df_edit = st.data_editor(
            st.session_state["memory_parsed"],
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("💾 Lưu vào trí nhớ AI", type="primary"):
            df_new = df_memory.copy()

            for _, row in df_edit.iterrows():
                df_new.loc[len(df_new)] = {
                    "LOAI": row["LOAI"],
                    "THOI_GIAN": row["THOI_GIAN"],
                    "NOI_DUNG": row["NOI_DUNG"],
                    "LAP_LAI": row["LAP_LAI"],
                    "CHU_KY": row["CHU_KY"],
                    "NGAY_TAO": row["NGAY_TAO"],
                    "LIEN_QUAN": row["LIEN_QUAN"],
                    "TOM_TAT": row["TOM_TAT"],
                    "NOI_DUNG_DAY_DU": row["NOI_DUNG_DAY_DU"],
                    "TRANG_THAI": row["TRANG_THAI"],
                }

            save_raw_sheet("10_TRI_NHO_AI", df_new)
            st.success("✅ Đã lưu trí nhớ AI vào hệ thống!")

    # -----------------------------------------------------
    # ✅ Hiển thị trí nhớ AI hiện có
    # -----------------------------------------------------
    st.markdown("---")
    st.subheader("📚 Trí nhớ AI đã lưu")

    if df_memory.empty:
        st.info("Chưa có trí nhớ AI nào.")
        return

    # Bộ lọc
    loai_list = ["Tất cả"] + sorted(df_memory["LOAI"].dropna().unique().tolist())
    loai_chon = st.selectbox("Lọc theo loại trí nhớ:", loai_list)

    df_show = df_memory.copy()
    if loai_chon != "Tất cả":
        df_show = df_show[df_show["LOAI"] == loai_chon]

    st.dataframe(df_show, use_container_width=True)
