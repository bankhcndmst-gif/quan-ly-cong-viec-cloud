import streamlit as st
import pandas as pd
import io
from datetime import datetime

from gsheet import load_all_sheets
from utils import lookup_display, format_date_vn


def highlight_status(s):
    s_clean = str(s).strip().upper()
    if "HOÀN" in s_clean:
        return 'background-color: #d4edda; color: #155724'
    if "TRỄ" in s_clean or "TRE" in s_clean:
        return 'background-color: #f8d7da; color: #721c24'
    if "ĐANG" in s_clean or "DANG" in s_clean:
        return 'background-color: #ffeeba; color: #856404'
    return ''


def render_report_tab():
    st.header("📊 Báo cáo công việc")

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

    if "TRANG_THAI_TONG" not in df_cv.columns:
        st.error("Không tìm thấy cột 'TRANG_THAI_TONG' trong sheet 7_CONG_VIEC.")
        return

    with st.expander("🔍 Bộ lọc nâng cao", expanded=True):
        colA, colB = st.columns(2)
        date_from = colA.date_input("Từ ngày (NGAY_GIAO)", None)
        date_to = colB.date_input("Đến ngày (NGAY_GIAO)", None)

        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)

        da_map = dict(zip(df_da["ID_DU_AN"], df_da["TEN_DU_AN"])) if "ID_DU_AN" in df_da else {}
        list_da = ["Tất cả"] + list(da_map.values())

        gt_map = dict(zip(df_gt["ID_GOI_THAU"], df_gt["TEN_GOI_THAU"])) if "ID_GOI_THAU" in df_gt else {}
        list_gt = ["Tất cả"] + list(gt_map.values())

        hd_map = dict(zip(df_hd["ID_HOP_DONG"], df_hd["TEN_HD"])) if "ID_HOP_DONG" in df_hd else {}
        list_hd = ["Tất cả"] + list(hd_map.values())

        search_ten = col1.text_input("Tên công việc (Từ khóa)", "")
        filter_da = col2.selectbox("Dự án", list_da)
        filter_gt = col3.selectbox("Gói thầu", list_gt)
        filter_hd = col4.selectbox("Hợp đồng", list_hd)

        list_loai = ["Tất cả"] + list(df_cv["LOAI_VIEC"].dropna().unique()) if "LOAI_VIEC" in df_cv else ["Tất cả"]
        filter_loai = col5.selectbox("Loại việc", list_loai)

        list_tt = ["Tất cả"] + sorted(df_cv["TRANG_THAI_TONG"].dropna().astype(str).str.strip().unique())
        filter_tt = col6.selectbox("Trạng thái", list_tt)

    df_filtered = df_cv.copy()

    if "NGAY_GIAO" in df_filtered.columns:
        if date_from:
            df_filtered = df_filtered[df_filtered["NGAY_GIAO"] >= pd.to_datetime(date_from)]
        if date_to:
            df_filtered = df_filtered[df_filtered["NGAY_GIAO"] <= pd.to_datetime(date_to)]

    if search_ten and "TEN_VIEC" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["TEN_VIEC"].astype(str).str.contains(search_ten, case=False, na=False)]

    def find_id(map_dict, value):
        return [k for k, v in map_dict.items() if v == value]

    if filter_da != "Tất cả" and "IDDA_CV" in df_filtered.columns:
        ids = find_id(da_map, filter_da)
        if ids:
            df_filtered = df_filtered[df_filtered["IDDA_CV"] == ids[0]]

    if filter_gt != "Tất cả" and "IDGT_CV" in df_filtered.columns:
        ids = find_id(gt_map, filter_gt)
        if ids:
            df_filtered = df_filtered[df_filtered["IDGT_CV"] == ids[0]]

    if filter_hd != "Tất cả" and "IDHD_CV" in df_filtered.columns:
        ids = find_id(hd_map, filter_hd)
        if ids:
            df_filtered = df_filtered[df_filtered["IDHD_CV"] == ids[0]]

    if filter_loai != "Tất cả" and "LOAI_VIEC" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["LOAI_VIEC"] == filter_loai]

    if filter_tt != "Tất cả":
        df_filtered = df_filtered[df_filtered["TRANG_THAI_TONG"].astype(str).str.strip() == filter_tt]

    st.markdown(f"**Tìm thấy: {len(df_filtered)} công việc**")

    if df_filtered.empty:
        st.info("Không có dữ liệu phù hợp.")
        return

    df_show = df_filtered.copy()

    # Hiển thị tên nhân sự bên cạnh mã ID
    if not df_ns.empty:
        for col in ["NGUOI_GIAO", "NGUOI_NHAN", "NGUOI_PHOI_HOP"]:
            if col in df_show.columns:
                df_show[col + "_TEN"] = df_show[col].apply(
                    lambda x: lookup_display(x, df_ns, "ID_NHAN_SU", ["HO_TEN"])
                )

    if "IDDA_CV" in df_show.columns:
        df_show["DU_AN"] = df_show["IDDA_CV"].map(da_map).fillna("-")
    if "IDGT_CV" in df_show.columns:
        df_show["GOI_THAU"] = df_show["IDGT_CV"].map(gt_map).fillna("-")

    if "HAN_CHOT" in df_show.columns:
        df_show["HAN_CHOT"] = df_show["HAN_CHOT"].apply(lambda x: format_date_vn(x) if pd.notnull(x) else "-")
    if "NGAY_GIAO" in df_show.columns:
        df_show["NGAY_GIAO"] = df_show["NGAY_GIAO"].apply(lambda x: format_date_vn(x) if pd.notnull(x) else "-")

    desired_cols = [
        "ID_CONG_VIEC", "TEN_VIEC",
        "NGUOI_GIAO", "NGUOI_GIAO_TEN",
        "NGUOI_NHAN", "NGUOI_NHAN_TEN",
        "NGUOI_PHOI_HOP", "NGUOI_PHOI_HOP_TEN",
        "NGAY_GIAO", "HAN_CHOT",
        "TRANG_THAI_TONG", "DU_AN", "GOI_THAU", "LOAI_VIEC"
    ]
    final_cols = [c for c in desired_cols if c in df_show.columns]

    csv_data = df_show[final_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Tải CSV",
        data=csv_data,
        file_name="bao_cao_cong_viec.csv",
        mime="text/csv"
    )

    st.dataframe(
        df_show[final_cols].style.applymap(highlight_status, subset=['TRANG_THAI_TONG']),
        use_container_width=True,
        hide_index=True
    )
