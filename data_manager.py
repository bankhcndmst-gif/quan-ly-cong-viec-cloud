import streamlit as st
import pandas as pd
from gsheet import load_all_sheets, save_raw_sheet

def render_data_manager_tab():
    st.header("📂 Quản lý dữ liệu gốc")

    # 1. Tải dữ liệu
    try:
        all_sheets = load_all_sheets()
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return

    if not all_sheets:
        st.warning("Không đọc được dữ liệu nào từ file Sheet.")
        return

    # 2. Chọn Sheet
    sheet_names = list(all_sheets.keys())
    # Ưu tiên chọn tab đang bị lỗi để kiểm tra
    index_default = 0
    if "4_DU_AN" in sheet_names:
        index_default = sheet_names.index("4_DU_AN")
        
    selected_sheet = st.selectbox("Chọn bảng dữ liệu:", sheet_names, index=index_default)
    
    # 3. Lấy dữ liệu
    df = all_sheets.get(selected_sheet, pd.DataFrame())

    st.markdown(f"### Đang chỉnh sửa: `{selected_sheet}`")
    
    # 4. Hiển thị Data Editor
    # Nếu thực sự trống (0 dòng, 0 cột), tạo khung tạm
    if df.empty and len(df.columns) == 0:
        st.warning("⚠️ Bảng này chưa có tiêu đề cột.")
        df = pd.DataFrame(columns=["Cột A", "Cột B", "Cột C"])
    
    # Ép kiểu sang string để hiển thị an toàn (tránh lỗi ngày tháng hiển thị)
    df_display = df.astype(str)
    
    edited_df = st.data_editor(
        df_display,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{selected_sheet}" 
    )

    # 5. Nút Lưu
    if st.button("💾 Lưu thay đổi", type="primary"):
        try:
            save_raw_sheet(selected_sheet, edited_df)
            st.success("✅ Đã lưu thành công!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi khi lưu: {e}")
