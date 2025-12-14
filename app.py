import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# =========================================================
# CẤU HÌNH CHUNG
# =========================================================

REQUIRED_SHEETS = [
    "1_NHAN_SU", "2_DON_VI", "3_VAN_BAN", "4_DU_AN", "5_GOI_THAU",
    "6_HOP_DONG", "7_CONG_VIEC", "8_CAU_HINH", "9_CHAT_GEMINI",
]

DATE_COLS = [
    "NGAY_GIAO", "HAN_CHOT", "NGAY_THUC_TE_XONG",
    "NGAY_BAN_HANH", "NGAY_BD", "NGAY_KY"
]

# Cấu hình liên kết giữa các sheet cho Tab 3 – dữ liệu gốc
# format: sheet_name: { col_in_sheet: (ref_sheet, ref_id_col, ref_display_cols(list)) }
LINK_CONFIG_RAW = {
    "2_DON_VI": {
        "IDNS_TEN_GIAM_DOC": ("1_NHAN_SU", "ID_NHAN_SU", ["HO_TEN", "CHUC_VU", "DIEN_THOAI"]),
        "IDNS_TEN_LIEN_HE": ("1_NHAN_SU", "ID_NHAN_SU", ["HO_TEN", "CHUC_VU", "DIEN_THOAI"]),
    },
    "3_VAN_BAN": {
        "IDNS_NGUOI_KY": ("1_NHAN_SU", "ID_NHAN_SU", ["HO_TEN", "CHUC_VU", "DIEN_THOAI"]),
        "IDDV_BAN_HANH": ("2_DON_VI", "ID_DON_VI", ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"]),
        "IDDV_NHAN": ("2_DON_VI", "ID_DON_VI", ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"]),
        "IDNS_CHU_TRI": ("1_NHAN_SU", "ID_NHAN_SU", ["HO_TEN", "CHUC_VU", "DIEN_THOAI"]),
        "IDGT_GOI_THAU": ("5_GOI_THAU", "ID_GOI_THAU", ["TEN_GOI_THAU", "GIA_TRI", "NGAY_BD"]),
        "IDDA_DU_AN": ("4_DU_AN", "ID_DU_AN", ["TEN_DU_AN", "MO_TA", "NGAY_BD"]),
        "IDDV_KY_HOP_DONG": ("2_DON_VI", "ID_DON_VI", ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"]),
        "IDHD_HOP_DONG": ("6_HOP_DONG", "ID_HOP_DONG", ["TEN_HD", "SO_HD", "NGAY_KY"]),
    },
    "4_DU_AN": {
        "IDDV_CHU_DAU_TU": ("2_DON_VI", "ID_DON_VI", ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"]),
    },
    "5_GOI_THAU": {
        "IDDA_DU_AN": ("4_DU_AN", "ID_DU_AN", ["TEN_DU_AN", "MO_TA", "NGAY_BD"]),
    },
    "6_HOP_DONG": {
        "IDGT_GOI_THAU": ("5_GOI_THAU", "ID_GOI_THAU", ["TEN_GOI_THAU", "GIA_TRI", "NGAY_BD"]),
        "IDDV_NHA_THAU": ("2_DON_VI", "ID_DON_VI", ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"]),
    },
}

# =========================================================
# KẾT NỐI GOOGLE SHEETS
# =========================================================

@st.cache_resource
def connect_gsheet():
    creds_dict = dict(st.secrets["gdrive"])
    creds_dict.setdefault("token_uri", "https://oauth2.googleapis.com/token")
    creds_dict.setdefault("auth_uri", "https://accounts.google.com/o/oauth2/auth")
    creds_dict.setdefault(
        "auth_provider_x509_cert_url",
        "https://www.googleapis.com/oauth2/v1/certs",
    )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# =========================================================
# HÀM XỬ LÝ DỮ LIỆU
# =========================================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\u00a0", "", regex=False)
    )
    return df

def remove_duplicate_and_empty_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.loc[:, df.columns != ""]
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    return df

def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for c in DATE_COLS:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

def format_date_vn(value):
    if pd.isna(value):
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    return str(value)

def get_unique_list(df: pd.DataFrame, col_name: str, prefix="Tất cả"):
    if df.empty or col_name not in df.columns:
        return [prefix]
    unique_list = df[col_name].dropna().astype(str).unique().tolist()
    return [prefix] + sorted(unique_list)

def get_display_list_multi(df, id_col, cols, prefix="Chọn"):
    if df.empty or any(c not in df.columns for c in [id_col] + cols):
        return [prefix], {}
    df_temp = df[[id_col] + cols].fillna("")
    df_temp["DISPLAY"] = df_temp[cols[0]].astype(str)
    for c in cols[1:]:
        df_temp["DISPLAY"] += " | " + df_temp[c].astype(str)
    mapping = dict(zip(df_temp["DISPLAY"], df_temp[id_col]))
    lst = [prefix] + df_temp["DISPLAY"].tolist()
    return lst, mapping

def lookup_display(id_value, df, id_col, cols):
    if not id_value or df.empty or id_col not in df.columns:
        return ""
    row = df[df[id_col].astype(str) == str(id_value)]
    if row.empty:
        return ""
    parts = []
    for c in cols:
        if c in row.columns:
            v = row.iloc[0][c]
            if isinstance(v, pd.Timestamp):
                parts.append(format_date_vn(v))
            else:
                parts.append(str(v))
    return " – ".join(parts)

# =========================================================
# LOAD DỮ LIỆU
# =========================================================

@st.cache_data(ttl=600)
def load_sheet_df(sheet_name: str) -> pd.DataFrame:
    try:
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)

        values = ws.get_all_values()
        if len(values) < 2:
            st.warning(f"⚠️ Sheet '{sheet_name}' không có dữ liệu.")
            return pd.DataFrame()

        df = pd.DataFrame(values[1:], columns=values[0])
        df = normalize_columns(df)
        df = remove_duplicate_and_empty_cols(df)
        df = parse_dates(df)

        for col in df.columns:
            if col not in DATE_COLS and not pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str).str.strip()

        return df
    except Exception as e:
        st.error(f"❌ Lỗi tải Sheet '{sheet_name}': {type(e).__name__} - {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_all_sheets():
    sheets = {}
    st.info("Đang tải dữ liệu từ Google Sheets...")
    for name in REQUIRED_SHEETS:
        sheets[name] = load_sheet_df(name)
    st.success("✅ Đã kết nối và tải dữ liệu Google Sheets thành công!")
    return sheets

# =========================================================
# GHI DỮ LIỆU
# =========================================================

def save_raw_sheet(sheet_name: str, edited_df: pd.DataFrame):
    try:
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)

        ws.clear()
        data_to_write = [edited_df.columns.tolist()] + edited_df.fillna("").values.tolist()
        ws.append_rows(data_to_write, value_input_option="USER_ENTERED")

        st.success(f"🎉 Đã lưu và cập nhật Sheet '{sheet_name}' thành công!")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"❌ Lỗi khi ghi vào Sheet '{sheet_name}': {e}")

def append_new_work(new_data: dict, df_cv: pd.DataFrame, all_sheets: dict):
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

    df_ns = all_sheets["1_NHAN_SU"]
    df_dv = all_sheets["2_DON_VI"]
    df_da = all_sheets["4_DU_AN"]
    df_gt = all_sheets["5_GOI_THAU"]
    df_hd = all_sheets["6_HOP_DONG"]
    df_vb = all_sheets["3_VAN_BAN"]

    try:
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
        ws_cv = sh.worksheet("7_CONG_VIEC")

        header = ws_cv.row_values(1)

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

        # Thêm cột mô tả cho các liên kết
        new_row_dict["TEN_NGUOI_NHAN_MO_TA"] = lookup_display(
            new_row_dict["NGUOI_NHAN"], df_ns, "ID_NHAN_SU", ["HO_TEN", "CHUC_VU", "DIEN_THOAI"]
        )
        new_row_dict["TEN_NGUOI_GIAO_MO_TA"] = lookup_display(
            new_row_dict["NGUOI_GIAO"], df_ns, "ID_NHAN_SU", ["HO_TEN", "CHUC_VU", "DIEN_THOAI"]
        )
        new_row_dict["TEN_DON_VI_MO_TA"] = lookup_display(
            new_row_dict["IDDV_CV"], df_dv, "ID_DON_VI", ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"]
        )
        new_row_dict["TEN_DU_AN_MO_TA"] = lookup_display(
            new_row_dict["IDDA_CV"], df_da, "ID_DU_AN", ["TEN_DU_AN", "MO_TA", "NGAY_BD"]
        )
        new_row_dict["TEN_GOI_THAU_MO_TA"] = lookup_display(
            new_row_dict["IDGT_CV"], df_gt, "ID_GOI_THAU", ["TEN_GOI_THAU", "GIA_TRI", "NGAY_BD"]
        )
        new_row_dict["TEN_HOP_DONG_MO_TA"] = lookup_display(
            new_row_dict["IDHD_CV"], df_hd, "ID_HOP_DONG", ["TEN_HD", "SO_HD", "NGAY_KY"]
        )
        new_row_dict["SO_VAN_BAN_MO_TA"] = lookup_display(
            new_row_dict["IDVB_VAN_BAN"], df_vb, "ID_VB", ["SO_VAN_BAN", "NGAY_BAN_HANH", "TRICH_YEU"]
        )

        values_to_append = [new_row_dict.get(h, "") for h in header]
        ws_cv.append_row(values_to_append, value_input_option="USER_ENTERED")

        st.success(f"🎉 Đã thêm công việc mới: **{new_id} - {new_data.get('ten_viec', '')}**")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"❌ Lỗi khi ghi vào Google Sheet 7_CONG_VIEC: {e}")

# =========================================================
# BỘ LỌC & BÁO CÁO
# =========================================================

def filter_report(df, start_date, end_date, id_duan, id_goithau, id_hopdong, trang_thai):
    df = df.copy()
    if "NGAY_GIAO" in df.columns and pd.api.types.is_datetime64_any_dtype(df["NGAY_GIAO"]):
        df = df[
            (df["NGAY_GIAO"].dt.date >= start_date) &
            (df["NGAY_GIAO"].dt.date <= end_date)
        ]
    if trang_thai != "Tất cả":
        df = df[df["TRANG_THAI_TONG"] == trang_thai]
    if id_duan != "Tất cả":
        df = df[df["IDDA_CV"] == id_duan]
    if id_goithau != "Tất cả":
        df = df[df["IDGT_CV"] == id_goithau]
    if id_hopdong != "Tất cả":
        df = df[df["IDHD_CV"] == id_hopdong]
    return df

# =========================================================
# HÀM EMAIL
# =========================================================

def render_email_button(all_sheets: dict, df_report: pd.DataFrame):
    df_cfg = all_sheets.get("8_CAU_HINH", pd.DataFrame())
    if df_cfg.empty or "EMAIL_BC_CV" not in df_cfg.columns:
        return
    emails = df_cfg["EMAIL_BC_CV"].dropna().astype(str).tolist()
    if not emails:
        return

    subject = "Bao cao cong viec"
    body_lines = ["Kinh gui anh/chi,", "", "Day la bao cao cong viec moi nhat:", ""]
    for _, r in df_report.iterrows():
        ten_viec = r.get("TEN_VIEC") or r.get("NOI_DUNG") or "Khong ten"
        trang_thai = r.get("TRANG_THAI_TONG", "")
        han = format_date_vn(r.get("HAN_CHOT"))
        body_lines.append(f"- {ten_viec} | Trang thai: {trang_thai} | Han chot: {han}")
    body_lines.append("")
    body_lines.append("Tran trong.")
    import urllib.parse
    body = "\n".join(body_lines)
    mailto_link = "mailto:{}?subject={}&body={}".format(
        ",".join(emails),
        urllib.parse.quote(subject),
        urllib.parse.quote(body),
    )
    st.markdown(f"[📧 Gửi email báo cáo]({mailto_link})")

# =========================================================
# UI – GIAO DIỆN CHÍNH
# =========================================================

def main():
    st.set_page_config(page_title="Quản lý công việc EVNGENCO1", layout="wide")
    st.title("📋 CHƯƠNG TRÌNH QUẢN LÝ CÔNG VIỆC – BAN KHCNĐMST")
    st.caption("Phát triển và công nghệ: Google & Nguyễn Trọng Thắng")
    st.caption("Email liên hệ: thangnt@evngenco1.vn")

    all_sheets = load_all_sheets()
    df_cv = all_sheets["7_CONG_VIEC"]
    df_ns = all_sheets["1_NHAN_SU"]
    df_dv = all_sheets["2_DON_VI"]

    tab_report, tab_input, tab_data = st.tabs(
        ["📊 Báo cáo & Lọc công việc", "📝 Giao việc mới", "📁 Quản lý dữ liệu gốc"]
    )

    # =====================================================
    # TAB 1: BÁO CÁO & LỌC
    # =====================================================
    with tab_report:
        st.header("1. Bộ lọc báo cáo")

        list_trang_thai = get_unique_list(df_cv, "TRANG_THAI_TONG")
        list_idda = get_unique_list(df_cv, "IDDA_CV")
        list_idgt = get_unique_list(df_cv, "IDGT_CV")
        list_idhd = get_unique_list(df_cv, "IDHD_CV")

        with st.sidebar:
            st.header("🎯 Bộ lọc")
            chon_trang_thai = st.selectbox("Trạng thái:", list_trang_thai)
            chon_duan = st.selectbox("ID Dự án:", list_idda)
            chon_goithau = st.selectbox("ID Gói thầu:", list_idgt)
            chon_hopdong = st.selectbox("ID Hợp đồng:", list_idhd)
            start_date = st.date_input("Từ ngày:", datetime.now().date() - timedelta(days=30))
            end_date = st.date_input("Đến ngày:", datetime.now().date())

        st.subheader("2. Chọn cột hiển thị báo cáo")

        available_columns = {
            "Tên công việc": "TEN_VIEC",
            "Nội dung": "NOI_DUNG",
            "Loại việc": "LOAI_VIEC",
            "Nguồn giao việc": "NGUON_GIAO_VIEC",
            "Người giao": "NGUOI_GIAO",
            "Người nhận": "NGUOI_NHAN",
            "Ngày giao": "NGAY_GIAO",
            "Hạn chót": "HAN_CHOT",
            "Người phối hợp": "NGUOI_PHOI_HOP",
            "Trạng thái tổng": "TRANG_THAI_TONG",
            "Trạng thái chi tiết": "TRANG_THAI_CHI_TIET",
            "Ngày thực tế xong": "NGAY_THUC_TE_XONG",
            "Vướng mắc": "VUONG_MAC",
            "Đề xuất": "DE_XUAT",
            "Ghi chú": "GHI_CHU_CV",
            "Dự án": "IDDA_CV",
            "Gói thầu": "IDGT_CV",
            "Hợp đồng": "IDHD_CV",
            "Văn bản": "IDVB_VAN_BAN",
            "Đơn vị": "IDDV_CV",
        }

        selected_columns = st.multiselect(
            "Chọn các cột muốn hiển thị:",
            list(available_columns.keys()),
            default=["Tên công việc", "Người nhận", "Hạn chót", "Trạng thái tổng"]
        )

        st.subheader("3. Kết quả báo cáo")

        if df_cv.empty:
            st.warning("Không có dữ liệu công việc.")
        else:
            df_report = filter_report(
                df_cv, start_date, end_date,
                chon_duan, chon_goithau, chon_hopdong, chon_trang_thai
            )

            if df_report.empty:
                st.info("Không có công việc khớp điều kiện.")
            else:
                st.markdown(f"**Tổng số công việc: {len(df_report)}**")
                render_email_button(all_sheets, df_report)

                df_display = pd.DataFrame()

                for col_label in selected_columns:
                    col_name = available_columns[col_label]

                    if col_name == "NGUOI_NHAN":
                        df_display[col_label] = df_report["NGUOI_NHAN"].apply(
                            lambda x: lookup_display(
                                x, df_ns, "ID_NHAN_SU", ["HO_TEN", "CHUC_VU", "DIEN_THOAI"]
                            )
                        )
                    elif col_name == "NGUOI_GIAO":
                        df_display[col_label] = df_report["NGUOI_GIAO"].apply(
                            lambda x: lookup_display(
                                x, df_ns, "ID_NHAN_SU", ["HO_TEN", "CHUC_VU", "DIEN_THOAI"]
                            )
                        )
                    elif col_name == "IDDV_CV":
                        df_display[col_label] = df_report["IDDV_CV"].apply(
                            lambda x: lookup_display(
                                x, df_dv, "ID_DON_VI", ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"]
                            )
                        )
                    elif col_name == "IDDA_CV":
                        df_display[col_label] = df_report["IDDA_CV"].apply(
                            lambda x: lookup_display(
                                x, all_sheets["4_DU_AN"], "ID_DU_AN", ["TEN_DU_AN", "MO_TA", "NGAY_BD"]
                            )
                        )
                    elif col_name == "IDGT_CV":
                        df_display[col_label] = df_report["IDGT_CV"].apply(
                            lambda x: lookup_display(
                                x, all_sheets["5_GOI_THAU"], "ID_GOI_THAU", ["TEN_GOI_THAU", "GIA_TRI", "NGAY_BD"]
                            )
                        )
                    elif col_name == "IDHD_CV":
                        df_display[col_label] = df_report["IDHD_CV"].apply(
                            lambda x: lookup_display(
                                x, all_sheets["6_HOP_DONG"], "ID_HOP_DONG", ["TEN_HD", "SO_HD", "NGAY_KY"]
                            )
                        )
                    elif col_name == "IDVB_VAN_BAN":
                        df_display[col_label] = df_report["IDVB_VAN_BAN"].apply(
                            lambda x: lookup_display(
                                x, all_sheets["3_VAN_BAN"], "ID_VB", ["SO_VAN_BAN", "NGAY_BAN_HANH", "TRICH_YEU"]
                            )
                        )
                    elif col_name in DATE_COLS:
                        df_display[col_label] = df_report[col_name].apply(format_date_vn)
                    else:
                        df_display[col_label] = df_report[col_name]

                st.dataframe(df_display, use_container_width=True)

    # =====================================================
    # TAB 2: GIAO VIỆC MỚI
    # =====================================================
    with tab_input:
        st.header("📝 Giao Công Việc Mới (Sheet 7_CONG_VIEC)")

        df_da = all_sheets["4_DU_AN"]
        df_gt = all_sheets["5_GOI_THAU"]
        df_hd = all_sheets["6_HOP_DONG"]
        df_vb = all_sheets["3_VAN_BAN"]

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

    # =====================================================
    # TAB 3: QUẢN LÝ DỮ LIỆU GỐC
    # =====================================================
    with tab_data:
        st.header("📁 Quản lý dữ liệu gốc (Thêm / Sửa / Xóa)")
        st.warning(
            "⚠️ Chức năng này ghi đè toàn bộ dữ liệu Sheet đã chọn. "
            "Hãy sao lưu Google Sheet trước khi chỉnh sửa."
        )

        editable_sheets = [s for s in REQUIRED_SHEETS if s != "7_CONG_VIEC"]
        sheet_name = st.selectbox("Chọn Sheet dữ liệu:", editable_sheets)

        df_goc = all_sheets[sheet_name].copy()

        # Áp dụng liên kết mô tả cho dữ liệu gốc (nếu có cấu hình)
        if sheet_name in LINK_CONFIG_RAW:
            for col, (ref_sheet, id_col, desc_cols) in LINK_CONFIG_RAW[sheet_name].items():
                if col in df_goc.columns:
                    df_ref = all_sheets.get(ref_sheet, pd.DataFrame())
                    df_goc[col] = df_goc[col].apply(
                        lambda x: lookup_display(x, df_ref, id_col, desc_cols)
                    )

        st.markdown(
            f"**Nội dung Sheet: {sheet_name}** "
            f"(Tổng số dòng: {len(df_goc)})"
        )

        edited_df = st.data_editor(
            df_goc,
            num_rows="dynamic",
            use_container_width=True,
            key=f"data_editor_{sheet_name}",
        )

        if st.button(f"LƯU CẬP NHẬT CHO SHEET {sheet_name}", type="primary"):
            # Ở đây: edited_df đang là mô tả, không có ID - nếu cần lưu ID, ta phải thêm logic mapping ngược
            # Hiện tại: ta lưu đúng như người dùng thấy (mô tả), còn các cột ID vẫn do Google Sheet hoặc quy trình nhập liệu khác quản lý
            save_raw_sheet(sheet_name, edited_df)

    st.caption("Dữ liệu được tải từ Google Sheets và được làm mới sau mỗi 10 phút.")


if __name__ == "__main__":
    main()
