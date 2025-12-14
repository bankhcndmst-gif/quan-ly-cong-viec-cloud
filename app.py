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

DATE_COLS = ["NGAY_GIAO", "HAN_CHOT", "NGAY_THUC_TE_XONG"]


# =========================================================
# KẾT NỐI GOOGLE SHEETS
# =========================================================

@st.cache_resource
def connect_gsheet():
    """Kết nối Google Sheets dùng service account trong st.secrets['gdrive']."""
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
# HÀM XỬ LÝ DỮ LIỆU CHUNG
# =========================================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hóa tên cột: bỏ khoảng trắng, ký tự đặc biệt không cần thiết."""
    df.columns = (
        df.columns.astype(str)
        .str.strip()                      # ✅ Sửa lỗi strip
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
        return "—"
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    return str(value)


def get_unique_list(df: pd.DataFrame, col_name: str, prefix="Tất cả"):
    if df.empty or col_name not in df.columns:
        return [prefix]
    unique_list = df[col_name].dropna().astype(str).unique().tolist()
    return [prefix] + sorted(unique_list)


def get_display_list(df: pd.DataFrame, id_col: str, name_col: str, prefix="Tất cả"):
    if df.empty or id_col not in df.columns or name_col not in df.columns:
        return [prefix]

    df_temp = df[[id_col, name_col]].dropna()
    df_temp["DISPLAY"] = (
        df_temp[id_col].astype(str).str.strip()
        + ": "
        + df_temp[name_col].astype(str).str.strip()
    )
    unique_list = df_temp["DISPLAY"].unique().tolist()
    return [prefix] + sorted(unique_list)


def extract_id_from_display(display_str: str) -> str:
    if ":" in display_str:
        return display_str.split(":", 1)[0].strip()
    return display_str.strip()


def get_display_name(id_value: str, df: pd.DataFrame, id_col: str, name_col: str) -> str:
    if df.empty or id_col not in df.columns or name_col not in df.columns or not id_value:
        return id_value
    result = df[df[id_col].astype(str).str.strip() == str(id_value).strip()]
    if not result.empty:
        return result[name_col].iloc[0]
    return id_value


# =========================================================
# LOAD DỮ LIỆU TỪ GOOGLE SHEETS
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
        data_to_write = [edited_df.columns.tolist()] + edited_df.values.tolist()
        ws.append_rows(data_to_write, value_input_option="USER_ENTERED")

        st.success(f"🎉 Đã lưu và cập nhật Sheet '{sheet_name}' thành công!")
        st.cache_data.clear()
        st.rerun()

    except Exception as e:
        st.error(f"❌ Lỗi khi ghi vào Sheet '{sheet_name}': {e}")


def append_new_work(new_data: dict, df_cv: pd.DataFrame):
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
                if new_data.get("ngay_thuc_te_xong")
                else ""
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

        values_to_append = [new_row_dict.get(h, "") for h in header]
        ws_cv.append_row(values_to_append, value_input_option="USER_ENTERED")

        st.success(f"🎉 Đã thêm công việc mới: **{new_id} - {new_data.get('ten_viec', '')}**")
        st.cache_data.clear()
        st.rerun()

    except Exception as e:
        st.error(f"❌ Lỗi khi ghi vào Google Sheet 7_CONG_VIEC: {e}")


# =========================================================
# BỘ LỌC BÁO CÁO
# =========================================================

def filter_report(df, start_date, end_date, id_duan, id_goithau, id_hopdong, trang_thai):
    df = df.copy()

    if "NGAY_GIAO" in df.columns:
        df = df[
            (df["NGAY_GIAO"].dt.date >= start_date)
            & (df["NGAY_GIAO"].dt.date <= end_date)
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
# UI CHÍNH
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

    # -----------------------------------------------------
    # TAB 1: BÁO CÁO
    # -----------------------------------------------------
    with tab_report:
        st.header("Bộ lọc báo cáo")

        list_trang_thai = get_unique_list(df_cv, "TRANG_THAI_TONG")
        list_idda = get_unique_list(df_cv, "IDDA_CV")
        list_idgt = get_unique_list(df_cv, "IDGT_CV")
        list_idhd = get_unique_list(df_cv, "IDHD_CV")

        with st.sidebar:
            chon_trang_thai = st.selectbox("Trạng thái:", list_trang_thai)
            chon_duan = st.selectbox("ID Dự án:", list_idda)
            chon_goithau = st.selectbox("ID Gói thầu:", list_idgt)
            chon_hopdong = st.selectbox("ID Hợp đồng:", list_idhd)

            start_date = st.date_input("Từ ngày:", datetime.now().date() - timedelta(days=30))
            end_date = st.date_input("Đến ngày:", datetime.now().date())

        df_report = filter_report(
            df_cv, start_date, end_date, chon_duan, chon_goithau, chon_hopdong, chon_trang_thai
        )

        st.subheader("Kết quả báo cáo")
        st.write(f"Tổng số công việc: **{len(df_report)}**")

        for _, r in df_report.iterrows():
            st.markdown(
                f"""
                **• {r['TEN_VIEC']}** (ID: {r['ID_CONG_VIEC']})  
                - Người nhận: **{get_display_name(r['NGUOI_NHAN'], df_ns, 'ID_NHAN_SU', 'HO_TEN')}**  
                - Hạn chót: **{format_date_vn(r['HAN_CHOT'])}**  
                - Trạng thái: **{r['TRANG_THAI_TONG']}**  
                - Vướng mắc: *{r['VUONG_MAC']}*
                """
            )
            st.markdown("---")

    # -----------------------------------------------------
    # TAB 2: GIAO VIỆC MỚI
    # -----------------------------------------------------
    with tab_input:
        st.header("Giao việc mới")

        list_ns_display = get_display_list(df_ns, "ID_NHAN_SU", "HO_TEN")
        list_dv_display = get_display_list(df_dv, "ID_DON_VI", "TEN_DON_VI")

        with st.form("form_new_work"):
            ten_viec = st.text_input("Tên công việc")
            nguoi_nhan_display = st.selectbox("Người nhận", list_ns_display)
            ngay_giao = st.date_input("Ngày giao", datetime.now().date())
            han_chot = st.date_input("Hạn chót", datetime.now().date() + timedelta(days=7))
            trang_thai = st.selectbox("Trạng thái", list_trang_thai)

            noi_dung = st.text_area("Nội dung")
            vuong_mac = st.text_area("Vướng mắc")
            ghi_chu = st.text_area("Ghi chú")

            submitted = st.form_submit_button("Lưu công việc")

            if submitted:
                new_data = {
                    "ten_viec": ten_viec,
                    "noi_dung": noi_dung,
                    "loai_viec": "",
                    "nguon_giao_viec": "",
                    "nguoi_giao": "",
                    "nguoi_nhan": extract_id_from_display(nguoi_nhan_display),
                    "ngay_giao": ngay_giao,
                    "han_chot": han_chot,
                    "trang_thai_tong": trang_thai,
                    "trang_thai_chi_tiet": "",
                    "ngay_thuc_te_xong": None,
                    "idda_cv": "",
                    "idhd_cv": "",
                    "idgt_cv": "",
                    "idvb_van_ban": "",
                    "iddv_cv": "",
                    "nguoi_phoi_hop": "",
                    "vuong_mac": vuong_mac,
                    "de_xuat": "",
                    "ghi_chu_cv": ghi_chu,
                }
                append_new_work(new_data, df_cv)

    # -----------------------------------------------------
    # TAB 3: QUẢN LÝ DỮ LIỆU GỐC
    # -----------------------------------------------------
    with tab_data:
        st.header("Quản lý dữ liệu gốc")

        editable_sheets = [s for s in REQUIRED_SHEETS if s != "7_CONG_VIEC"]
        sheet_name = st.selectbox("Chọn sheet", editable_sheets)

        df_goc = all_sheets[sheet_name]

        edited_df = st.data_editor(df_goc, num_rows="dynamic")

        if st.button("Lưu dữ liệu"):
            save_raw_sheet(sheet_name, edited_df)


if __name__ == "__main__":
    main()
