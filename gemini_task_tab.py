import streamlit as st
import pandas as pd
from gsheet import load_all_sheets, save_raw_sheet
from gemini_task_parser import parse_task_from_chat

def generate_task_id(df):
    if df.empty or "ID_CONG_VIEC" not in df.columns: return "CV001"
    existing = df["ID_CONG_VIEC"].dropna().astype(str).tolist()
    nums = []
    for x in existing:
        if x.startswith("CV"):
            try: nums.append(int(x.replace("CV", "")))
            except: pass
    next_num = max(nums) + 1 if nums else 1
    return f"CV{next_num:03d}"

def render_gemini_task_tab():
    st.header("🤖 Giao việc bằng Gemini")

    # 1. Lấy API Key từ Secrets
    api_key = st.secrets.get("general", {}).get("GEMINI_API_KEY", None)

    # 2. Fallback tìm trong Sheet (có Try/Except an toàn)
    all_sheets = load_all_sheets()
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
        st.error("❌ Thiếu GEMINI_API_KEY trong secrets.toml.")
        return

    user_message = st.text_area("Mô tả công việc:", height=200)
    if st.button("🚀 Phân tích", type="primary"):
        if not user_message.strip(): return
        tasks = parse_task_from_chat(api_key, user_message, all_sheets)
        if not tasks.empty:
            st.session_state["gemini_tasks"] = tasks
            st.success("Đã phân tích xong!")
        else:
            st.error("Không phân tích được.")

    if "gemini_tasks" in st.session_state:
        edited_tasks = st.data_editor(st.session_state["gemini_tasks"], num_rows="dynamic", use_container_width=True)
        if st.button("💾 Lưu công việc", type="primary"):
            df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame())
            df_new = df_cv.copy()
            for _, row in edited_tasks.iterrows():
                # Tạo row an toàn
                new_row = {"ID_CONG_VIEC": generate_task_id(df_new), "TRANG_THAI": "Đang thực hiện"}
                for col in edited_tasks.columns:
                    new_row[col] = row[col]
                # Đảm bảo đủ cột
                for col in df_new.columns:
                    if col not in new_row: new_row[col] = ""
                
                df_new = pd.concat([df_new, pd.DataFrame([new_row])], ignore_index=True)
            
            save_raw_sheet("7_CONG_VIEC", df_new)
            st.success("Đã lưu!")
