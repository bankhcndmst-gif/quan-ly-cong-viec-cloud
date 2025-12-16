import streamlit as st
import pandas as pd
from datetime import datetime
from gsheet import load_all_sheets
from utils import lookup_display, format_date_vn

# =========================================================
# ✅ HÀM TÔ MÀU TRẠNG THÁI
# =========================================================
def highlight_status(s):
    s_clean = str(s).strip().upper()
    if s_clean == 'HOÀN THÀNH':
        return 'background-color: #d4edda; color: #155724'
    if s_clean == 'TRỄ HẠN':
        return 'background-color: #f8d7da; color: #721c24'
    if s_clean == 'ĐANG THỰC HIỆN':
        return 'background-color: #ffeeba; color: #856404'
    return ''

# =========================================================
# ✅ TÍNH TRẠNG THÁI CÔNG VIỆC
# =========================================================
def compute_status(row):
    trang_thai_goc = row.get("TRANG_THAI_TONG", "")
    han = row.get("HAN_CHOT")

    if str(trang_thai_goc).strip().upper() == "HOÀN THÀNH":
        return "Hoàn thành"

    if han and isinstance(han, pd.Timestamp):
        if han < pd.to_datetime(datetime.now().date()):
            return "Trễ hạn"

    return "Đang thực hiện"

# =========================================================
# 📤 XUẤT EXCEL
# =========================================================
def to_excel(df: pd.DataFrame):
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter", datetime_format="dd/mm/yyyy") as writer:
        df.to_excel(writer, index=False, sheet_name="Bao_cao_cong_viec")
    return output.getvalue()

# =========================================================
# ✅ TAB BÁO CÁO CÔNG VIỆC
# =========================================================
def render_report_tab():
    st.header("📊 Báo cáo công việc")

    # 1. Load dữ liệu
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
        st.warning("Chưa có dữ liệu công việc.")
        return

    # 2. Tính trạng thái
    df_cv["TRANG_THAI_TONG"] = df_cv.apply(compute_status, axis=1)

    # =========================================================
    # 🔍 BỘ LỌC
    # =========================================================
    with st.expander("🔍 Bộ lọc nâng cao", expanded=True):
        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)

        da_map = dict(zip(df_da["ID_DU_AN"], df_da["TEN_DU_AN"])) if set(["ID_DU_AN","TEN_DU_AN"]).issubset(df_da.columns) else {}
        gt_map = dict(zip(df_gt["ID_GOI_THAU"], df_gt["TEN_GOI_THAU"])) if set(["ID_GOI_THAU","TEN_GOI_THAU"]).issubset(df_gt.columns) else {}
        hd_map = dict(zip(df_hd["ID_HOP_DONG"], df_hd["TEN_HD"])) if set(["ID_HOP_DONG","TEN_HD"]).issubset(df_hd.columns) else {}

        search_ten = col1.text_input("Tên công việc (từ khóa)")
        filter_da = col2.selectbox("Dự án", ["Tất cả"] + list(da_map.values()))
        filter_gt = col3.selectbox("Gói thầu", ["Tất cả"] + list(gt_map.values()))
        filter_hd = col4.selectbox("Hợp đồng", ["Tất cả"] + list(hd_map.values()))

        if "LOAI_VIEC" in df_cv.columns:
            filter_loai = col5.selectbox("Loại việc", ["Tất cả"] + sorted(df_cv["LOAI_VIEC"].dropna().unique()))
        else:
            filter_loai = "Tất cả"

        # ✅ LẤY TRẠNG THÁI TỪ CỘT TRANG_THAI_TONG
        list_tt = ["Tất cả"] + sorted(
            df_cv["TRANG_THAI_TONG"].dropna().astype(str).str.strip().unique().tolist()
        )
        filter_tt = col6.selectbox("Trạng thái", list_tt)

        # ✅ LỌC THEO NGÀY GIAO
        col7, col8 = st.columns(2)
        from_date = col7.date_input("📅 Ngày giao từ", value=None)
        to_date = col8.date_input("📅 Ngày giao đến", value=None)

    # =========================================================
    # ⚙️ ÁP DỤNG LỌC
    # =========================================================
    df_filtered = df_cv.copy()

    if search_ten and "TEN_VIEC" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["TEN_VIEC"].astype(str).str.contains(search_ten, case=False, na=False)]

    def find_id(map_dict, val):
        return [k for k, v in map_dict.items() if v == val]

    if filter_da != "Tất cả" and "IDDA_CV" in df_filtered.columns:
        ids = find_id(da_map, filter_da)
        if ids: df_filtered = df_filtered[df_filtered["IDDA_CV"] == ids[0]]

    if filter_gt != "Tất cả" and "IDGT_CV" in df_filtered.columns:
        ids = find_id(gt_map, filter_gt)
        if ids: df_filtered = df_filtered[df_filtered["IDGT_CV"] == ids[0]]

    if filter_hd != "Tất cả" and "IDHD_CV" in df_filtered.columns:
        ids = find_id(hd_map, filter_hd)
        if ids: df_filtered = df_filtered[df_filtered["IDHD_CV"] == ids[0]]

    if filter_loai != "Tất cả" and "LOAI_VIEC" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["LOAI_VIEC"] == filter_loai]

    if filter_tt != "Tất cả":
        df_filtered = df_filtered[df_filtered["TRANG_THAI_TONG"] == filter_tt]

    if "NGAY_GIAO" in df_filtered.columns:
        df_filtered["NGAY_GIAO"] = pd.to_datetime(df_filtered["NGAY_GIAO"], errors="coerce")
        if from_date:
            df_filtered = df_filtered[df_filtered["NGAY_GIAO"] >= pd.to_datetime(from_date)]
        if to_date:
            df_filtered = df_filtered[df_filtered["NGAY_GIAO"] <= pd.to_datetime(to_date)]

    # =========================================================
    # 📋 HIỂN THỊ
    # =========================================================
    st.markdown(f"**Tìm thấy: {len(df_filtered)} công việc**")

    if df_filtered.empty:
        st.info("Không có dữ liệu phù hợp.")
        return

    df_show = df_filtered.copy()

    if "NGUOI_NHAN" in df_show.columns:
        df_show["NGUOI_NHAN"] = df_show["NGUOI_NHAN"].apply(
            lambda x: lookup_display(x, df_ns, "ID_NHAN_SU", ["HO_TEN"])
        )

    if "IDDA_CV" in df_show.columns:
        df_show["DU_AN"] = df_show["IDDA_CV"].map(da_map).fillna("-")
    if "IDGT_CV" in df_show.columns:
        df_show["GOI_THAU"] = df_show["IDGT_CV"].map(gt_map).fillna("-")

    final_cols = [
        c for c in [
            "ID_CONG_VIEC", "TEN_VIEC", "NGUOI_NHAN",
            "NGAY_GIAO", "HAN_CHOT", "TRANG_THAI_TONG",
            "DU_AN", "GOI_THAU", "LOAI_VIEC"
        ] if c in df_show.columns
    ]

    if "NGAY_GIAO" in df_show.columns:
        df_show["NGAY_GIAO"] = df_show["NGAY_GIAO"].apply(format_date_vn)
    if "HAN_CHOT" in df_show.columns:
        df_show["HAN_CHOT"] = df_show["HAN_CHOT"].apply(format_date_vn)

    # 📤 NÚT XUẤT EXCEL
    st.download_button(
        label="📥 Xuất Excel",
        data=to_excel(df_show[final_cols]),
        file_name=f"bao_cao_cong_viec_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.dataframe(
        df_show[final_cols].style.applymap(
            highlight_status, subset=["TRANG_THAI_TONG"]
        ),
        use_container_width=True,
        hide_index=True
    )
