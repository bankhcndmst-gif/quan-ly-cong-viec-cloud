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

    # 2. Chọn Sheet để sửa
    sheet_names = list(all_sheets.keys())
    if not sheet_names:
        st.warning("Không tìm thấy sheet nào trong file.")
        return

    selected_sheet = st.selectbox("Chọn sheet để quản lý:", sheet_names, index=0)
    
    # Lấy dữ liệu của sheet đã chọn
    df = all_sheets.get(selected_sheet, pd.DataFrame())

    # 3. Hiển thị khu vực nhập liệu
    st.markdown(f"### Đang chỉnh sửa: `{selected_sheet}`")
    
    if df.empty:
        st.info("⚠️ Sheet này đang trống. Bạn hãy nhập dòng dữ liệu đầu tiên vào bảng dưới đây.")
        # Nếu sheet trống hoàn toàn (không có cả tiêu đề), tạo tiêu đề giả để không lỗi
        if len(df.columns) == 0:
             df = pd.DataFrame(columns=["COT_1", "COT_2", "COT_3"])

    # 4. Hiện bảng biên tập (Data Editor)
    # num_rows="dynamic" giúp bạn thêm/xóa dòng thoải mái
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{selected_sheet}" # Key riêng để không bị lag
    )

    # 5. Nút Lưu thay đổi
    if st.button("💾 Lưu thay đổi lên Google Sheet", type="primary"):
        try:
            # Lưu lên Google Sheet
            save_raw_sheet(selected_sheet, edited_df)
            st.success("✅ Đã lưu thành công! Đang tải lại dữ liệu...")
            
            # Xóa cache để App nhận dữ liệu mới ngay lập tức
            st.cache_data.clear()
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Lỗi khi lưu: {e}")

    st.caption("Mẹo: Bấm vào dòng cuối cùng có dấu (+) để thêm dòng mới. Chọn ô vuông bên trái dòng và bấm Delete để xóa.")
