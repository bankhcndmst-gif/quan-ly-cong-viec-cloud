import streamlit as st
import pandas as pd
from datetime import datetime
from gsheet import load_all_sheets
from utils import format_date_vn, get_unique_list, lookup_display

# =========================================================
# ✅ TÍNH TRẠNG THÁI CÔNG VIỆC
# =========================================================
def compute_status(row):
    trang_thai_goc = row.get("TRANG_THAI", "")
    ngay_xong = row.get("NGAY_THUC_TE_XONG")
    han = row.get("HAN_CHOT")

    # 1. Nếu đã xong thực tế hoặc trạng thái gốc là Hoàn thành
    if ngay_xong or trang_thai_goc == "Hoàn thành":
        return "Hoàn thành"

    # 2. Nếu chưa xong mà quá hạn
    if han and isinstance(han, datetime) and han < datetime.now():
        return "Trễ hạn"

    # 3. Còn lại
    return "Đang thực hiện"

# =========================================================
# ✅ TAB BÁO CÁO CÔNG VIỆC (NÂNG CẤP)
# =========================================================
def render_report_tab():
    st.header("📊 Báo cáo công việc")

    # 1. Tải dữ liệu
    all_sheets = load_all_sheets()
    df_cv = all_sheets["7_CONG_VIEC"].copy()
    
    # Tải các bảng liên quan để lấy tên
    df_ns = all_sheets["1_NHAN_SU"]
    df_da = all_sheets["4_DU_AN"]
    df_gt = all_sheets["5_GOI_THAU"]
    df_hd = all_sheets["6_HOP_DONG"]

    if df_cv.empty:
        st.warning("Chưa có dữ liệu công việc.")
        return

    # 2. Tính toán trạng thái tự động
    # Cần đảm bảo cột HAN_CHOT là datetime để so sánh
    if "HAN_CHOT" in df_cv.columns:
        df_cv["HAN_CHOT"] = pd.to_datetime(df_cv["HAN_CHOT"], errors='coerce', dayfirst=True)
    
    df_cv["TRANG_THAI_TONG"] = df_cv.apply(compute_status, axis=1)

    # =========================================================
    # 🔍 KHU VỰC BỘ LỌC (FILTER)
    # =========================================================
    with st.expander("🔍 Bộ lọc nâng cao", expanded=True):
        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)
        
        # --- Hàng 1 ---
        # 1. Tên việc (Tìm kiếm)
        search_ten = col1.text_input("Tên công việc (Từ khóa)", "")

        # 2. Dự án (TEN_DU_AN)
        # Tạo map ID -> Tên
        da_map = dict(zip(df_da["ID_DU_AN"], df_da["TEN_DU_AN"]))
        list_da = ["Tất cả"] + list(df_da["TEN_DU_AN"].unique())
        filter_da = col2.selectbox("Dự án", list_da)

        # 3. Gói thầu (TEN_GOI_THAU)
        gt_map = dict(zip(df_gt["ID_GOI_THAU"], df_gt["TEN_GOI_THAU"]))
        list_gt = ["Tất cả"] + list(df_gt["TEN_GOI_THAU"].unique())
        filter_gt = col3.selectbox("Gói thầu", list_gt)

        # --- Hàng 2 ---
        # 4. Hợp đồng (TEN_HD)
        hd_map = dict(zip(df_hd["ID_HOP_DONG"], df_hd["TEN_HD"]))
        list_hd = ["Tất cả"] + list(df_hd["TEN_HD"].unique())
        filter_hd = col4.selectbox("Hợp đồng", list_hd)

        # 5. Loại việc (LOAI_VIEC)
        # Kiểm tra xem cột LOAI_VIEC có trong sheet chưa, nếu chưa thì bỏ qua
        if "LOAI_VIEC" in df_cv.columns:
            list_loai = ["Tất cả"] + list(df_cv["LOAI_VIEC"].unique())
            filter_loai = col5.selectbox("Loại việc", list_loai)
        else:
            filter_loai = "Tất cả"
            col5.info("Chưa có cột LOAI_VIEC")

        # 6. Trạng thái tổng (TRANG_THAI_TONG)
        list_tt = ["Tất cả", "Đang thực hiện", "Trễ hạn", "Hoàn thành"]
        filter_tt = col6.selectbox("Trạng thái", list_tt)

    # =========================================================
    # ⚙️ XỬ LÝ LỌC
    # =========================================================
    df_filtered = df_cv.copy()

    # Lọc Tên việc
    if search_ten:
        df_filtered = df_filtered[df_filtered["TEN_VIEC"].str.contains(search_ten, case=False, na=False)]

    # Lọc Dự án (Tìm ID ứng với Tên đã chọn)
    if filter_da != "Tất cả":
        # Lấy ID của tên dự án đã chọn
        selected_id_da = df_da[df_da["TEN_DU_AN"] == filter_da]["ID_DU_AN"].values
        if len(selected_id_da) > 0:
            df_filtered = df_filtered[df_filtered["IDDA_CV"] == selected_id_da[0]]

    # Lọc Gói thầu
    if filter_gt != "Tất cả":
        selected_id_gt = df_gt[df_gt["TEN_GOI_THAU"] == filter_gt]["ID_GOI_THAU"].values
        if len(selected_id_gt) > 0:
            df_filtered = df_filtered[df_filtered["IDGT_CV"] == selected_id_gt[0]]

    # Lọc Hợp đồng
    if filter_hd != "Tất cả":
        selected_id_hd = df_hd[df_hd["TEN_HD"] == filter_hd]["ID_HOP_DONG"].values
        if len(selected_id_hd) > 0:
            df_filtered = df_filtered[df_filtered["IDHD_CV"] == selected_id_hd[0]]
            
    # Lọc Loại việc
    if filter_loai != "Tất cả" and "LOAI_VIEC" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["LOAI_VIEC"] == filter_loai]

    # Lọc Trạng thái
    if filter_tt != "Tất cả":
        df_filtered = df_filtered[df_filtered["TRANG_THAI_TONG"] == filter_tt]

    # =========================================================
    # 📋 HIỂN THỊ KẾT QUẢ
    # =========================================================
    st.markdown(f"**Tìm thấy: {len(df_filtered)} công việc**")
    
    if df_filtered.empty:
        st.info("Không có dữ liệu phù hợp.")
        return

    # Chuẩn bị bảng hiển thị đẹp
    df_show = df_filtered.copy()
    
    # Map ID sang Tên để hiển thị
    df_show["NGUOI_NHAN"] = df_show["NGUOI_NHAN"].apply(lambda x: lookup_display(x, df_ns, "ID_NHAN_SU", ["HO_TEN"]))
    df_show["DU_AN"] = df_show["IDDA_CV"].map(da_map).fillna("-")
    df_show["GOI_THAU"] = df_show["IDGT_CV"].map(gt_map).fillna("-")
    
    # Chọn các cột cần hiện
    cols_to_show = ["ID_CONG_VIEC", "TEN_VIEC", "NGUOI_NHAN", "HAN_CHOT", "TRANG_THAI_TONG", "DU_AN", "GOI_THAU"]
    if "LOAI_VIEC" in df_show.columns:
        cols_to_show.append("LOAI_VIEC")

    # Format ngày tháng lại cho đẹp (vì ở trên đã chuyển sang datetime để tính toán)
    if "HAN_CHOT" in df_show.columns:
        df_show["HAN_CHOT"] = df_show["HAN_CHOT"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")

    st.dataframe(
        df_show[cols_to_show], 
        use_container_width=True,
        hide_index=True
    )
