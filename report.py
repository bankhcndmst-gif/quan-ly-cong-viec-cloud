# =========================================================
# REPORT.PY — TAB BÁO CÁO & LỌC CÔNG VIỆC (BẢN NÂNG CẤP)
# =========================================================

import streamlit as st
from datetime import datetime, timedelta

from utils import (
    get_unique_list,
    lookup_display,
    format_date_vn
)
from config import DATE_COLS


# ---------------------------------------------------------
# HÀM LỌC DỮ LIỆU BÁO CÁO
# ---------------------------------------------------------
def filter_report(df, start_date, end_date, id_duan, id_goithau, id_hopdong, trang_thai):
    df = df.copy()

    # Lọc theo ngày giao
    if "NGAY_GIAO" in df.columns and hasattr(df["NGAY_GIAO"], "dt"):
        df = df[
            (df["NGAY_GIAO"].dt.date >= start_date) &
            (df["NGAY_GIAO"].dt.date <= end_date)
        ]

    # Lọc theo trạng thái
    if trang_thai != "Tất cả":
        df = df[df["TRANG_THAI_TONG"] == trang_thai]

    # Lọc theo dự án
    if id_duan != "Tất cả":
        df = df[df["IDDA_CV"] == id_duan]

    # Lọc theo gói thầu
    if id_goithau != "Tất cả":
        df = df[df["IDGT_CV"] == id_goithau]

    # Lọc theo hợp đồng
    if id_hopdong != "Tất cả":
        df = df[df["IDHD_CV"] == id_hopdong]

    return df


# ---------------------------------------------------------
# NÚT GỬI EMAIL BÁO CÁO
# ---------------------------------------------------------
def render_email_button(all_sheets, df_report):
    df_cfg = all_sheets.get("8_CAU_HINH", None)
    if df_cfg is None or df_cfg.empty:
        return

    if "EMAIL_BC_CV" not in df_cfg.columns:
        return

    emails = df_cfg["EMAIL_BC_CV"].dropna().astype(str).tolist()
    if not emails:
        return

    subject = "Bao cao cong viec"
    body_lines = ["Kính gửi anh/chị,", "", "Dưới đây là báo cáo công việc mới nhất:", ""]

    for _, r in df_report.iterrows():
        ten_viec = r.get("TEN_VIEC") or r.get("NOI_DUNG") or "Không tên"
        trang_thai = r.get("TRANG_THAI_TONG", "")
        han = format_date_vn(r.get("HAN_CHOT"))
        body_lines.append(f"- {ten_viec} | Trạng thái: {trang_thai} | Hạn chót: {han}")

    body_lines.append("")
    body_lines.append("Trân trọng.")

    import urllib.parse
    body = "\n".join(body_lines)

    mailto_link = "mailto:{}?subject={}&body={}".format(
        ",".join(emails),
        urllib.parse.quote(subject),
        urllib.parse.quote(body),
    )

    st.markdown(f"[📧 Gửi email báo cáo]({mailto_link})")


# ---------------------------------------------------------
# TAB BÁO CÁO (BẢN NÂNG CẤP)
# ---------------------------------------------------------
def render_report_tab(all_sheets, df_cv, df_ns, df_dv):
    st.header("📊 Báo cáo & Lọc công việc (Bản nâng cấp)")

    # Danh sách lọc
    list_trang_thai = get_unique_list(df_cv, "TRANG_THAI_TONG")
    list_idda = get_unique_list(df_cv, "IDDA_CV")
    list_idgt = get_unique_list(df_cv, "IDGT_CV")
    list_idhd = get_unique_list(df_cv, "IDHD_CV")

    # -----------------------------
    # Bộ lọc bên sidebar
    # -----------------------------
    with st.sidebar:
        st.header("🎯 Bộ lọc nâng cao")

        chon_trang_thai = st.selectbox("Trạng thái:", list_trang_thai)
        chon_duan = st.selectbox("Dự án (ID):", list_idda)
        chon_goithau = st.selectbox("Gói thầu (ID):", list_idgt)
        chon_hopdong = st.selectbox("Hợp đồng (ID):", list_idhd)

        start_date = st.date_input("Từ ngày:", datetime.now().date() - timedelta(days=30))
        end_date = st.date_input("Đến ngày:", datetime.now().date())

    # -----------------------------
    # Chọn cột hiển thị
    # -----------------------------
    st.subheader("2. Chọn cột hiển thị báo cáo")

    available_columns = {
        "ID Công việc": "ID_CONG_VIEC",
        "Tên công việc": "TEN_VIEC",
        "Nội dung": "NOI_DUNG",
        "Loại việc": "LOAI_VIEC",
        "Nguồn giao việc": "NGUON_GIAO_VIEC",
        "Người giao (ID)": "NGUOI_GIAO",
        "Người giao (Mô tả)": "NGUOI_GIAO_MO_TA",
        "Người nhận (ID)": "NGUOI_NHAN",
        "Người nhận (Mô tả)": "NGUOI_NHAN_MO_TA",
        "Ngày giao": "NGAY_GIAO",
        "Hạn chót": "HAN_CHOT",
        "Ngày thực tế xong": "NGAY_THUC_TE_XONG",
        "Trạng thái tổng": "TRANG_THAI_TONG",
        "Trạng thái chi tiết": "TRANG_THAI_CHI_TIET",
        "Vướng mắc": "VUONG_MAC",
        "Đề xuất": "DE_XUAT",
        "Ghi chú": "GHI_CHU_CV",
        "Dự án (ID)": "IDDA_CV",
        "Dự án (Mô tả)": "TEN_DU_AN_MO_TA",
        "Gói thầu (ID)": "IDGT_CV",
        "Gói thầu (Mô tả)": "TEN_GOI_THAU_MO_TA",
        "Hợp đồng (ID)": "IDHD_CV",
        "Hợp đồng (Mô tả)": "TEN_HOP_DONG_MO_TA",
        "Văn bản (ID)": "IDVB_VAN_BAN",
        "Văn bản (Mô tả)": "SO_VAN_BAN_MO_TA",
        "Đơn vị (ID)": "IDDV_CV",
        "Đơn vị (Mô tả)": "TEN_DON_VI_MO_TA",
    }

    selected_columns = st.multiselect(
        "Chọn các cột muốn hiển thị:",
        list(available_columns.keys()),
        default=["ID Công việc", "Tên công việc", "Người nhận (Mô tả)", "Hạn chót", "Trạng thái tổng"]
    )

    # -----------------------------
    # Lọc dữ liệu
    # -----------------------------
    st.subheader("3. Kết quả báo cáo")

    df_report = filter_report(
        df_cv, start_date, end_date,
        chon_duan, chon_goithau, chon_hopdong, chon_trang_thai
    )

    if df_report.empty:
        st.info("Không có công việc khớp điều kiện.")
        return

    st.markdown(f"**Tổng số công việc: {len(df_report)}**")

    render_email_button(all_sheets, df_report)

    # -----------------------------
    # Tạo bảng hiển thị
    # -----------------------------
    df_display = {}

    for col_label in selected_columns:
        col_name = available_columns[col_label]

        # Cột ngày
        if col_name in DATE_COLS:
            df_display[col_label] = df_report[col_name].apply(format_date_vn)

        # Cột mô tả đã có sẵn
        elif col_name.endswith("_MO_TA"):
            df_display[col_label] = df_report[col_name]

        # Cột ID hoặc text
        else:
            df_display[col_label] = df_report[col_name]

    st.dataframe(df_display, use_container_width=True)
