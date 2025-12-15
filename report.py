import streamlit as st
import pandas as pd
from datetime import datetime
from gsheet import load_all_sheets
from utils import (
    format_date_vn,
    get_unique_list,
    lookup_display,
)
from config import LINK_CONFIG_RAW


# =========================================================
# ✅ TÍNH TRẠNG THÁI CÔNG VIỆC
# =========================================================
def compute_status(row):
    han = row.get("HAN_CHOT")
    ngay_xong = row.get("NGAY_THUC_TE_XONG")

    if ngay_xong:
        return "Hoàn thành"

    if han and han < datetime.now():
        return "Trễ hạn"

    return "Đang thực hiện"


# =========================================================
# ✅ TAB BÁO CÁO CÔNG VIỆC
# =========================================================
def render_report_tab():
    st.header("📊 Báo cáo công việc")

    # -----------------------------------------------------
    # ✅ Tải dữ liệu
    # -----------------------------------------------------
    all_sheets = load_all_sheets()
    df = all_sheets["7_CONG_VIEC"].copy()

    if df.empty:
        st.warning("Chưa có dữ liệu công việc.")
        return

    # -----------------------------------------------------
    # ✅ Tính trạng thái tự động
    # -----------------------------------------------------
    df["TRANG_THAI_TINH"] = df.apply(compute_status, axis=1)

    # -----------------------------------------------------
    # ✅ Bộ lọc
    # -----------------------------------------------------
    st.subheader("🔍 Bộ lọc")

    col1, col2, col3 = st.columns(3)

    # Lọc theo người nhận
    df_ns = all_sheets["1_NHAN_SU"]
    list_ns = get_unique_list(df_ns, "HO_TEN", prefix="Tất cả")
    nguoi_nhan = col1.selectbox("Người nhận", list_ns)

    # Lọc theo đơn vị
    df_dv = all_sheets["2_DON_VI"]
    list_dv = get_unique_list(df_dv, "TEN_DON_VI", prefix="Tất cả")
    don_vi = col2.selectbox("Đơn vị", list_dv)

    # Lọc theo trạng thái
    list_tt = ["Tất cả", "Đang thực hiện", "Trễ hạn", "Hoàn thành"]
    trang_thai = col3.selectbox("Trạng thái", list_tt)

    # -----------------------------------------------------
    # ✅ Lọc theo ngày
    # -----------------------------------------------------
    st.subheader("📅 Lọc theo thời gian")

    col4, col5 = st.columns(2)
    tu_ngay = col4.date_input("Từ ngày", value=None)
    den_ngay = col5.date_input("Đến ngày", value=None)

    # -----------------------------------------------------
    # ✅ Áp dụng bộ lọc
    # -----------------------------------------------------
    df_filtered = df.copy()

    # Lọc theo người nhận
    if nguoi_nhan != "Tất cả":
        id_ns = df_ns[df_ns["HO_TEN"] == nguoi_nhan]["ID_NHAN_SU"].values
        if len(id_ns) > 0:
            df_filtered = df_filtered[df_filtered["NGUOI_NHAN"] == id_ns[0]]

    # Lọc theo đơn vị
    if don_vi != "Tất cả":
        id_dv = df_dv[df_dv["TEN_DON_VI"] == don_vi]["ID_DON_VI"].values
        if len(id_dv) > 0:
            df_filtered = df_filtered[df_filtered["IDDV_CV"] == id_dv[0]]

    # Lọc theo trạng thái
    if trang_thai != "Tất cả":
        df_filtered = df_filtered[df_filtered["TRANG_THAI_TINH"] == trang_thai]

    # Lọc theo ngày giao
    if tu_ngay:
        df_filtered = df_filtered[df_filtered["NGAY_GIAO"] >= datetime.combine(tu_ngay, datetime.min.time())]

    if den_ngay:
        df_filtered = df_filtered[df_filtered["NGAY_GIAO"] <= datetime.combine(den_ngay, datetime.max.time())]

    # -----------------------------------------------------
    # ✅ Hiển thị kết quả
    # -----------------------------------------------------
    st.subheader("📄 Kết quả lọc")

    if df_filtered.empty:
        st.warning("Không có công việc phù hợp.")
        return

    # -----------------------------------------------------
    # ✅ Thay ID bằng mô tả để dễ đọc
    # -----------------------------------------------------
    df_show = df_filtered.copy()

    # Người giao / nhận
    df_show["NGUOI_GIAO"] = df_show["NGUOI_GIAO"].apply(
        lambda x: lookup_display(x, df_ns, "ID_NHAN_SU", ["HO_TEN", "CHUC_VU"])
    )
    df_show["NGUOI_NHAN"] = df_show["NGUOI_NHAN"].apply(
        lambda x: lookup_display(x, df_ns, "ID_NHAN_SU", ["HO_TEN", "CHUC_VU"])
    )

    # Đơn vị
    df_show["IDDV_CV"] = df_show["IDDV_CV"].apply(
        lambda x: lookup_display(x, df_dv, "ID_DON_VI", ["TEN_DON_VI"])
    )

    # Dự án
    df_da = all_sheets["4_DU_AN"]
    df_show["IDDA_CV"] = df_show["IDDA_CV"].apply(
        lambda x: lookup_display(x, df_da, "ID_DU_AN", ["TEN_DU_AN"])
    )

    # Gói thầu
    df_gt = all_sheets["5_GOI_THAU"]
    df_show["IDGT_CV"] = df_show["IDGT_CV"].apply(
        lambda x: lookup_display(x, df_gt, "ID_GOI_THAU", ["TEN_GOI_THAU"])
    )

    # Hợp đồng
    df_hd = all_sheets["6_HOP_DONG"]
    df_show["IDHD_CV"] = df_show["IDHD_CV"].apply(
        lambda x: lookup_display(x, df_hd, "ID_HOP_DONG", ["TEN_HD"])
    )

    # Văn bản
    df_vb = all_sheets["3_VAN_BAN"]
    df_show["IDVB_VAN_BAN"] = df_show["IDVB_VAN_BAN"].apply(
        lambda x: lookup_display(x, df_vb, "ID_VB", ["SO_VAN_BAN"])
    )

    # Format ngày
    for col in ["NGAY_GIAO", "HAN_CHOT", "NGAY_THUC_TE_XONG"]:
        if col in df_show.columns:
            df_show[col] = df_show[col].apply(format_date_vn)

    st.dataframe(df_show, use_container_width=True)

    # -----------------------------------------------------
    # ✅ Thống kê tổng hợp
    # -----------------------------------------------------
    st.subheader("📌 Thống kê")

    tong = len(df_filtered)
    hoan_thanh = len(df_filtered[df_filtered["TRANG_THAI_TINH"] == "Hoàn thành"])
    tre_han = len(df_filtered[df_filtered["TRANG_THAI_TINH"] == "Trễ hạn"])
    dang_lam = len(df_filtered[df_filtered["TRANG_THAI_TINH"] == "Đang thực hiện"])

    st.write(f"- Tổng số công việc: **{tong}**")
    st.write(f"- ✅ Hoàn thành: **{hoan_thanh}**")
    st.write(f"- ⚠️ Trễ hạn: **{tre_han}**")
    st.write(f"- 🔄 Đang thực hiện: **{dang_lam}**")
