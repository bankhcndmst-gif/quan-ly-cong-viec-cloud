import streamlit as st
import pandas as pd
from gsheet import load_all_sheets, save_raw_sheet
from gemini_memory_parser import parse_memory_from_chat

def render_memory_tab():
    st.header("🧠 Trí nhớ AI")

    # 1. Lấy API Key từ Secrets
    api_key = st.secrets.get("general", {}).get("GEMINI_API_KEY", None)

    all_sheets = load_all_sheets()
    
    # 2. Fallback tìm trong Sheet (Xử lý an toàn)
    if not api_key:
        try:
            df_config = all_sheets.get("8_CAU_HINH", pd.DataFrame())
            if not df_config.empty:
                if "GEMINI_API_KEY" in df_config.columns:
                    api_key = str(df_config["GEMINI_API_KEY"].iloc[0]).strip()
                elif "TEN_CAU_HINH" in df_config.columns and "GIA_TRI" in df_config.columns:
                    row = df_config[df_config["TEN_CAU_HINH"].astype(str).str.contains("Gemini", case=False, na=False)]
                    if not row.empty:
                        api_key = str(row["GIA_TRI"].iloc[0]).strip()
        except: pass

    if not api_key:
        st.error("❌ Vui lòng thêm GEMINI_API_KEY vào secrets.toml")
        return

    # Giao diện
    user_message = st.text_area("Nhập nội dung ghi nhớ:", height=200)
    if st.button("🚀 Phân tích", type="primary"):
        if user_message.strip():
            df_parsed = parse_memory_from_chat(api_key, user_message, all_sheets)
            if not df_parsed.empty:
                st.session_state["memory_parsed"] = df_parsed
                st.success("Đã phân tích!")
            else:
                st.error("Lỗi phân tích.")

    if "memory_parsed" in st.session_state:
        df_edit = st.data_editor(st.session_state["memory_parsed"], num_rows="dynamic", use_container_width=True)
        if st.button("💾 Lưu trí nhớ", type="primary"):
            df_mem = all_sheets.get("11_TRI_NHO_AI", pd.DataFrame())
            df_new = df_mem.copy()
            for _, row in df_edit.iterrows():
                new_row = {}
                # Chỉ lấy các cột khớp với sheet để tránh lỗi
                for col in df_new.columns:
                    if col in row:
                        new_row[col] = row[col]
                    else:
                        new_row[col] = ""
                
                df_new = pd.concat([df_new, pd.DataFrame([new_row])], ignore_index=True)

            save_raw_sheet("11_TRI_NHO_AI", df_new)
            st.success("Đã lưu!")

    st.markdown("---")
    try:
        df_mem = all_sheets.get("11_TRI_NHO_AI", pd.DataFrame())
        if not df_mem.empty and "LOAI" in df_mem.columns:
            loai_chon = st.selectbox("Lọc theo loại:", ["Tất cả"] + list(df_mem["LOAI"].unique()))
            if loai_chon != "Tất cả":
                df_mem = df_mem[df_mem["LOAI"] == loai_chon]
            st.dataframe(df_mem, use_container_width=True)
    except: pass
