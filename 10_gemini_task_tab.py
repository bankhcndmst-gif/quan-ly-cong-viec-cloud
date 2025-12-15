import streamlit as st
import pandas as pd
from datetime import datetime

from gsheet import load_all_sheets, save_raw_sheet
from utils import get_display_list_multi
from config import LINK_CONFIG_RAW
from gemini_task_parser import parse_task_from_chat


# =========================================================
# ✅ HÀM TẠO ID CÔNG VIỆC TỰ ĐỘNG (CV001…)
# =========================================================
def generate_task_id(df):
    if df.empty or "ID_CONG_VIEC" not in df.columns:
        return "CV001"

    existing = df["ID_CONG_VIEC"].dropna().astype(str).tolist()
    nums = []

    for x in existing:
        if x.startswith("CV"):
            try:
                nums.append(int(x.replace("CV", "")))
            except:
                pass

    next_num = max(nums) + 1 if nums else 1
    return f"CV{next_num:03d}"


# =========================================================
# ✅ TAB GIAO VIỆC BẰNG GEMINI
# =========================================================
def render_gemini_task_tab():
    st.header("🤖 Giao việc bằng Gemini")

    # -----------------------------------------------------
    # ✅ Tải dữ liệu
    # -----------------------------------------------------
    all_sheets = load_all_sheets()
    df_cv = all_sheets["7_CONG_VIEC"].copy()
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
    # ✅ Nhập mô tả công việc
    # -----------------------------------------------------
    st.subheader("✏️ Nhập mô tả công việc")
    user_message = st.text_area("Nhập mô tả công việc cần giao:", height=200)

    if st.button("🚀 Phân tích bằng Gemini", type="primary"):
        if not user_message.strip():
            st.error("❌ Vui lòng nhập mô tả công việc.")
            return

        tasks = parse_task_from_chat(api_key, user_message, all_sheets)

        if tasks.empty:
            st.error("❌ Không phân tích được công việc.")
            return

        st.session_state["gemini_tasks"] = tasks
        st.success("✅ Đã phân tích xong! Kiểm tra bản nháp bên dưới.")

    # -----------------------------------------------------
    # ✅ Hiển thị bản nháp công việc
    # -----------------------------------------------------
    if "gemini_tasks" in st.session_state:
        st.subheader("📄 Bản nháp công việc")

        tasks = st.session_state["gemini_tasks"]

        edited_tasks = st.data_editor(tasks, num_rows="dynamic", use_container_width=True)

        # -----------------------------------------------------
        # ✅ Nút lưu vào Google Sheets
        # -----------------------------------------------------
        if st.button("💾 Lưu vào hệ thống", type="primary"):
            df_new = df_cv.copy()

            for _, row in edited_tasks.iterrows():
                new_id = generate_task_id(df_new)

                new_row = {
                    "ID_CONG_VIEC": new_id,
                    "TEN_VIEC": row["TEN_VIEC"],
                    "NOI_DUNG": row["NOI_DUNG"],
                    "NGUOI_GIAO": row["NGUOI_GIAO"],
                    "NGUOI_NHAN": row["NGUOI_NHAN"],
                    "NGAY_GIAO": row["NGAY_GIAO"],
                    "HAN_CHOT": row["HAN_CHOT"],
                    "IDDV_CV": row["IDDV_CV"],
                    "IDDA_CV": row["IDDA_CV"],
                    "IDGT_CV": row["IDGT_CV"],
                    "IDHD_CV": row["IDHD_CV"],
                    "IDVB_VAN_BAN": row["IDVB_VAN_BAN"],
                    "TRANG_THAI": "Đang thực hiện",
                    "GHI_CHU_GEMINI": row.get("GHI_CHU_GEMINI", "")
                }

                df_new.loc[len(df_new)] = new_row

            save_raw_sheet("7_CONG_VIEC", df_new)
            st.success("✅ Đã lưu toàn bộ công việc vào hệ thống!")
