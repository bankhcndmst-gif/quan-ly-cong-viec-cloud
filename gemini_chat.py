import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from gsheet import load_all_sheets, save_raw_sheet

def generate_chat_id(df):
    if df.empty or "ID_CHAT" not in df.columns: return "CHAT001"
    existing = df["ID_CHAT"].dropna().astype(str).tolist()
    nums = []
    for x in existing:
        if x.startswith("CHAT"):
            try: nums.append(int(x.replace("CHAT", "")))
            except: pass
    next_num = max(nums) + 1 if nums else 1
    return f"CHAT{next_num:03d}"

def render_gemini_chat_tab():
    st.header("🤖 Hỏi đáp Gemini")

    # 1. Lấy API Key từ Secrets (Ưu tiên số 1)
    api_key = st.secrets.get("general", {}).get("GEMINI_API_KEY", None)

    # 2. Nếu không có trong Secrets, mới tìm trong Sheet
    if not api_key:
        try:
            all_sheets = load_all_sheets()
            df_config = all_sheets.get("8_CAU_HINH", pd.DataFrame())
            if not df_config.empty:
                # Tìm cột trực tiếp
                if "GEMINI_API_KEY" in df_config.columns:
                    api_key = str(df_config["GEMINI_API_KEY"].iloc[0]).strip()
                # Tìm kiểu Key-Value
                elif "TEN_CAU_HINH" in df_config.columns and "GIA_TRI" in df_config.columns:
                    row = df_config[df_config["TEN_CAU_HINH"].astype(str).str.contains("Gemini", case=False, na=False)]
                    if not row.empty:
                        api_key = str(row["GIA_TRI"].iloc[0]).strip()
        except Exception as e:
            print(f"Lỗi đọc config từ sheet: {e}")

    if not api_key:
        st.error("❌ Chưa cấu hình GEMINI_API_KEY trong 'secrets.toml' hoặc Sheet 8_CAU_HINH.")
        return

    genai.configure(api_key=api_key)

    # Giao diện Chat
    cau_hoi = st.text_area("Nhập câu hỏi:", height=150)
    if st.button("🚀 Gửi câu hỏi", type="primary"):
        if not cau_hoi.strip():
            st.warning("Vui lòng nhập nội dung.")
            return
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(cau_hoi)
            
            # Lưu lịch sử
            all_sheets = load_all_sheets()
            df_memory = all_sheets.get("9_TRI_NHO_AI", pd.DataFrame(columns=["ID_CHAT", "THOI_GIAN", "CAU_HOI", "CAU_TRA_LOI"]))
            
            new_row = {
                "ID_CHAT": generate_chat_id(df_memory),
                "THOI_GIAN": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "CAU_HOI": cau_hoi,
                "CAU_TRA_LOI": response.text,
            }
            df_new = df_memory.copy()
            df_new.loc[len(df_new)] = new_row
            save_raw_sheet("9_TRI_NHO_AI", df_new)
            
            st.success("Đã trả lời!")
            st.write(response.text)
        except Exception as e:
            st.error(f"Lỗi Gemini: {e}")

    # Lịch sử
    st.markdown("---")
    try:
        all_sheets = load_all_sheets()
        df_mem = all_sheets.get("9_TRI_NHO_AI", pd.DataFrame())
        if not df_mem.empty:
            st.dataframe(df_mem.sort_values("THOI_GIAN", ascending=False).head(10), use_container_width=True)
    except:
        pass
