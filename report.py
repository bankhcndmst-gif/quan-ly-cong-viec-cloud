import streamlit as st
import pandas as pd
from datetime import datetime
from gsheet import load_all_sheets
from utils import lookup_display

# =========================================================
# ✅ TÍNH TRẠNG THÁI CÔNG VIỆC
# =========================================================
def compute_status(row):
    trang_thai_goc = row.get("TRANG_THAI", "")
    ngay_xong = row.get("NGAY_THUC_TE_XONG")
    han = row.get("HAN_CHOT")

    # 1. Nếu đã xong
    if ngay_xong or str(trang_thai_goc) == "Hoàn thành":
        return "Hoàn thành"

    # 2. Nếu quá hạn (Chỉ tính nếu có hạn chót hợp lệ)
    if han and isinstance(han, datetime) and han < datetime.now():
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

    # 2. Xử lý dữ liệu ngày tháng
    if "HAN_CHOT" in df_cv.columns:
        df_cv["HAN_CHOT"] = pd.to_datetime(df_cv["HAN_CHOT"], errors='coerce', dayfirst=True)
    
    # Tính trạng thái
    df_cv["TRANG_THAI_TONG"] = df_cv.apply(compute_status, axis=1)

    # =========================================================
    # 🔍 KHU VỰC BỘ LỌC (FILTER) - XỬ LÝ AN TOÀN
    # =========================================================
    with st.expander("🔍 Bộ lọc nâng cao", expanded=True):
        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)
        
        # --- Lấy dữ liệu cho Filter (Chống lỗi thiếu cột) ---
        
        # 1. Dự án
        da_map = {}
        list_da = ["Tất cả"]
        if "ID_DU_AN" in df_da.columns and "TEN_DU_AN" in df_da.columns:
            da_map = dict(zip(df_da["ID_DU_AN"], df_da["TEN_DU_AN"]))
            list_da += list(df_da["TEN_DU_AN"].unique())
        
        # 2. Gói thầu
        gt_map = {}
        list_gt = ["Tất cả"]
        if "ID_GOI_THAU" in df_gt.columns and "TEN_GOI_THAU" in df_gt.columns:
            gt_map = dict(zip(df_gt["ID_GOI_THAU"], df_gt["TEN_GOI_THAU"]))
            list_gt += list(df_gt["TEN_GOI_THAU"].unique())

        # 3. Hợp đồng (Nguyên nhân gây lỗi của bạn nằm ở đây)
        hd_map = {}
        list_hd = ["Tất cả"]
        if "ID_HOP_DONG" in df_hd.columns and "TEN_HD" in df_hd.columns:
            hd_map = dict(zip(df_hd["ID_HOP_DONG"], df_hd["TEN_HD"]))
            list_hd += list(df_hd["TEN_HD"].unique())

        # --- Hiển thị Filter ---
        search_ten = col1.text_input("Tên công việc (Từ khóa)", "")
        filter_da = col2.selectbox("Dự án", list_da)
        filter_gt = col3.selectbox("Gói thầu", list_gt)
        filter_hd = col4.selectbox("Hợp đồng", list_hd)

        # Loại việc
        if "LOAI_VIEC" in df_cv.columns:
            list_loai = ["Tất cả"] + list(df_cv["LOAI_VIEC"].dropna().unique())
            filter_loai = col5.selectbox("Loại việc", list_loai)
        else:
            filter_loai = "Tất cả"
            # Không báo lỗi, chỉ ẩn đi hoặc hiện text mờ
            
        # Trạng thái
        list_tt = ["Tất cả", "Đang thực hiện", "Trễ hạn", "Hoàn thành"]
        filter_tt = col6.selectbox("Trạng thái", list_tt)

    # =========================================================
    # ⚙️ XỬ LÝ LỌC
    # =========================================================
    df_filtered = df_cv.copy()

    # Lọc tên
    if search_ten and "TEN_VIEC" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["TEN_VIEC"].astype(str).str.contains(search_ten, case=False, na=False)]

    # Lọc Dự án
    if filter_da != "Tất cả" and "IDDA_CV" in df_filtered.columns:
        selected_id = [k for k, v in da_map.items() if v == filter_da]
        if selected_id:
            df_filtered = df_filtered[df_filtered["IDDA_CV"] == selected_id[0]]

    # Lọc Gói thầu
    if filter_gt != "Tất cả" and "IDGT_CV" in df_filtered.columns:
        selected_id = [k for k, v in gt_map.items() if v == filter_gt]
        if selected_id:
            df_filtered = df_filtered[df_filtered["IDGT_CV"] == selected_id[0]]

    # Lọc Hợp đồng
    if filter_hd != "Tất cả" and "IDHD_CV" in df_filtered.columns:
        selected_id = [k for k, v in hd_map.items() if v == filter_hd]
        if selected_id:
            df_filtered = df_filtered[df_filtered["IDHD_CV"] == selected_id[0]]

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
    
    # Map tên người nhận (nếu có cột)
    if "NGUOI_NHAN" in df_show.columns:
        df_show["NGUOI_NHAN"] = df_show["NGUOI_NHAN"].apply(lambda x: lookup_display(x, df_ns, "ID_NHAN_SU", ["HO_TEN"]))
    
    # Map tên dự án/hợp đồng vào bảng hiển thị
    if "IDDA_CV" in df_show.columns: df_show["DU_AN"] = df_show["IDDA_CV"].map(da_map).fillna("-")
    if "IDGT_CV" in df_show.columns: df_show["GOI_THAU"] = df_show["IDGT_CV"].map(gt_map).fillna("-")
    
    # Chọn cột hiển thị (Chỉ hiện cột nào thực sự tồn tại)
    desired_cols = ["ID_CONG_VIEC", "TEN_VIEC", "NGUOI_NHAN", "HAN_CHOT", "TRANG_THAI_TONG", "DU_AN", "GOI_THAU", "LOAI_VIEC"]
    final_cols = [c for c in desired_cols if c in df_show.columns]

    # Format ngày
    if "HAN_CHOT" in df_show.columns:
        df_show["HAN_CHOT"] = df_show["HAN_CHOT"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")

    st.dataframe(df_show[final_cols], use_container_width=True, hide_index=True)
