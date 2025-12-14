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

    # Bổ sung các field hay thiếu gây lỗi MalformedError
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
        .strip()
        .str.replace("\u00a0", "", regex=False)
    )
    return df


def remove_duplicate_and_empty_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Xóa cột rỗng hoặc trùng lặp để tránh lỗi Duplicate column names."""
    df = df.loc[:, df.columns != ""]
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Chuyển các cột ngày trong DATE_COLS sang datetime."""
    for c in DATE_COLS:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def format_date_vn(value):
    """Định dạng datetime thành dd/mm/yyyy (kiểu VN)."""
    if pd.isna(value):
        return "—"
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    return str(value)


def get_unique_list(df: pd.DataFrame, col_name: str, prefix="Tất cả"):
    """Trả về danh sách giá trị duy nhất trong 1 cột, thêm phần tử prefix đầu tiên."""
    if df.empty or col_name not in df.columns:
        return [prefix]
    unique_list = df[col_name].dropna().astype(str).unique().tolist()
    return [prefix] + sorted(unique_list)


def get_display_list(df: pd.DataFrame, id_col: str, name_col: str, prefix="Tất cả"):
    """Tạo list dạng [prefix, 'ID: Tên', ...] để dùng cho selectbox."""
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
    """Tách ID từ chuỗi 'ID: Tên'."""
    if ":" in display_str:
        return display_str.split(":", 1)[0].strip()
    return display_str.strip()


def get_display_name(id_value: str, df: pd.DataFrame, id_col: str, name_col: str) -> str:
    """Tìm tên (name_col) tương ứng với ID (id_col)."""
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
    """Tải 1 sheet thành DataFrame, đã xử lý cột và kiểu date."""
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
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"⚠️ Sheet '{sheet_name}' không tồn tại.")
        return pd.DataFrame()
    except gspread.exceptions.APIError as e:
        st.error(f"❌ Lỗi API khi tải Sheet '{sheet_name}': {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi tải Sheet '{sheet_name}': {type(e).__name__} - {e}")
        return pd.DataFrame()


@st.cache_data(ttl=600)
def load_all_sheets():
    """Tải tất cả các sheet bắt buộc vào dictionary."""
    sheets = {}
    st.info("Đang tải dữ liệu từ Google Sheets...")
    for name in REQUIRED_SHEETS:
        sheets[name] = load_sheet_df(name)
    st.success("✅ Đã kết nối và tải dữ liệu Google Sheets thành công!")
    return sheets


# =========================================================
# HÀM GHI / CẬP NHẬT GOOGLE SHEETS
# =========================================================

def save_raw_sheet(sheet_name: str, edited_df: pd.DataFrame):
    """Ghi đè toàn bộ sheet bằng DataFrame mới."""
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
    """Thêm 1 dòng công việc mới vào Sheet '7_CONG_VIEC'."""
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
            "NGAY_GIAO": new_data.get("ngay_giao").strftime("%Y-%m-%d") if new_data.get("ngay_giao") else "",
            "HAN_CHOT": new_data.get("han_chot").strftime("%Y-%m-%d") if new_data.get("han_chot") else "",
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
# LOGIC BÁO CÁO / LỌC
# =========================================================

def filter_report(
    df: pd.DataFrame,
    start_date,
    end_date,
    id_duan: str,
    id_goithau: str,
    id_hopdong: str,
    trang_thai: str,
):
    df = df.copy()

    if "NGAY_GIAO" in df.columns and pd.api.types.is_datetime64_any_dtype(df["NGAY_GIAO"]):
        df = df[
            (df["NGAY_GIAO"].dt.date >= start_date)
            & (df["NGAY_GIAO"].dt.date <= end_date)
        ]

    if trang_thai != "Tất cả" and "TRANG_THAI_TONG" in df.columns:
        df = df[df["TRANG_THAI_TONG"].astype(str) == trang_thai]

    if id_duan != "Tất cả" and "IDDA_CV" in df.columns:
        df = df[df["IDDA_CV"].astype(str) == id_duan]

    if id_goithau != "Tất cả" and "IDGT_CV" in df.columns:
        df = df[df["IDGT_CV"].astype(str) == id_goithau]

    if id_hopdong != "Tất cả" and "IDHD_CV" in df.columns:
        df = df[df["IDHD_CV"].astype(str) == id_hopdong]

    return df


# =========================================================
# HÀM HỖ TRỢ UI: LIST LỌC, LIST LIÊN KẾT
# =========================================================

def get_display_lists(all_sheets: dict):
    df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame())
    df_ns = all_sheets.get("1_NHAN_SU", pd.DataFrame())
    df_dv = all_sheets.get("2_DON_VI", pd.DataFrame())
    df_da = all_sheets.get("4_DU_AN", pd.DataFrame())
    df_gt = all_sheets.get("5_GOI_THAU", pd.DataFrame())
    df_hd = all_sheets.get("6_HOP_DONG", pd.DataFrame())
    df_vb = all_sheets.get("3_VAN_BAN", pd.DataFrame())

    list_trang_thai = get_unique_list(df_cv, "TRANG_THAI_TONG")
    list_loai_viec = get_unique_list(df_cv, "LOAI_VIEC")

    list_ns_display = get_display_list(df_ns, "ID_NHAN_SU", "HO_TEN", prefix="Chọn ID")
    list_dv_display = get_display_list(df_dv, "ID_DON_VI", "TEN_DON_VI", prefix="Chọn ID")

    list_da_display = get_display_list(df_da, "ID_DU_AN", "TEN_DU_AN")
    list_gt_display = get_display_list(df_gt, "ID_GOI_THAU", "TEN_GOI_THAU")
    list_hd_display = get_display_list(df_hd, "ID_HOP_DONG", "TEN_HD")
    list_vb_display = get_display_list(df_vb, "ID_VB", "SO_VAN_BAN")

    return {
        "trang_thai": list_trang_thai,
        "loai_viec": list_loai_viec,
        "ns_display": list_ns_display,
        "dv_display": list_dv_display,
        "da_display": list_da_display,
        "gt_display": list_gt_display,
        "hd_display": list_hd_display,
        "vb_display": list_vb_display,
    }


# =========================================================
# HÀM NÚT GỬI EMAIL BÁO CÁO
# =========================================================

def render_email_button(all_sheets: dict, df_report: pd.DataFrame):
    """Đọc danh sách email từ 8_CAU_HINH.EMAIL_BC_CV và tạo nút gửi email."""
    df_cfg = all_sheets.get("8_CAU_HINH", pd.DataFrame())
    if df_cfg.empty or "EMAIL_BC_CV" not in df_cfg.columns:
        st.info("Chưa cấu hình cột EMAIL_BC_CV trong Sheet 8_CAU_HINH.")
        return

    emails = df_cfg["EMAIL_BC_CV"].dropna().astype(str).tolist()
    if not emails:
        st.info("Không tìm thấy email nào trong cột EMAIL_BC_CV.")
        return

    subject = "Bao cao cong viec"
    # Tạo nội dung body đơn giản, bạn có thể tùy chỉnh thêm
    body_lines = ["Kinh gui anh/chi,", "", "Day la bao cao cong viec moi nhat:", ""]
    for _, r in df_report.iterrows():
        ten_viec = r.get("TEN_VIEC") or r.get("NOI_DUNG") or "Khong ten"
        trang_thai = r.get("TRANG_THAI_TONG", "")
        han = format_date_vn(r.get("HAN_CHOT"))
        body_lines.append(f"- {ten_viec} | Trang thai: {trang_thai} | Han chot: {han}")
    body_lines.append("")
    body_lines.append("Trân trọng.")
    body = "\n".join(body_lines)

    # mailto không hỗ trợ full UTF-8 tốt, nên dùng không dấu hoặc chấp nhận 1 phần
    import urllib.parse

    mailto_link = "mailto:{}?subject={}&body={}".format(
        ",".join(emails),
        urllib.parse.quote(subject),
        urllib.parse.quote(body),
    )

    st.markdown(f"[📧 Gửi email báo cáo]({mailto_link})")


# =========================================================
# UI CHÍNH
# =========================================================

def main():
    st.set_page_config(
        page_title="Quản lý công việc EVNGENCO1",
        layout="wide",
    )

    # Tiêu đề & ghi chú tác giả
    st.title("📋 CHƯƠNG TRÌNH QUẢN LÝ CÔNG VIỆC – BAN KHCNĐMST")
    st.caption("Phát triển và công nghệ: Google & Nguyễn Trọng Thắng")
    st.caption("Email liên hệ: thangnt@evngenco1.vn")

    all_sheets = load_all_sheets()
    df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame())
    df_ns = all_sheets.get("1_NHAN_SU", pd.DataFrame())
    df_dv = all_sheets.get("2_DON_VI", pd.DataFrame())

    lists = get_display_lists(all_sheets)

    tab_report, tab_input, tab_data = st.tabs(
        ["📊 Báo cáo & Lọc công việc", "📝 Giao việc mới (Sheet 7)", "📁 Quản lý Dữ liệu Gốc"]
    )

    # -----------------------------------------------------
    # TAB 1: BÁO CÁO & LỌC
    # -----------------------------------------------------
    with tab_report:
        st.header("1. Bộ lọc báo cáo")

        list_idda_cv = get_unique_list(df_cv, "IDDA_CV")
        list_idgt_cv = get_unique_list(df_cv, "IDGT_CV")
        list_idhd_cv = get_unique_list(df_cv, "IDHD_CV")

        with st.sidebar:
            st.header("🎯 Bộ lọc báo cáo")

            chon_trang_thai = st.selectbox(
                "Lọc theo Trạng thái:",
                lists["trang_thai"],
                key="loc_trang_thai",
            )
            st.markdown("---")

            chon_duan = st.selectbox("ID Dự án (IDDA_CV):", list_idda_cv, key="loc_duan")
            chon_goithau = st.selectbox("ID Gói thầu (IDGT_CV):", list_idgt_cv, key="loc_goithau")
            chon_hopdong = st.selectbox("ID Hợp đồng (IDHD_CV):", list_idhd_cv, key="loc_hopdong")
            st.markdown("---")

            st.caption("Lọc theo ngày giao:")
            start_date = st.date_input(
                "Từ ngày:",
                datetime.now().date() - timedelta(days=30),
                key="loc_start_date",
            )
            end_date = st.date_input("Đến ngày:", datetime.now().date(), key="loc_end_date")

        st.subheader("2. Kết quả báo cáo")

        if df_cv.empty:
            st.warning("Không có dữ liệu công việc để báo cáo.")
        else:
            df_report = filter_report(
                df_cv,
                start_date,
                end_date,
                chon_duan,
                chon_goithau,
                chon_hopdong,
                chon_trang_thai,
            )

            if df_report.empty:
                st.info("Không có công việc nào khớp với điều kiện lọc.")
            else:
                st.markdown(f"**Tổng số công việc tìm thấy: {len(df_report)}**")

                # Nút gửi email báo cáo
                render_email_button(all_sheets, df_report)

                st.markdown("---")

                for _, r in df_report.iterrows():
                    ten_viec = r.get("TEN_VIEC") or r.get("NOI_DUNG") or "Không tên"
                    han_val = r.get("HAN_CHOT")
                    trang_thai = r.get("TRANG_THAI_TONG", "")
                    han = format_date_vn(han_val)

                    ten_nguoi_nhan = get_display_name(
                        r.get("NGUOI_NHAN", ""),
                        df_ns,
                        "ID_NHAN_SU",
                        "HO_TEN",
                    )

                    today = datetime.now().date()
                    is_overdue = (
                        pd.notna(han_val)
                        and hasattr(han_val, "date")
                        and han_val.date() < today
                        and trang_thai != "Hoan_Thanh"
                    )

                    status_display = f"**{trang_thai}**"
                    if is_overdue:
                        status_display = f"🔴 **{trang_thai} (QUÁ HẠN)**"
                    elif trang_thai == "Hoan_Thanh":
                        status_display = f"✅ **{trang_thai}**"

                    st.markdown(
                        f"""
                        **• {ten_viec}** (ID: {r.get('ID_CONG_VIEC')})
                        - Người nhận: **{ten_nguoi_nhan}** ({r.get('NGUOI_NHAN')})
                        - Hạn chót: **{han}**
                        - Trạng thái: {status_display}
                        - Liên kết: DA: {r.get('IDDA_CV')}, HD: {r.get('IDHD_CV')}, GT: {r.get('IDGT_CV')}
                        - **Vướng mắc**: *{r.get('VUONG_MAC', '')}*
                        """
                    )
                    st.markdown("---")

    # -----------------------------------------------------
    # TAB 2: GIAO VIỆC MỚI
    # -----------------------------------------------------
    with tab_input:
        st.header("📝 Giao công việc mới (Sheet 7_CONG_VIEC)")

        if df_cv.empty or df_ns.empty:
            st.error(
                "Không đủ dữ liệu (Sheet 7_CONG_VIEC hoặc 1_NHAN_SU) để giao việc. "
                "Vui lòng kiểm tra dữ liệu nguồn."
            )
        else:
            with st.form("form_new_work"):
                st.subheader("1. Thông tin chung (bắt buộc):")

                col1, col2 = st.columns(2)
                with col1:
                    new_ten_viec = st.text_input(
                        "Tên công việc:",
                        placeholder="Nhập tên công việc ngắn gọn",
                    )
                    new_nguoi_nhan_display = st.selectbox(
                        "Người nhận:",
                        lists["ns_display"],
                        index=0,
                    )
                    new_han_chot = st.date_input(
                        "Hạn chót:",
                        datetime.now().date() + timedelta(days=7),
                    )
                    default_idx_trang_thai = (
                        lists["trang_thai"].index("Dang_Lam")
                        if "Dang_Lam" in lists["trang_thai"]
                        else 0
                    )
                    new_trang_thai = st.selectbox(
                        "Trạng thái TỔNG:",
                        lists["trang_thai"],
                        index=default_idx_trang_thai,
                    )
                    new_trang_thai_chi_tiet = st.text_input(
                        "Trạng thái chi tiết:",
                        placeholder="Ví dụ: Đã gửi email, chờ duyệt...",
                    )

                with col2:
                    new_loai_viec = st.selectbox(
                        "Loại công việc:",
                        lists["loai_viec"],
                    )
                    new_nguoi_giao_display = st.selectbox(
                        "Người giao:",
                        lists["ns_display"],
                        index=0,
                    )
                    new_ngay_giao = st.date_input(
                        "Ngày giao:",
                        datetime.now().date(),
                    )
                    new_nguon_giao_viec = st.text_input(
                        "Nguồn giao việc:",
                        placeholder="Văn bản, email, họp...",
                    )
                    # Streamlit không hỗ trợ date_input value=None -> dùng checkbox
                    da_hoan_thanh = st.checkbox("Đã hoàn thành?")
                    new_ngay_thuc_te_xong = (
                        st.date_input("Ngày hoàn thành:", datetime.now().date())
                        if da_hoan_thanh
                        else None
                    )

                new_noi_dung = st.text_area(
                    "Nội dung chi tiết:",
                    placeholder="Mô tả chi tiết công việc...",
                )

                st.subheader("2. Vướng mắc & Ghi chú:")
                col3, col4 = st.columns(2)
                with col3:
                    new_vuong_mac = st.text_area(
                        "Vướng mắc:",
                        placeholder="Chi tiết các vấn đề gặp phải",
                    )
                with col4:
                    new_de_xuat = st.text_area(
                        "Đề xuất:",
                        placeholder="Đề xuất giải pháp/hỗ trợ",
                    )
                    new_ghi_chu = st.text_area(
                        "Ghi chú công việc:",
                        placeholder="Ghi chú chung cho công việc",
                    )

                st.subheader("3. Liên kết dữ liệu (ID):")
                col_link_1, col_link_2, col_link_3 = st.columns(3)
                with col_link_1:
                    new_idda_display = st.selectbox(
                        "ID Dự án (IDDA_CV):",
                        lists["da_display"],
                        index=0,
                    )
                    new_idhd_display = st.selectbox(
                        "ID Hợp đồng (IDHD_CV):",
                        lists["hd_display"],
                        index=0,
                    )
                    new_idvb_display = st.selectbox(
                        "ID Văn bản (IDVB_VAN_BAN):",
                        lists["vb_display"],
                        index=0,
                    )

                with col_link_2:
                    new_idgt_display = st.selectbox(
                        "ID Gói thầu (IDGT_CV):",
                        lists["gt_display"],
                        index=0,
                    )
                    new_iddv_cv_display = st.selectbox(
                        "ID Đơn vị (IDDV_CV):",
                        lists["dv_display"],
                        index=0,
                    )
                    new_nguoi_phoi_hop = st.text_input(
                        "Người phối hợp (ID):",
                        placeholder="Ví dụ: NS002, NS005",
                    )

                submitted = st.form_submit_button(
                    "LƯU VÀ GIAO VIỆC MỚI",
                    type="primary",
                )

                if submitted:
                    id_nguoi_nhan = extract_id_from_display(new_nguoi_nhan_display)
                    id_nguoi_giao = extract_id_from_display(new_nguoi_giao_display)
                    id_da = extract_id_from_display(new_idda_display)
                    id_hd = extract_id_from_display(new_idhd_display)
                    id_gt = extract_id_from_display(new_idgt_display)
                    id_vb = extract_id_from_display(new_idvb_display)
                    id_dv_cv = extract_id_from_display(new_iddv_cv_display)

                    if not new_ten_viec or id_nguoi_nhan == "Chọn ID":
                        st.error("Vui lòng nhập Tên công việc và chọn Người nhận hợp lệ.")
                    else:
                        new_data = {
                            "ten_viec": new_ten_viec,
                            "noi_dung": new_noi_dung,
                            "loai_viec": new_loai_viec,
                            "nguon_giao_viec": new_nguon_giao_viec,
                            "nguoi_giao": id_nguoi_giao if id_nguoi_giao != "Chọn ID" else "",
                            "nguoi_nhan": id_nguoi_nhan,
                            "ngay_giao": new_ngay_giao,
                            "han_chot": new_han_chot,
                            "trang_thai_tong": new_trang_thai,
                            "trang_thai_chi_tiet": new_trang_thai_chi_tiet,
                            "ngay_thuc_te_xong": new_ngay_thuc_te_xong,
                            "idda_cv": id_da if id_da != "Tất cả" else "",
                            "idhd_cv": id_hd if id_hd != "Tất cả" else "",
                            "idgt_cv": id_gt if id_gt != "Tất cả" else "",
                            "idvb_van_ban": id_vb if id_vb != "Tất cả" else "",
                            "iddv_cv": id_dv_cv if id_dv_cv not in ["Chọn ID", "Tất cả"] else "",
                            "nguoi_phoi_hop": new_nguoi_phoi_hop,
                            "vuong_mac": new_vuong_mac,
                            "de_xuat": new_de_xuat,
                            "ghi_chu_cv": new_ghi_chu,
                        }
                        append_new_work(new_data, df_cv)

    # -----------------------------------------------------
    # TAB 3: QUẢN LÝ DỮ LIỆU GỐC
    # -----------------------------------------------------
    with tab_data:
        st.header("📁 Quản lý dữ liệu gốc (Thêm / Sửa / Xóa)")
        st.warning(
            "⚠️ Lưu ý: Chức năng này ghi đè toàn bộ dữ liệu Sheet đã chọn. "
            "Hãy sao lưu Google Sheets trước khi chỉnh sửa."
        )

        editable_sheets = [name for name in REQUIRED_SHEETS if name != "7_CONG_VIEC"]
        sheet_to_display = st.selectbox(
            "Chọn Sheet dữ liệu để chỉnh sửa:",
            editable_sheets,
            key="select_raw_sheet",
        )

        df_goc = all_sheets.get(sheet_to_display, pd.DataFrame())

        if df_goc.empty:
            st.info(
                f"Sheet '{sheet_to_display}' không có dữ liệu để hiển thị hoặc tải thất bại."
            )
        else:
            st.markdown(
                f"**Nội dung Sheet: {sheet_to_display}** "
                f"(Tổng số dòng: {len(df_goc)})"
            )

            # TODO: Nếu sau này muốn liên kết ID tại đây, có thể transform df_goc trước khi hiển thị

            edited_df = st.data_editor(
                df_goc,
                num_rows="dynamic",
                use_container_width=True,
                key="data_editor_goc",
            )

            if st.button(
                f"LƯU CẬP NHẬT CHO SHEET {sheet_to_display}",
                type="primary",
                key="save_raw",
            ):
                final_df = edited_df[~edited_df.index.astype(str).str.startswith("_st")]
                save_raw_sheet(sheet_to_display, final_df)

    st.caption("Dữ liệu được tải từ Google Sheets và được làm mới sau mỗi 10 phút.")


if __name__ == "__main__":
    main()
