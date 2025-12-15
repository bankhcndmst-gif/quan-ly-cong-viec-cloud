import streamlit as st
import pandas as pd
from gsheet import load_all_sheets, save_raw_sheet

def render_data_manager_tab():
    st.header("📂 Quản lý dữ liệu gốc")

    # ===============================
    # 1. KIỂM TRA QUYỀN
    # ===============================
    if st.session_state.get("user_role") != "ADMIN":
        st.warning("🔒 Chỉ quản trị viên mới được chỉnh sửa dữ liệu gốc.")
        st.stop()

    # ===============================
    # 2. TẢI DỮ LIỆU
    # ===============================
    try:
        all_sheets = load_all_sheets()
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheet: {e}")
        return

    if not all_sheets:
        st.warning("Không đọc được dữ liệu nào từ file Sheet.")
        return

    # ===============================
    # 3. CHỌN SHEET
    # ===============================
    sheet_names = list(all_sheets.keys())

    index_default = sheet_names.index("4_DU_AN") if "4_DU_AN" in sheet_names else 0

    selected_sheet = st.selectbox(
        "📑 Chọn bảng dữ liệu:",
        sheet_names,
        index=index_default,
        key="select_data_manager_sheet"
    )

    # ===============================
    # 4. LẤY DỮ LIỆU
    # ===============================
    df = all_sheets.get(selected_sheet, pd.DataFrame())

    st.markdown(f"### ✏️ Đang chỉnh sửa: `{selected_sheet}`")

    if df.empty and len(df.columns) == 0:
        st.warning("⚠️ Bảng chưa có tiêu đề cột. Tạo khung tạm.")
        df = pd.DataFrame(columns=["Cột A", "Cột B", "Cột C"])

    # ❗ KHÔNG astype(str)
    df_edit = df.copy()

    # ===============================
    # 5. DATA EDITOR (ADMIN)
    # ===============================
    edited_df = st.data_editor(
        df_edit,
        num_rows="dynamic",          # 🔥 BẮT BUỘC
        use_container_width=True,
        key=f"editor_{selected_sheet}"
    )

    # ===============================
    # 6. NÚT LƯU
    # ===============================
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Lưu thay đổi", type="primary"):
            try:
                save_raw_sheet(selected_sheet, edited_df)
                st.success("✅ Đã lưu thành công!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Lỗi khi lưu: {e}")
