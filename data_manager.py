import streamlit as st
import pandas as pd
from gsheet import load_all_sheets, save_raw_sheet

def render_data_manager_tab():
    st.header("📂 Quản lý dữ liệu gốc")

    # 1. Tải dữ liệu
    try:
        all_sheets = load_all_sheets()
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheet: {e}")
        return

    # 2. Chọn Sheet
    if not all_sheets:
        st.warning("Không tìm thấy dữ liệu.")
        return

    sheet_names = list(all_sheets.keys())
    selected_sheet = st.selectbox("Chọn bảng dữ liệu:", sheet_names)
    
    df = all_sheets.get(selected_sheet, pd.DataFrame())

    # 3. Hiển thị & Sửa lỗi
    st.markdown(f"### Đang chỉnh sửa: `{selected_sheet}`")
    
    # Nếu sheet chưa có dữ liệu, tạo một DataFrame rỗng có cột mẫu để không bị lỗi
    if df.empty:
        st.info("⚠️ Bảng này đang trống. Hãy nhập dòng đầu tiên làm tiêu đề.")
        # Tạo bảng tạm để người dùng nhập
        df = pd.DataFrame(columns=["COT_1", "COT_2", "COT_3"])

    # Xử lý các cột ngày tháng để hiển thị string cho dễ sửa (tránh lỗi hiển thị)
    df_display = df.copy()
    for col in df_display.columns:
        if pd.api.types.is_datetime64_any_dtype(df_display[col]):
            df_display[col] = df_display[col].dt.strftime('%Y-%m-%d').fillna("")

    # 4. Data Editor
    edited_df = st.data_editor(
        df_display,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{selected_sheet}"
    )

    # 5. Lưu
    if st.button("💾 Lưu thay đổi", type="primary"):
        try:
            save_raw_sheet(selected_sheet, edited_df)
            st.success("✅ Đã lưu thành công!")
            st.cache_data.clear() # Xóa cache để cập nhật
            st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi khi lưu: {e}")
