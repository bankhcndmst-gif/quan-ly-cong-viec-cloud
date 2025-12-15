import streamlit as st
import pandas as pd
from datetime import datetime
from gsheet import load_all_sheets, save_raw_sheet
from utils import get_display_list_multi
from config import LINK_CONFIG_RAW, DATE_COLS


# =========================================================
# ✅ HÀM TẠO ID CÔNG VIỆC TỰ ĐỘNG (CV001, CV002…)
# =========================================================
def generate_task_id(df):
    if "ID_CONG_VIEC" not in df.columns or df.empty:
        return "CV001"

    existing = df["ID_CONG_VIEC"].dropna().astype(str).tolist()
    nums = []

    for x in existing:
        if x.startswith("CV"):
            try:
                nums.append(int(x.replace("CV", "")))
            except:
                pass

    next_num = max(nums) + 1 if nums else 1
    return f"CV{next_num:03d}"


# =========================================================
# ✅ TAB GIAO VIỆC MỚI
# =========================================================
def render_new_task_tab():
    st.header("📝 Giao việc mới")

    # -----------------------------------------------------
    # ✅ Tải toàn bộ dữ liệu
    # -----------------------------------------------------
    all_sheets = load_all_sheets()
    df_cv = all_sheets["7_CONG_VIEC"].copy()

    # -----------------------------------------------------
    # ✅ Sinh ID công việc mới
    # -----------------------------------------------------
    new_id = generate_task_id(df_cv)
    st.info(f"ID công việc mới: **{new_id}**")

    # -----------------------------------------------------
    # ✅ Form nhập thông tin công việc
    # -----------------------------------------------------
    ten_viec = st.text_input("Tên công việc")
    noi_dung = st.text_area("Nội dung chi tiết")

    # -----------------------------------------------------
    # ✅ Người giao / Người nhận (dropdown từ 1_NHAN_SU)
    # -----------------------------------------------------
    df_ns = all_sheets["1_NHAN_SU"]
    ns_display, ns_map = get_display_list_multi(
        df_ns,
        id_col="ID_NHAN_SU",
        cols=["HO_TEN", "CHUC_VU"],
        prefix="Chọn..."
    )

    nguoi_giao = st.selectbox("Người giao", ns_display)
    nguoi_nhan = st.selectbox("Người nhận", ns_display)

    id_nguoi_giao = ns_map.get(nguoi_giao, "")
    id_nguoi_nhan = ns_map.get(nguoi_nhan, "")

    # -----------------------------------------------------
    # ✅ Ngày giao / Hạn chót
    # -----------------------------------------------------
    ngay_giao = st.date_input("Ngày giao", datetime.now())
    han_chot = st.date_input("Hạn chót")

    # -----------------------------------------------------
    # ✅ Liên kết: Đơn vị, Dự án, Gói thầu, Hợp đồng, Văn bản
    # -----------------------------------------------------
    def dropdown_link(sheet_name, id_col, display_cols, label):
        df_ref = all_sheets[sheet_name]
        display_list, mapping = get_display_list_multi(
            df_ref, id_col=id_col, cols=display_cols, prefix="Không chọn"
        )
        choice = st.selectbox(label, display_list)
        return mapping.get(choice, "")

    id_don_vi = dropdown_link("2_DON_VI", "ID_DON_VI",
                              ["TEN_DON_VI", "DIA_CHI"], "Đơn vị liên quan")

    id_du_an = dropdown_link("4_DU_AN", "ID_DU_AN",
                             ["TEN_DU_AN", "MO_TA", "NGAY_BD"], "Dự án liên quan")

    id_goi_thau = dropdown_link("5_GOI_THAU", "ID_GOI_THAU",
                                ["TEN_GOI_THAU", "GIA_TRI", "NGAY_BD"], "Gói thầu liên quan")

    id_hop_dong = dropdown_link("6_HOP_DONG", "ID_HOP_DONG",
                                ["SO_HD", "TEN_HD", "NGAY_KY"], "Hợp đồng liên quan")

    id_van_ban = dropdown_link("3_VAN_BAN", "ID_VB",
                               ["SO_VAN_BAN", "TRICH_YEU", "NGAY_BAN_HANH"], "Văn bản liên quan")

    # -----------------------------------------------------
    # ✅ Nút lưu công việc
    # -----------------------------------------------------
    if st.button("✅ Giao việc", type="primary"):
        if not ten_viec:
            st.error("❌ Vui lòng nhập tên công việc.")
            return

        new_row = {
            "ID_CONG_VIEC": new_id,
            "TEN_VIEC": ten_viec,
            "NOI_DUNG": noi_dung,
            "NGUOI_GIAO": id_nguoi_giao,
            "NGUOI_NHAN": id_nguoi_nhan,
            "NGAY_GIAO": ngay_giao.strftime("%d/%m/%Y"),
            "HAN_CHOT": han_chot.strftime("%d/%m/%Y"),
            "IDDV_CV": id_don_vi,
            "IDDA_CV": id_du_an,
            "IDGT_CV": id_goi_thau,
            "IDHD_CV": id_hop_dong,
            "IDVB_VAN_BAN": id_van_ban,
            "TRANG_THAI": "Đang thực hiện",
        }

        df_new = df_cv.copy()
        df_new.loc[len(df_new)] = new_row

        save_raw_sheet("7_CONG_VIEC", df_new)
        st.success("✅ Đã giao việc thành công!")
