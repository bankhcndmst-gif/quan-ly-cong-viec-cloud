# =========================================================
# NEW_TASK.PY — TAB GIAO VIỆC MỚI (22 CỘT + MÔ TẢ)
# =========================================================

import streamlit as st
from datetime import datetime, timedelta

from utils import (
    get_display_list_multi,
    lookup_display,
    get_unique_list   # ✅ thêm dòng này
)

from gsheet import connect_gsheet
import pandas as pd


# ---------------------------------------------------------
# HÀM THÊM CÔNG VIỆC MỚI VÀO GOOGLE SHEET
# ---------------------------------------------------------
def append_new_work(new_data: dict, df_cv: pd.DataFrame, all_sheets: dict):
    """
    Thêm 1 công việc mới vào Sheet 7_CONG_VIEC.
    Tự động sinh ID + mô tả liên kết.
    """

    # Tạo ID mới
    if not df_cv.empty and "ID_CONG_VIEC" in df_cv.columns:
        max_id_num = (
            df_cv["ID_CONG_VIEC"]
            .str.extract(r"(\d+)")
            .astype(float)
            .max()
            .iloc[0]
        )
    else:
        max_id_num = None

    new_id_num = int(max_id_num) + 1 if max_id_num is not None else 1
    new_id = f"CV{new_id_num:03d}"

    # Lấy bảng gốc
    df_ns = all_sheets["1_NHAN_SU"]
    df_dv = all_sheets["2_DON_VI"]
    df_da = all_sheets["4_DU_AN"]
    df_gt = all_sheets["5_GOI_THAU"]
    df_hd = all_sheets["6_HOP_DONG"]
    df_vb = all_sheets["3_VAN_BAN"]

    # Kết nối Google Sheets
    try:
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
        ws_cv = sh.worksheet("7_CONG_VIEC")

        header = ws_cv.row_values(1)

        # Tạo dòng dữ liệu mới
        new_row_dict = {
            "ID_CONG_VIEC": new_id,
            "TEN_VIEC": new_data.get("ten_viec", ""),
            "NOI_DUNG": new_data.get("noi_dung", ""),
            "LOAI_VIEC": new_data.get("loai_viec", ""),
            "NGUON_GIAO_VIEC": new_data.get("nguon_giao_viec", ""),
            "NGUOI_GIAO": new_data.get("nguoi_giao", ""),
            "NGUOI_NHAN": new_data.get("nguoi_nhan", ""),
            "NGAY_GIAO": new_data.get("ngay_giao").strftime("%Y-%m-%d"),
            "HAN_CHOT": new_data.get("han_chot").strftime("%Y-%m-%d"),
            "NGUOI_PHOI_HOP": new_data.get("nguoi_phoi_hop", ""),
            "TRANG_THAI_TONG": new_data.get("trang_thai_tong", ""),
            "TRANG_THAI_CHI_TIET": new_data.get("trang_thai_chi_tiet", ""),
            "NGAY_THUC_TE_XONG": (
                new_data.get("ngay_thuc_te_xong").strftime("%Y-%m-%d")
                if new_data.get("ngay_thuc_te_xong") else ""
            ),
            "IDVB_VAN_BAN": new_data.get("idvb_van_ban", ""),
            "IDHD_CV": new_data.get("idhd_cv", ""),
            "IDDA_CV": new_data.get("idda_cv", ""),
            "IDGT_CV": new_data.get("idgt_cv", ""),
            "VUONG_MAC": new_data.get("vuong_mac", ""),
            "DE_XUAT": new_data.get("de_xuat", ""),
            "IDDV_CV": new_data.get("iddv_cv", ""),
            "GHI_CHU_CV": new_data.get("ghi_chu_cv", ""),
        }

        # ---------------------------------------------------------
        # THÊM CÁC CỘT MÔ TẢ TỰ ĐỘNG
        # ---------------------------------------------------------
        new_row_dict["TEN_NGUOI_NHAN_MO_TA"] = lookup_display(
            new_row_dict["NGUOI_NHAN"], df_ns, "ID_NHAN_SU",
            ["HO_TEN", "CHUC_VU", "DIEN_THOAI"]
        )
        new_row_dict["TEN_NGUOI_GIAO_MO_TA"] = lookup_display(
            new_row_dict["NGUOI_GIAO"], df_ns, "ID_NHAN_SU",
            ["HO_TEN", "CHUC_VU", "DIEN_THOAI"]
        )
        new_row_dict["TEN_DON_VI_MO_TA"] = lookup_display(
            new_row_dict["IDDV_CV"], df_dv, "ID_DON_VI",
            ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"]
        )
        new_row_dict["TEN_DU_AN_MO_TA"] = lookup_display(
            new_row_dict["IDDA_CV"], df_da, "ID_DU_AN",
            ["TEN_DU_AN", "MO_TA", "NGAY_BD"]
        )
        new_row_dict["TEN_GOI_THAU_MO_TA"] = lookup_display(
            new_row_dict["IDGT_CV"], df_gt, "ID_GOI_THAU",
            ["TEN_GOI_THAU", "GIA_TRI", "NGAY_BD"]
        )
        new_row_dict["TEN_HOP_DONG_MO_TA"] = lookup_display(
            new_row_dict["IDHD_CV"], df_hd, "ID_HOP_DONG",
            ["SO_HD", "TEN_HD", "NGAY_KY"]
        )
        new_row_dict["SO_VAN_BAN_MO_TA"] = lookup_display(
            new_row_dict["IDVB_VAN_BAN"], df_vb, "ID_VB",
            ["SO_VAN_BAN", "NGAY_BAN_HANH", "TRICH_YEU"]
        )

        # ---------------------------------------------------------
        # GHI DỮ LIỆU VÀO GOOGLE SHEET
        # ---------------------------------------------------------
        values_to_append = [new_row_dict.get(h, "") for h in header]
        ws_cv.append_row(values_to_append, value_input_option="USER_ENTERED")

        st.success(f"🎉 Đã thêm công việc mới: **{new_id} - {new_data.get('ten_viec', '')}**")
        st.cache_data.clear()
        st.rerun()

    except Exception as e:
        st.error(f"❌ Lỗi khi ghi vào Google Sheet 7_CONG_VIEC: {e}")


# ---------------------------------------------------------
# TAB GIAO VIỆC MỚI
# ---------------------------------------------------------
def render_new_task_tab(all_sheets, df_cv, df_ns, df_dv):
    st.header("📝 Giao Công Việc Mới (Sheet 7_CONG_VIEC)")

    df_da = all_sheets["4_DU_AN"]
    df_gt = all_sheets["5_GOI_THAU"]
    df_hd = all_sheets["6_HOP_DONG"]
    df_vb = all_sheets["3_VAN_BAN"]

    # Danh sách hiển thị mô tả (không có ID)
    list_ns_display, map_ns = get_display_list_multi(
        df_ns, "ID_NHAN_SU", ["HO_TEN", "CHUC_VU", "DIEN_THOAI"], prefix="Chọn người"
    )
    list_dv_display, map_dv = get_display_list_multi(
        df_dv, "ID_DON_VI", ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"], prefix="Chọn đơn vị"
    )
    list_da_display, map_da = get_display_list_multi(
        df_da, "ID_DU_AN", ["TEN_DU_AN", "MO_TA", "NGAY_BD"], prefix="Tất cả"
    )
    list_gt_display, map_gt = get_display_list_multi(
        df_gt, "ID_GOI_THAU", ["TEN_GOI_THAU", "GIA_TRI", "NGAY_BD"], prefix="Tất cả"
    )
    list_hd_display, map_hd = get_display_list_multi(
        df_hd, "ID_HOP_DONG", ["TEN_HD", "SO_HD", "NGAY_KY"], prefix="Tất cả"
    )
    list_vb_display, map_vb = get_display_list_multi(
        df_vb, "ID_VB", ["SO_VAN_BAN", "NGAY_BAN_HANH", "TRICH_YEU"], prefix="Tất cả"
    )

    list_trang_thai = get_unique_list(df_cv, "TRANG_THAI_TONG", prefix="Chọn trạng thái")
    list_loai_viec = get_unique_list(df_cv, "LOAI_VIEC", prefix="Chọn loại việc")

    # ---------------------------------------------------------
    # FORM GIAO VIỆC
    # ---------------------------------------------------------
    with st.form("form_new_work_full"):
        st.subheader("A. Thông tin chính")

        colA1, colA2 = st.columns(2)
        with colA1:
            ten_viec = st.text_input("Tên công việc *")
            loai_viec = st.selectbox("Loại công việc", list_loai_viec)
            nguon_giao_viec = st.text_input("Nguồn giao việc (Văn bản, email, họp...)")
            nguoi_giao_display = st.selectbox("Người giao", list_ns_display)
            ngay_giao = st.date_input("Ngày giao", datetime.now().date())

        with colA2:
            noi_dung = st.text_area("Nội dung chi tiết")
            nguoi_nhan_display = st.selectbox("Người nhận *", list_ns_display)
            han_chot = st.date_input("Hạn chót", datetime.now().date() + timedelta(days=7))
            trang_thai_tong = st.selectbox("Trạng thái tổng", list_trang_thai)
            trang_thai_chi_tiet = st.text_input("Trạng thái chi tiết")

        da_xong = st.checkbox("Đã hoàn thành?")
        ngay_thuc_te_xong = (
            st.date_input("Ngày thực tế hoàn thành", datetime.now().date())
            if da_xong else None
        )

        st.markdown("---")
        st.subheader("B. Liên kết & thông tin bổ sung")

        colB1, colB2, colB3 = st.columns(3)
        with colB1:
            idvb_display = st.selectbox("Văn bản (IDVB_VAN_BAN)", list_vb_display)
            idda_display = st.selectbox("Dự án (IDDA_CV)", list_da_display)
            iddv_display = st.selectbox("Đơn vị (IDDV_CV)", list_dv_display)

        with colB2:
            idhd_display = st.selectbox("Hợp đồng (IDHD_CV)", list_hd_display)
            idgt_display = st.selectbox("Gói thầu (IDGT_CV)", list_gt_display)
            nguoi_phoi_hop = st.text_input("Người phối hợp (ghi ID hoặc mô tả)")

        with colB3:
            vuong_mac = st.text_area("Vướng mắc")
            de_xuat = st.text_area("Đề xuất")
            ghi_chu_cv = st.text_area("Ghi chú công việc")

        submitted = st.form_submit_button("✅ LƯU VÀ GIAO VIỆC MỚI", type="primary")

        # ---------------------------------------------------------
        # XỬ LÝ LƯU DỮ LIỆU
        # ---------------------------------------------------------
        if submitted:
            if not ten_viec or nguoi_nhan_display == "Chọn người":
                st.error("⚠️ Vui lòng nhập Tên công việc và chọn Người nhận hợp lệ.")
            else:
                id_nguoi_giao = map_ns.get(nguoi_giao_display, "")
                id_nguoi_nhan = map_ns.get(nguoi_nhan_display, "")
                id_dv = map_dv.get(iddv_display, "")
                id_da = map_da.get(idda_display, "") if idda_display != "Tất cả" else ""
                id_gt = map_gt.get(idgt_display, "") if idgt_display != "Tất cả" else ""
                id_hd = map_hd.get(idhd_display, "") if idhd_display != "Tất cả" else ""
                id_vb = map_vb.get(idvb_display, "") if idvb_display != "Tất cả" else ""

                new_data = {
                    "ten_viec": ten_viec,
                    "noi_dung": noi_dung,
                    "loai_viec": loai_viec,
                    "nguon_giao_viec": nguon_giao_viec,
                    "nguoi_giao": id_nguoi_giao,
                    "nguoi_nhan": id_nguoi_nhan,
                    "ngay_giao": ngay_giao,
                    "han_chot": han_chot,
                    "nguoi_phoi_hop": nguoi_phoi_hop,
                    "trang_thai_tong": trang_thai_tong,
                    "trang_thai_chi_tiet": trang_thai_chi_tiet,
                    "ngay_thuc_te_xong": ngay_thuc_te_xong,
                    "idvb_van_ban": id_vb,
                    "idhd_cv": id_hd,
                    "idda_cv": id_da,
                    "idgt_cv": id_gt,
                    "iddv_cv": id_dv,
                    "vuong_mac": vuong_mac,
                    "de_xuat": de_xuat,
                    "ghi_chu_cv": ghi_chu_cv,
                }

                append_new_work(new_data, df_cv, all_sheets)
