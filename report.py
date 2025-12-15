import streamlit as st
import pandas as pd
from gsheet import load_all_sheets
from utils import get_display_list_multi, lookup_display, format_date_vn

# =========================================================
# ✅ HÀM GỢI Ý TÔ MÀU TRẠNG THÁI
# =========================================================
def highlight_status(s):
    """Tô màu cho cột Trạng thái tổng"""
    if s == 'HOAN_THANH' or s == 'Hoàn thành':
        return 'background-color: #d4edda; color: #155724' # Xanh lá
    if s == 'TRE_HAN' or s == 'Quá hạn':
        return 'background-color: #f8d7da; color: #721c24' # Đỏ
    if s == 'DANG_THUC_HIEN' or s == 'Đang thực hiện':
        return 'background-color: #ffeeba; color: #856404' # Vàng
    return ''

# =========================================================
# ✅ TAB BÁO CÁO CÔNG VIỆC
# =========================================================
def render_report_tab():
    st.header("📊 Báo cáo Công việc & Tiến độ")

    # 1. Tải dữ liệu nền
    try:
        all_sheets = load_all_sheets()
        df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame()).copy()
        df_ns = all_sheets.get("1_NHAN_SU", pd.DataFrame())
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return

    if df_cv.empty:
        st.warning("Chưa có dữ liệu công việc trong Sheet '7_CONG_VIEC'.")
        return
        
    # --- 2. Xử lý và làm giàu dữ liệu ---
    
    # 2.1. Chuẩn hóa/Tính toán trạng thái Quá hạn
    # df_cv đã được parse_dates từ gsheet.py/utils.py
    if 'HAN_CHOT' in df_cv.columns:
        now = pd.to_datetime(datetime.now().date())
        # Tạo cột 'QUÁ HẠN' (True/False)
        df_cv['QUÁ_HẠN'] = (df_cv['HAN_CHOT'] < now) & (df_cv['TRANG_THAI_TONG'] != 'Hoàn thành')
        
        # Cập nhật TRẠNG_THÁI_TỔNG nếu cần (Đảm bảo cột TRANG_THAI_TONG tồn tại)
        if 'TRANG_THAI_TONG' not in df_cv.columns:
            df_cv['TRANG_THAI_TONG'] = 'Chưa thực hiện'
            
        df_cv.loc[df_cv['QUÁ_HẠN'], 'TRANG_THAI_TONG'] = 'Quá hạn'
    
    # 2.2. Thêm cột Tên người nhận (Tên người dùng)
    if 'NGUOI_NHAN' in df_cv.columns:
        df_cv['TÊN_NGƯỜI_NHẬN'] = df_cv['NGUOI_NHAN'].apply(
            lambda x: lookup_display(x, df_ns, "ID_NHAN_SU", ["HO_TEN"])
        )

    # --- 3. Giao diện Bộ lọc ---
    st.subheader("Bộ lọc")
    col1, col2, col3 = st.columns(3)
    
    # Lọc theo Người nhận
    with col1:
        list_ns_report, map_ns_report = get_display_list_multi(df_ns, "ID_NHAN_SU", ["HO_TEN"], "Tất cả nhân sự")
        nguoi_nhan_filter = st.selectbox("Lọc theo Chủ trì", list_ns_report)
        id_nguoi_nhan_filter = map_ns_report.get(nguoi_nhan_filter, "")
    
    # Lọc theo Trạng thái
    with col2:
        list_trang_thai = ['Tất cả'] + list(df_cv['TRANG_THAI_TONG'].dropna().unique())
        trang_thai_filter = st.selectbox("Lọc theo Trạng thái", list_trang_thai)

    # Lọc theo Dự án (ví dụ)
    with col3:
        df_da = all_sheets.get("4_DU_AN", pd.DataFrame())
        list_da_report, map_da_report = get_display_list_multi(df_da, "ID_DU_AN", ["TEN_DU_AN"], "Tất cả Dự án")
        du_an_filter = st.selectbox("Lọc theo Dự án", list_da_report)
        id_du_an_filter = map_da_report.get(du_an_filter, "")

    # --- 4. Áp dụng Bộ lọc ---
    df_filtered = df_cv.copy()
    
    if id_nguoi_nhan_filter:
        df_filtered = df_filtered[df_filtered['NGUOI_NHAN'] == id_nguoi_nhan_filter]
        
    if trang_thai_filter != 'Tất cả':
        df_filtered = df_filtered[df_filtered['TRANG_THAI_TONG'] == trang_thai_filter]
        
    if id_du_an_filter:
        df_filtered = df_filtered[df_filtered['IDDA_CV'] == id_du_an_filter]


    # --- 5. Hiển thị Kết quả ---
    st.subheader(f"Kết quả ({len(df_filtered)} công việc)")
    
    # Chọn cột hiển thị (Lược bỏ bớt cột phụ để dễ nhìn)
    cols_display = [
        'ID_CONG_VIEC', 'TEN_VIEC', 'TÊN_NGƯỜI_NHẬN', 
        'NGAY_GIAO', 'HAN_CHOT', 'TRANG_THAI_TONG', 
        'NOI_DUNG', 'IDDA_CV'
    ]
    
    # Sắp xếp và chỉ lấy cột cần thiết
    df_display = df_filtered.sort_values(by=['QUÁ_HẠN', 'HAN_CHOT'], ascending=[False, True])
    df_display = df_display[[c for c in cols_display if c in df_display.columns]]
    
    # Áp dụng định dạng ngày VN
    for col in ['NGAY_GIAO', 'HAN_CHOT']:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: format_date_vn(x))

    # Áp dụng màu sắc (Styler)
    st.dataframe(
        df_display.style.applymap(highlight_status, subset=['TRANG_THAI_TONG']),
        use_container_width=True,
        hide_index=True
    )
