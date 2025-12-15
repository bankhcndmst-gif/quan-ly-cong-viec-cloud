import streamlit as st
import pandas as pd
import json
from gsheet import load_all_sheets, save_raw_sheet


# =========================================================
# ✅ TAB NHẬP LIỆU TỪ JSON
# =========================================================
def render_json_import_tab():
    st.header("📥 Nhập liệu từ JSON (AI / Hệ thống ngoài)")

    st.write("""
    Tính năng này cho phép bạn:
    - Upload file JSON chứa danh sách công việc hoặc dữ liệu AI
    - Xem trước nội dung JSON
    - Lưu vào sheet **AI_JSON_DATA**
    """)

    # -----------------------------------------------------
    # ✅ Upload file JSON
    # -----------------------------------------------------
    uploaded_file = st.file_uploader("Chọn file JSON", type=["json"])

    if not uploaded_file:
        return

    try:
        json_data = json.load(uploaded_file)
    except Exception as e:
        st.error(f"❌ Lỗi đọc file JSON: {e}")
        return

    # -----------------------------------------------------
    # ✅ Chuẩn hóa JSON thành DataFrame
    # -----------------------------------------------------
    if isinstance(json_data, dict):
        # Nếu JSON là object → chuyển thành list
        json_data = [json_data]

    try:
        df_json = pd.DataFrame(json_data)
    except Exception as e:
        st.error(f"❌ Không thể chuyển JSON thành bảng: {e}")
        return

    st.subheader("📄 Xem trước dữ liệu JSON")
    st.dataframe(df_json, use_container_width=True)

    # -----------------------------------------------------
    # ✅ Tải sheet AI_JSON_DATA
    # -----------------------------------------------------
    all_sheets = load_all_sheets()
    df_ai = all_sheets.get("AI_JSON_DATA", pd.DataFrame())

    # -----------------------------------------------------
    # ✅ Nút lưu vào Google Sheets
    # -----------------------------------------------------
    if st.button("💾 Lưu vào AI_JSON_DATA", type="primary"):
        df_new = df_ai.copy()

        # Nếu sheet trống → tạo mới
        if df_new.empty:
            df_new = df_json
        else:
            # Ghép thêm dữ liệu mới
            df_new = pd.concat([df_new, df_json], ignore_index=True)

        save_raw_sheet("AI_JSON_DATA", df_new)
        st.success("✅ Đã lưu dữ liệu JSON vào sheet AI_JSON_DATA!")
