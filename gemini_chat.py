import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from gsheet import load_all_sheets, save_raw_sheet

# =========================================================
# ✅ HÀM TẠO ID_CHAT TỰ ĐỘNG
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
# ✅ TAB HỎI – ĐÁP GEMINI (ĐÃ SỬA LỖI ĐỌC CONFIG)
# =========================================================
def render_gemini_chat_tab():
    st.header("🤖 Hỏi đáp Gemini")

    # Tải dữ liệu
    all_sheets = load_all_sheets()
    df_memory = all_sheets["9_TRI_NHO_AI"].copy()
    df_config = all_sheets["8_CAU_HINH"].copy()

    # -----------------------------------------------------
    # 🛠️ LOGIC LẤY API KEY THÔNG MINH (Hỗ trợ cả 2 kiểu cấu hình)
    # -----------------------------------------------------
    api_key = ""
    
    # Cách 1: Tìm theo tên cột trực tiếp (Nếu bạn đặt tên cột là GEMINI_API_KEY)
    if "GEMINI_API_KEY" in df_config.columns:
        val = df_config["GEMINI_API_KEY"].iloc[0]
        if val: api_key = str(val).strip()

    # Cách 2: Tìm theo dạng Key-Value (TEN_CAU_HINH - GIA_TRI) như ảnh bạn gửi
    if not api_key and "TEN_CAU_HINH" in df_config.columns and "GIA_TRI" in df_config.columns:
        # Tìm dòng có chữ "Gemini" trong tên cấu hình
        row = df_config[df_config["TEN_CAU_HINH"].astype(str).str.contains("Gemini", case=False, na=False)]
        if not row.empty:
            api_key = str(row["GIA_TRI"].iloc[0]).strip()

    # Kiểm tra kết quả
    if not api_key:
        st.error("❌ Không tìm thấy API Key trong sheet 8_CAU_HINH.")
        st.info("👉 Hãy đảm bảo sheet có cột 'TEN_CAU_HINH' chứa 'Gemini_API_Key' và cột 'GIA_TRI' chứa mã.")
        return

    genai.configure(api_key=api_key)

    # -----------------------------------------------------
    # ✅ Giao diện Chat
    # -----------------------------------------------------
    cau_hoi = st.text_area("Nhập câu hỏi của bạn:", height=150)

    if st.button("🚀 Gửi câu hỏi", type="primary"):
        if not cau_hoi.strip():
            st.error("❌ Vui lòng nhập câu hỏi.")
            return

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(cau_hoi)
            cau_tra_loi = response.text

            new_id = generate_chat_id(df_memory)
            new_row = {
                "ID_CHAT": new_id,
                "THOI_GIAN": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "CAU_HOI": cau_hoi,
                "CAU_TRA_LOI": cau_tra_loi,
            }

            df_new = df_memory.copy()
            df_new.loc[len(df_new)] = new_row
            save_raw_sheet("9_TRI_NHO_AI", df_new)

            st.success("✅ Đã nhận câu trả lời từ Gemini!")
            st.subheader("📌 Câu trả lời:")
            st.write(cau_tra_loi)

        except Exception as e:
            st.error(f"❌ Lỗi khi gọi Gemini: {e}")

    st.markdown("---")
    st.subheader("🕘 Lịch sử hỏi – đáp gần đây")
    if not df_memory.empty:
        df_show = df_memory.sort_values("THOI_GIAN", ascending=False).head(20)
        st.dataframe(df_show, use_container_width=True)
