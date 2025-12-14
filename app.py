import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
REQUIRED_SHEETS = [
    "1_NHAN_SU",
    "2_DON_VI",
    "3_VAN_BAN",
    "4_DU_AN",
    "5_GOI_THAU",
    "6_HOP_DONG",
    "7_CONG_VIEC",
    "9_CAU_HINH",
    "11_CHAT_GEMINI",
]

DATE_COLS = ["NGAY_GIAO", "HAN_CHOT", "NGAY_THUC_TE_XONG"]

# =========================
# GOOGLE SHEET CONNECT (ĐÃ SỬA LỖI MalformedError)
# =========================
@st.cache_resource
def connect_gsheet():
    # 1. Trích xuất các trường từ Streamlit Secrets
    creds_dict = dict(st.secrets["gdrive"])
    
    # 2. BẮT BUỘC: Thêm các trường bị thiếu mà google.oauth2.service_account.Credentials cần
    # Đây là giải pháp khắc phục lỗi MalformedError: missing fields token_uri/auth_uri
    if 'token_uri' not in creds_dict:
        creds_dict['token_uri'] = "https://oauth2.googleapis.com/token"
    if 'auth_uri' not in creds_dict:
        creds_dict['auth_uri'] = "https://accounts.google.com/o/oauth2/auth"
    if 'auth_provider_x509_cert_url' not in creds_dict:
        creds_dict['auth_provider_x509_cert_url'] = "https://www.googleapis.com/oauth2/v1/certs"

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    # Truyền đối tượng dict đã được bổ sung
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# =========================
# UTILS
# =========================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\u00a0", "", regex=False)
    )
    return df

def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for c in DATE_COLS:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

# =========================
# LOAD ONE SHEET
# =========================
@st.cache_data
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
        df = parse_dates(df)
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"⚠️ Sheet '{sheet_name}' không tồn tại trong Spreadsheet.")
        return pd.DataFrame()
    except Exception as e:
        # Nếu lỗi là PermissionError, sẽ được bắt ở đây
        st.error(f"❌ Lỗi tải Sheet '{sheet_name}': {e}")
        return pd.DataFrame()


# =========================
# LOAD ALL SHEETS
# =========================
@st.cache_data
def load_all_sheets():
    sheets = {}
    for name in REQUIRED_SHEETS:
        sheets[name] = load_sheet_df(name)
    return sheets

# =========================
# REPORT LOGIC
# =========================
def filter_report(df, start_date, end_date, id_duan, id_goithau, id_hopdong):
    df = df.copy()

    if "NGAY_GIAO" in df.columns and pd.api.types.is_datetime64_any_dtype(df["NGAY_GIAO"]):
        df = df[
            (df["NGAY_GIAO"] >= start_date) &
            (df["NGAY_GIAO"] <= end_date)
        ]

    if id_duan != "Tất cả" and "ID_DU_AN" in df.columns:
        df = df[df["ID_DU_AN"] == id_duan]

    if id_goithau != "Tất cả" and "ID_GOI_THAU" in df.columns:
        df = df[df["ID_GOI_THAU"] == id_goithau]

    if id_hopdong != "Tất cả" and "ID_HOP_DONG" in df.columns:
        df = df[df["ID_HOP_DONG"] == id_hopdong]

    return df

# =========================
# UI
# =========================
st.set_page_config(page_title="Quản lý công việc EVNGENCO1", layout="wide")
st.title("📋 QUẢN LÝ CÔNG VIỆC – GOOGLE SHEET")

try:
    all_sheets = load_all_sheets()
    
    # Kiểm tra xem có dữ liệu Sheet 7 (Công việc) không
    if "7_CONG_VIEC" not in all_sheets or all_sheets["7_CONG_VIEC"].empty:
        st.warning("⚠️ Không thể tải dữ liệu Sheet '7_CONG_VIEC' hoặc Sheet rỗng. Vui lòng kiểm tra tên Sheet và quyền truy cập.")
        df_cv = pd.DataFrame()
    else:
        st.success("✅ Kết nối và tải dữ liệu Google Sheets thành công!")
        df_cv = all_sheets["7_CONG_VIEC"]

    # ---------------------
    # FILTER BAR
    # ---------------------
    with st.sidebar:
        st.header("🎯 Bộ lọc báo cáo")

        start_date = st.date_input("Từ ngày", datetime.now().date() - timedelta(days=7))
        end_date = st.date_input("Đến ngày", datetime.now().date())
        
        # Đảm bảo df_cv không rỗng trước khi lấy unique values
        if not df_cv.empty:
            id_duan = ["Tất cả"] + sorted(df_cv.get("ID_DU_AN", pd.Series()).dropna().astype(str).unique().tolist())
            id_goithau = ["Tất cả"] + sorted(df_cv.get("ID_GOI_THAU", pd.Series()).dropna().astype(str).unique().tolist())
            id_hopdong = ["Tất cả"] + sorted(df_cv.get("ID_HOP_DONG", pd.Series()).dropna().astype(str).unique().tolist())
        else:
            id_duan, id_goithau, id_hopdong = ["Tất cả"], ["Tất cả"], ["Tất cả"]

        chon_duan = st.selectbox("ID Dự án", id_duan)
        chon_goithau = st.selectbox("ID Gói thầu", id_goithau)
        chon_hopdong = st.selectbox("ID Hợp đồng", id_hopdong)

    # ---------------------
    # REPORT
    # ---------------------
    st.subheader("📊 KẾT QUẢ BÁO CÁO")
    
    if not df_cv.empty:
        df_report = filter_report(
            df_cv,
            pd.to_datetime(start_date),
            pd.to_datetime(end_date),
            chon_duan,
            chon_goithau,
            chon_hopdong,
        )

        if df_report.empty:
            st.info("Không có công việc nào trong khoảng đã chọn.")
        else:
            for _, r in df_report.iterrows():
                # Lấy tên cột chính xác (thay NOI_DUNG bằng TEN_VIEC hoặc tên phù hợp)
                ten_viec = r.get("TEN_VIEC") or r.get("NOI_DUNG") or "Không tên"
                
                han_val = r.get("HAN_CHOT")
                han = (
                    han_val.strftime("%d/%m/%Y")
                    if pd.notna(han_val) and hasattr(han_val, "strftime")
                    else "—"
                )

                st.markdown(
                    f"""
                    **• {ten_viec}** (ID: {r.get('ID_CONGVIEC')})
                    - Ngày giao: {r.get("NGAY_GIAO").strftime("%d/%m/%Y") if pd.notna(r.get("NGAY_GIAO")) else "—"}
                    - Hạn chót: **{han}**
                    - Trạng thái: {r.get("TRANG_THAI_TONG", "")}
                    """
                )
                st.markdown("---")

    # ---------------------
    # DATA TABS
    # ---------------------
    st.subheader("📁 DỮ LIỆU GỐC")
    tabs = st.tabs(REQUIRED_SHEETS)
    for tab, name in zip(tabs, REQUIRED_SHEETS):
        with tab:
            st.dataframe(all_sheets.get(name, pd.DataFrame()), use_container_width=True)

except Exception as e:
    st.error("❌ Lỗi hệ thống")
    # Hiển thị Traceback chỉ khi lỗi không phải là MalformedError (để tránh hiển thị lỗi đã biết)
    if not ("token_uri" in str(e) and "MalformedError" in str(e)):
        st.exception(e)
