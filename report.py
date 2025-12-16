import streamlit as st

import pandas as pd

from datetime import datetime

from gsheet import load_all_sheets

from utils import lookup_display, format_date_vn # <-- Dùng lại các hàm hỗ trợ từ utils



# =========================================================

# ✅ HÀM TÔ MÀU (CẦN ĐỊNH NGHĨA TRƯỚC)

# =========================================================

def highlight_status(s):

    """Tô màu cho cột Trạng thái tổng"""

    s_clean = str(s).strip().upper()

    if s_clean == 'HOÀN THÀNH':

        return 'background-color: #d4edda; color: #155724' # Xanh lá

    if s_clean == 'TRỄ HẠN':

        return 'background-color: #f8d7da; color: #721c24' # Đỏ

    if s_clean == 'ĐANG THỰC HIỆN':

        return 'background-color: #ffeeba; color: #856404' # Vàng

    return ''



# =========================================================

# ✅ TÍNH TRẠNG THÁI CÔNG VIỆC

# =========================================================

def compute_status(row):

    trang_thai_goc = row.get("TRANG_THAI_TONG", "")

    ngay_xong = row.get("NGAY_THUC_TE_XONG")

    han = row.get("HAN_CHOT")



    # 1. Nếu đã xong

    if str(trang_thai_goc).strip().upper() == "HOÀN THÀNH":

        return "Hoàn thành"



    # 2. Nếu quá hạn (Chỉ tính nếu có hạn chót hợp lệ)

    if han and isinstance(han, pd.Timestamp) and han < pd.to_datetime(datetime.now().date()):

        return "Trễ hạn"



    # 3. Mặc định

    return "Đang thực hiện"



# =========================================================

# ✅ TAB BÁO CÁO CÔNG VIỆC (PHIÊN BẢN AN TOÀN)

# =========================================================

def render_report_tab():

    st.header("📊 Báo cáo công việc")



    # 1. Tải dữ liệu

    try:

        all_sheets = load_all_sheets()

        df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame()).copy()

        df_ns = all_sheets.get("1_NHAN_SU", pd.DataFrame()).copy()

        df_da = all_sheets.get("4_DU_AN", pd.DataFrame()).copy()

        df_gt = all_sheets.get("5_GOI_THAU", pd.DataFrame()).copy()

        df_hd = all_sheets.get("6_HOP_DONG", pd.DataFrame()).copy()

    except Exception as e:

        st.error(f"Lỗi tải dữ liệu: {e}")

        return



    if df_cv.empty:

        st.warning("Chưa có dữ liệu công việc trong sheet 7_CONG_VIEC.")

        return



    # 2. Xử lý dữ liệu ngày tháng & Tính trạng thái

    # Gsheet.py đã xử lý datetime, ta chỉ cần tính toán

    df_cv["TRANG_THAI_TONG"] = df_cv.apply(compute_status, axis=1)



    # =========================================================

    # 🔍 KHU VỰC BỘ LỌC (FILTER)

    # =========================================================

    with st.expander("🔍 Bộ lọc nâng cao", expanded=True):

        col1, col2, col3 = st.columns(3)

        col4, col5, col6 = st.columns(3)

        

        # --- Lấy dữ liệu cho Filter (Đảm bảo ID và Tên tồn tại) ---

        

        da_map = dict(zip(df_da["ID_DU_AN"], df_da["TEN_DU_AN"])) if "ID_DU_AN" in df_da.columns and "TEN_DU_AN" in df_da.columns else {}

        list_da = ["Tất cả"] + list(da_map.values())

        

        gt_map = dict(zip(df_gt["ID_GOI_THAU"], df_gt["TEN_GOI_THAU"])) if "ID_GOI_THAU" in df_gt.columns and "TEN_GOI_THAU" in df_gt.columns else {}

        list_gt = ["Tất cả"] + list(gt_map.values())



        hd_map = dict(zip(df_hd["ID_HOP_DONG"], df_hd["TEN_HD"])) if "ID_HOP_DONG" in df_hd.columns and "TEN_HD" in df_hd.columns else {}

        list_hd = ["Tất cả"] + list(hd_map.values())





        # --- Hiển thị Filter ---

        search_ten = col1.text_input("Tên công việc (Từ khóa)", "")

        filter_da = col2.selectbox("Dự án", list_da)

        filter_gt = col3.selectbox("Gói thầu", list_gt)

        filter_hd = col4.selectbox("Hợp đồng", list_hd)



        if "LOAI_VIEC" in df_cv.columns:

            list_loai = ["Tất cả"] + list(df_cv["LOAI_VIEC"].dropna().unique())

            filter_loai = col5.selectbox("Loại việc", list_loai)

        else: filter_loai = "Tất cả"

            

        list_tt = ["Tất cả", "Đang thực hiện", "Trễ hạn", "Hoàn thành"]

        filter_tt = col6.selectbox("Trạng thái", list_tt)



    # =========================================================

    # ⚙️ XỬ LÝ LỌC

    # =========================================================

    df_filtered = df_cv.copy()



    # Lọc tên

    if search_ten and "TEN_VIEC" in df_filtered.columns:

        df_filtered = df_filtered[df_filtered["TEN_VIEC"].astype(str).str.contains(search_ten, case=False, na=False)]



    # Lọc Dự án/Gói thầu/Hợp đồng (Dùng map ngược)

    def find_id_from_value(map_dict, value):

        return [k for k, v in map_dict.items() if v == value]

        

    if filter_da != "Tất cả" and "IDDA_CV" in df_filtered.columns:

        selected_id = find_id_from_value(da_map, filter_da)

        if selected_id: df_filtered = df_filtered[df_filtered["IDDA_CV"] == selected_id[0]]



    if filter_gt != "Tất cả" and "IDGT_CV" in df_filtered.columns:

        selected_id = find_id_from_value(gt_map, filter_gt)

        if selected_id: df_filtered = df_filtered[df_filtered["IDGT_CV"] == selected_id[0]]



    if filter_hd != "Tất cả" and "IDHD_CV" in df_filtered.columns:

        selected_id = find_id_from_value(hd_map, filter_hd)

        if selected_id: df_filtered = df_filtered[df_filtered["IDHD_CV"] == selected_id[0]]





    # Lọc Loại & Trạng thái

    if filter_loai != "Tất cả" and "LOAI_VIEC" in df_filtered.columns:

        df_filtered = df_filtered[df_filtered["LOAI_VIEC"] == filter_loai]

        

    if filter_tt != "Tất cả":

        df_filtered = df_filtered[df_filtered["TRANG_THAI_TONG"] == filter_tt]



    # =========================================================

    # 📋 HIỂN THỊ KẾT QUẢ

    # =========================================================

    st.markdown(f"**Tìm thấy: {len(df_filtered)} công việc**")



    if df_filtered.empty:

        st.info("Không có dữ liệu phù hợp.")

        return



    df_show = df_filtered.copy()

    

    # Map ID -> Tên hiển thị (Dùng lookup_display từ utils)

    if "NGUOI_NHAN" in df_show.columns: 

        df_show["NGUOI_NHAN"] = df_show["NGUOI_NHAN"].apply(lambda x: lookup_display(x, df_ns, "ID_NHAN_SU", ["HO_TEN"]))

    

    # Map ID -> Tên Dự án/Gói thầu/Hợp đồng

    if "IDDA_CV" in df_show.columns: df_show["DU_AN"] = df_show["IDDA_CV"].map(da_map).fillna("-")

    if "IDGT_CV" in df_show.columns: df_show["GOI_THAU"] = df_show["IDGT_CV"].map(gt_map).fillna("-")

    

    # Chọn cột hiển thị

    desired_cols = ["ID_CONG_VIEC", "TEN_VIEC", "NGUOI_NHAN", "HAN_CHOT", "TRANG_THAI_TONG", "DU_AN", "GOI_THAU", "LOAI_VIEC"]

    final_cols = [c for c in desired_cols if c in df_show.columns]



    # Format ngày và áp dụng màu sắc

    if "HAN_CHOT" in df_show.columns:

        df_show["HAN_CHOT"] = df_show["HAN_CHOT"].apply(lambda x: format_date_vn(x))



    st.dataframe(

        df_show[final_cols].style.applymap(highlight_status, subset=['TRANG_THAI_TONG']),

        use_container_width=True,

        hide_index=True

    )
