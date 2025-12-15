import streamlit as st
import pandas as pd
from gsheet import load_all_sheets, save_raw_sheet
from gemini_memory_parser import parse_memory_from_chat

# =========================================================
# ✅ TAB TRÍ NHỚ AI (ĐÃ SỬA LỖI CONFIG)
# =========================================================
def render_memory_tab():
    st.header("🧠 Trí nhớ AI")

    all_sheets = load_all_sheets()
    df_memory = all_sheets["11_TRI_NHO_AI"].copy() # Lưu ý: dùng 11_TRI_NHO_AI theo config mới
    df_config = all_sheets["8_CAU_HINH"].copy()

    # -----------------------------------------------------
    # 🛠️ LOGIC LẤY API KEY THÔNG MINH
    # -----------------------------------------------------
    api_key = ""
    if "GEMINI_API_KEY" in df_config.columns:
        val = df_config["GEMINI_API_KEY"].iloc[0]
        if val: api_key = str(val).strip()

    if not api_key and "TEN_CAU_HINH" in df_config.columns and "GIA_TRI" in df_config.columns:
        row = df_config[df_config["TEN_CAU_HINH"].astype(str).str.contains("Gemini", case=False, na=False)]
        if not row.empty:
            api_key = str(row["GIA_TRI"].iloc[0]).strip()

    if not api_key:
        st.error("❌ Không tìm thấy API Key trong sheet 8_CAU_HINH.")
        return

    # -----------------------------------------------------
    # Giao diện chính
    # -----------------------------------------------------
    st.subheader("✏️ Nhập mô tả để lưu vào trí nhớ AI")
    user_message = st.text_area("Nhập nội dung (nhắc việc, họp hành...):", height=200)

    if st.button("🚀 Phân tích bằng Gemini", type="primary"):
        if not user_message.strip():
            st.error("❌ Vui lòng nhập nội dung.")
            return

        df_parsed = parse_memory_from_chat(api_key, user_message, all_sheets)
        if df_parsed.empty:
            st.error("❌ Không phân tích được.")
            return

        st.session_state["memory_parsed"] = df_parsed
        st.success("✅ Đã phân tích xong!")

    if "memory_parsed" in st.session_state:
        st.subheader("📄 Bản nháp trí nhớ AI")
        df_edit = st.data_editor(st.session_state["memory_parsed"], num_rows="dynamic", use_container_width=True)

        if st.button("💾 Lưu vào trí nhớ AI", type="primary"):
            df_new = df_memory.copy()
            for _, row in df_edit.iterrows():
                # Map columns an toàn
                new_row = {col: row[col] for col in df_new.columns if col in row}
                df_new.loc[len(df_new)] = new_row

            save_raw_sheet("11_TRI_NHO_AI", df_new)
            st.success("✅ Đã lưu trí nhớ AI!")

    st.markdown("---")
    st.subheader("📚 Trí nhớ AI đã lưu")
    if not df_memory.empty:
        if "LOAI" in df_memory.columns:
            loai_list = ["Tất cả"] + sorted(df_memory["LOAI"].dropna().unique().tolist())
            loai_chon = st.selectbox("Lọc theo loại:", loai_list)
            if loai_chon != "Tất cả":
                df_memory = df_memory[df_memory["LOAI"] == loai_chon]
        st.dataframe(df_memory, use_container_width=True)
