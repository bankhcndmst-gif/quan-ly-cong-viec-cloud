import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai

from gsheet import load_all_sheets, save_raw_sheet


# =========================================================
# ✅ HÀM TẠO ID_CHAT TỰ ĐỘNG (CHAT001, CHAT002…)
# =========================================================
def generate_chat_id(df):
    if df.empty or "ID_CHAT" not in df.columns:
        return "CHAT001"

    existing = df["ID_CHAT"].dropna().astype(str).tolist()
    nums = []

    for x in existing:
        if x.startswith("CHAT"):
            try:
                nums.append(int(x.replace("CHAT", "")))
            except:
                pass

    next_num = max(nums) + 1 if nums else 1
    return f"CHAT{next_num:03d}"


# =========================================================
# ✅ TAB HỎI – ĐÁP GEMINI
# =========================================================
def render_gemini_chat_tab():
    st.header("🤖 Hỏi đáp Gemini")

    # -----------------------------------------------------
    # ✅ Tải dữ liệu
    # -----------------------------------------------------
    all_sheets = load_all_sheets()
    df_memory = all_sheets["9_TRI_NHO_AI"].copy()
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

    genai.configure(api_key=api_key)

    # -----------------------------------------------------
    # ✅ Nhập câu hỏi
    # -----------------------------------------------------
    cau_hoi = st.text_area("Nhập câu hỏi của bạn:", height=150)

    if st.button("🚀 Gửi câu hỏi", type="primary"):
        if not cau_hoi.strip():
            st.error("❌ Vui lòng nhập câu hỏi.")
            return

        try:
            # -----------------------------------------------------
            # ✅ Gửi câu hỏi đến Gemini
            # -----------------------------------------------------
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(cau_hoi)
            cau_tra_loi = response.text

            # -----------------------------------------------------
            # ✅ Tạo ID_CHAT mới
            # -----------------------------------------------------
            new_id = generate_chat_id(df_memory)

            # -----------------------------------------------------
            # ✅ Ghi vào sheet 9_TRI_NHO_AI
            # -----------------------------------------------------
            new_row = {
                "ID_CHAT": new_id,
                "THOI_GIAN": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "CAU_HOI": cau_hoi,
                "CAU_TRA_LOI": cau_tra_loi,
            }

            df_new = df_memory.copy()
            df_new.loc[len(df_new)] = new_row

            save_raw_sheet("9_TRI_NHO_AI", df_new)

            # -----------------------------------------------------
            # ✅ Hiển thị kết quả
            # -----------------------------------------------------
            st.success("✅ Đã nhận câu trả lời từ Gemini!")
            st.subheader("📌 Câu trả lời:")
            st.write(cau_tra_loi)

        except Exception as e:
            st.error(f"❌ Lỗi khi gọi Gemini: {e}")

    # -----------------------------------------------------
    # ✅ Hiển thị lịch sử hỏi–đáp
    # -----------------------------------------------------
    st.markdown("---")
    st.subheader("🕘 Lịch sử hỏi – đáp gần đây")

    if df_memory.empty:
        st.info("Chưa có lịch sử hỏi – đáp.")
        return

    df_show = df_memory.sort_values("THOI_GIAN", ascending=False).head(20)
    st.dataframe(df_show, use_container_width=True)
