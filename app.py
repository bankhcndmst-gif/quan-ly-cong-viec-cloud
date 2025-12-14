import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
REQUIRED_SHEETS = [
    "1_NHAN_SU", "2_DON_VI", "3_VAN_BAN", "4_DU_AN", "5_GOI_THAU", 
    "6_HOP_DONG", "7_CONG_VIEC", "8_CAU_HINH", "9_CHAT_GEMINI",
]

DATE_COLS = ["NGAY_GIAO", "HAN_CHOT", "NGAY_THUC_TE_XONG"]

# =========================
# GOOGLE SHEET CONNECT (KHÔNG THAY ĐỔI)
# =========================
@st.cache_resource
def connect_gsheet():
    creds_dict = dict(st.secrets["gdrive"])
    
    # Khắc phục lỗi MalformedError
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
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# =========================
# UTILS (ĐÃ THÊM HÀM PHÒNG NGỪA LỖI TÊN CỘT)
# =========================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\u00a0", "", regex=False)
    )
    return df

def remove_duplicate_and_empty_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Xử lý lỗi Duplicate column names found do cột rỗng hoặc trùng lặp."""
    df = df.loc[:, df.columns != '']
    df = df.loc[:, ~df.columns.duplicated(keep='first')]
    return df

def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for c in DATE_COLS:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

# =========================
# LOAD ONE SHEET
# =========================
@st.cache_data(ttl=600) # Thêm cache TTL 10 phút để giảm tải
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
        
        # Chuyển đổi tất cả các cột không phải ngày tháng thành chuỗi để lọc dễ dàng hơn
        for col in df.columns:
             if col not in DATE_COLS and not pd.api.types.is_datetime64_any_dtype(df[col]):
                 df[col] = df[col].astype(str).str.strip()
        
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"⚠️ Sheet '{sheet_name}' không tồn tại trong Spreadsheet. Vui lòng kiểm tra tên Sheet.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi tải Sheet '{sheet_name}': {type(e).__name__} - {e}")
        return pd.DataFrame()


# =========================
# LOAD ALL SHEETS
# =========================
@st.cache_data(ttl=600)
def load_all_sheets():
    sheets = {}
    st.info("Đang tải dữ liệu từ Google Sheets (Cache 10 phút)...")
    for name in REQUIRED_SHEETS:
        sheets[name] = load_sheet_df(name)
    st.success("✅ Kết nối và tải dữ liệu Google Sheets thành công!")
    return sheets

# =========================
# REPORT LOGIC
# =========================
def filter_report(df, start_date, end_date, id_duan, id_goithau, id_hopdong, trang_thai):
    df = df.copy() 

    # Lọc theo Ngày Giao
    if "NGAY_GIAO" in df.columns and pd.api.types.is_datetime64_any_dtype(df["NGAY_GIAO"]):
        df = df[
            (df["NGAY_GIAO"].dt.date >= start_date) & # So sánh với .dt.date
            (df["NGAY_GIAO"].dt.date <= end_date)
        ]

    # Lọc theo TRẠNG THÁI TỔNG
    if trang_thai != "Tất cả" and "TRANG_THAI_TONG" in df.columns:
        df = df[df["TRANG_THAI_TONG"].astype(str) == trang_thai]

    # Lọc theo ID (sử dụng tên cột chính xác trong Sheet 7: IDDA_CV, IDGT_CV, IDHD_CV)
    if id_duan != "Tất cả" and "IDDA_CV" in df.columns:
        df = df[df["IDDA_CV"].astype(str) == id_duan]

    if id_goithau != "Tất cả" and "IDGT_CV" in df.columns:
        df = df[df["IDGT_CV"].astype(str) == id_goithau]

    if id_hopdong != "Tất cả" and "IDHD_CV" in df.columns:
        df = df[df["IDHD_CV"].astype(str) == id_hopdong]
        
    return df

# =========================
# HÀM LƯU DỮ LIỆU MỚI (CHỈ MÔ PHỎNG)
# =========================
def append_new_work(new_data: dict, all_sheets: dict):
    # Lấy sheet công việc và nhân sự
    df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame())
    
    if df_cv.empty:
        st.error("Không thể thêm công việc: Sheet 7_CONG_VIEC rỗng.")
        return
        
    # Tạo ID mới
    max_id_num = df_cv['ID_CONG_VIEC'].str.extract(r'(\d+)').astype(float).max()
    new_id_num = int(max_id_num) + 1 if pd.notna(max_id_num) else 1
    new_id = f"CV{new_id_num:03d}"
    
    # Chuẩn bị dữ liệu cho dòng mới
    new_row = {
        'ID_CONG_VIEC': new_id,
        'TEN_VIEC': new_data['ten_viec'],
        'NOI_DUNG': new_data['noi_dung'],
        'LOAI_VIEC': new_data['loai_viec'],
        'NGUOI_GIAO': new_data['nguoi_giao'],
        'NGUOI_NHAN': new_data['nguoi_nhan'],
        'NGAY_GIAO': new_data['ngay_giao'].strftime('%Y-%m-%d'),
        'HAN_CHOT': new_data['han_chot'].strftime('%Y-%m-%d'),
        'TRANG_THAI_TONG': new_data['trang_thai_tong'],
        'IDDA_CV': new_data['idda_cv'],
        'IDHD_CV': new_data['idhd_cv'],
        'IDGT_CV': new_data['idgt_cv'],
        'NGUOI_PHOI_HOP': new_data['nguoi_phoi_hop'],
        # Thêm các cột còn lại nếu cần (ví dụ: VUONG_MAC, DE_XUAT, v.v.)
    }

    try:
        # Ghi dữ liệu vào Google Sheet (thực tế)
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
        ws_cv = sh.worksheet("7_CONG_VIEC")
        
        # Ghi dòng mới (chỉ ghi các giá trị)
        header = ws_cv.row_values(1)
        values_to_append = [new_row.get(h, '') for h in header]
        
        ws_cv.append_row(values_to_append, value_input_option='USER_ENTERED')
        
        st.success(f"🎉 Đã thêm công việc mới thành công: **{new_id} - {new_data['ten_viec']}**")
        st.cache_data.clear() # Xóa cache để tải lại dữ liệu mới
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Lỗi khi ghi vào Google Sheet: {e}")


# =========================
# UI
# =========================
st.set_page_config(page_title="Quản lý công việc EVNGENCO1", layout="wide")
st.title("📋 HỆ THỐNG QUẢN LÝ CÔNG VIỆC – GOOGLE SHEET")

# Tải dữ liệu
all_sheets = load_all_sheets()
df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame())
df_ns = all_sheets.get("1_NHAN_SU", pd.DataFrame())


# ---------------------
# LẤY DANH SÁCH LỌC VÀ NHẬP LIỆU
# ---------------------
def get_unique_list(df, col_name, prefix="Tất cả"):
    if df.empty or col_name not in df.columns:
        return [prefix]
    # Lọc bỏ giá trị rỗng/NaT, chuyển sang chuỗi, lấy unique
    unique_list = df[col_name].dropna().astype(str).unique().tolist()
    # Nếu là ID, chuyển về dạng đơn giản hơn nếu cần
    return [prefix] + sorted(unique_list)

# Danh sách cho bộ lọc và nhập liệu
list_trang_thai = get_unique_list(df_cv, "TRANG_THAI_TONG")
list_du_an = get_unique_list(all_sheets.get("4_DU_AN", pd.DataFrame()), "ID_DU_AN")
list_goi_thau = get_unique_list(all_sheets.get("5_GOI_THAU", pd.DataFrame()), "ID_GOI_THAU")
list_hop_dong = get_unique_list(all_sheets.get("6_HOP_DONG", pd.DataFrame()), "ID_HOP_DONG")
list_nhan_su_id = get_unique_list(df_ns, "ID_NHAN_SU", prefix="Chọn ID")
list_loai_viec = get_unique_list(df_cv, "LOAI_VIEC")


# ---------------------
# CẤU TRÚC GIAO DIỆN CHÍNH
# ---------------------

tab_report, tab_input, tab_data = st.tabs(["📊 Báo Cáo & Lọc Công Việc", "📝 Giao Việc Mới (Sheet 7)", "📁 Dữ Liệu Gốc"])

# ---------------------
# TAB 1: BÁO CÁO VÀ LỌC
# ---------------------
with tab_report:
    st.header("1. BỘ LỌC BÁO CÁO")
    
    # 1. SIDEBAR FILTER
    with st.sidebar:
        st.header("🎯 Bộ lọc báo cáo")
        
        # Thêm TRANG THÁI TỔNG
        chon_trang_thai = st.selectbox("Lọc theo Trạng Thái:", list_trang_thai, key="loc_trang_thai")
        st.markdown("---")
        
        # Các bộ lọc ID khác (đã lấy từ Sheet 7_CONG_VIEC)
        chon_duan = st.selectbox("ID Dự án (IDDA_CV):", list_du_an, key="loc_duan")
        chon_goithau = st.selectbox("ID Gói thầu (IDGT_CV):", list_goi_thau, key="loc_goithau")
        chon_hopdong = st.selectbox("ID Hợp đồng (IDHD_CV):", list_hop_dong, key="loc_hopdong")
        st.markdown("---")
        
        st.caption("Lọc theo ngày giao:")
        start_date = st.date_input("Từ ngày:", datetime.now().date() - timedelta(days=30), key="loc_start_date")
        end_date = st.date_input("Đến ngày:", datetime.now().date(), key="loc_end_date")

    
    st.subheader("2. KẾT QUẢ BÁO CÁO")
    
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
            chon_trang_thai # Thêm trạng thái vào hàm lọc
        )

        if df_report.empty:
            st.info("Không có công việc nào khớp với điều kiện lọc.")
        else:
            st.markdown(f"**Tổng số công việc tìm thấy: {len(df_report)}**")
            for _, r in df_report.iterrows():
                # Logic hiển thị đã được cải thiện
                ten_viec = r.get("TEN_VIEC") or r.get("NOI_DUNG") or "Không tên"
                han_val = r.get("HAN_CHOT")
                trang_thai = r.get("TRANG_THAI_TONG", "")
                
                han = (han_val.strftime("%d/%m/%Y") if pd.notna(han_val) and hasattr(han_val, "strftime") else "—")
                
                # Logic quá hạn
                today = datetime.now().date()
                is_overdue = pd.notna(han_val) and han_val.date() < today and trang_thai != "Hoan_Thanh"
                status_display = f"**{trang_thai}**"
                if is_overdue:
                    status_display = f"🔴 **{trang_thai} (QUÁ HẠN)**"
                elif trang_thai == "Hoan_Thanh":
                    status_display = f"✅ **{trang_thai}**"
                
                st.markdown(
                    f"""
                    **• {ten_viec}** (ID: {r.get('ID_CONG_VIEC')})
                    - Người nhận: {r.get('NGUOI_NHAN')}
                    - Ngày giao: {r.get("NGAY_GIAO").strftime("%d/%m/%Y") if pd.notna(r.get("NGAY_GIAO")) else "—"}
                    - Hạn chót: **{han}**
                    - Trạng thái: {status_display}
                    """
                )
                st.markdown("---")

# ---------------------
# TAB 2: GIAO VIỆC MỚI (NHẬP LIỆU)
# ---------------------
with tab_input:
    st.header("📝 Giao Công Việc Mới (Sheet 7_CONG_VIEC)")
    
    if df_cv.empty or df_ns.empty:
        st.error("Không đủ dữ liệu (Sheet 7 hoặc 1) để thực hiện giao việc. Vui lòng kiểm tra các cảnh báo.")
    else:
        with st.form("form_new_work"):
            
            st.subheader("Thông tin Công việc:")
            
            col_a, col_b = st.columns(2)
            with col_a:
                new_ten_viec = st.text_input("Tên Công Việc:", placeholder="Nhập tên công việc ngắn gọn")
                new_nguoi_nhan = st.selectbox("Người Nhận (ID):", list_nhan_su_id, index=0)
                new_han_chot = st.date_input("Hạn Chót:", datetime.now().date() + timedelta(days=7))
                new_trang_thai = st.selectbox("Trạng Thái Mặc Định:", list_trang_thai, index=1 if "Dang_Lam" in list_trang_thai else 0)
                
            with col_b:
                new_loai_viec = st.selectbox("Loại Công Việc:", list_loai_viec)
                new_nguoi_giao = st.selectbox("Người Giao (ID):", list_nhan_su_id, index=0)
                new_ngay_giao = st.date_input("Ngày Giao:", datetime.now().date())
                new_phoi_hop = st.text_input("Người Phối Hợp (ID):", placeholder="Ví dụ: NS002, NS005")

            new_noi_dung = st.text_area("Nội Dung Chi Tiết:", placeholder="Mô tả chi tiết công việc...")

            st.subheader("Liên kết Dữ liệu (ID):")
            col_link_a, col_link_b, col_link_c = st.columns(3)
            with col_link_a:
                new_idda = st.selectbox("ID Dự án (IDDA_CV):", list_du_an, index=0)
            with col_link_b:
                new_idhd = st.selectbox("ID Hợp đồng (IDHD_CV):", list_hop_dong, index=0)
            with col_link_c:
                new_idgt = st.selectbox("ID Gói thầu (IDGT_CV):", list_goi_thau, index=0)

            submitted = st.form_submit_button("LƯU VÀ GIAO VIỆC MỚI", type="primary")

            if submitted:
                if not new_ten_viec or new_nguoi_nhan == "Chọn ID":
                    st.error("Vui lòng nhập Tên Công Việc và chọn Người Nhận hợp lệ.")
                else:
                    new_data = {
                        'ten_viec': new_ten_viec,
                        'noi_dung': new_noi_dung,
                        'loai_viec': new_loai_viec,
                        'nguoi_giao': new_nguoi_giao if new_nguoi_giao != "Chọn ID" else "",
                        'nguoi_nhan': new_nguoi_nhan,
                        'ngay_giao': new_ngay_giao,
                        'han_chot': new_han_chot,
                        'trang_thai_tong': new_trang_thai,
                        'idda_cv': new_idda if new_idda != "Tất cả" else "",
                        'idhd_cv': new_idhd if new_idhd != "Tất cả" else "",
                        'idgt_cv': new_idgt if new_idgt != "Tất cả" else "",
                        'nguoi_phoi_hop': new_phoi_hop,
                    }
                    append_new_work(new_data, all_sheets)


# ---------------------
# TAB 3: DỮ LIỆU GỐC
# ---------------------
with tab_data:
    st.header("📁 Xem Dữ Liệu Gốc")
    
    # Sử dụng Selectbox để chọn Sheet thay vì Tabs quá nhiều
    sheet_to_display = st.selectbox("Chọn Sheet Dữ Liệu:", REQUIRED_SHEETS, key="select_raw_sheet")

    df_display = all_sheets.get(sheet_to_display, pd.DataFrame())
    if df_display.empty:
        st.info(f"Sheet '{sheet_to_display}' không có dữ liệu để hiển thị hoặc tải thất bại.")
    else:
        st.dataframe(df_display, use_container_width=True)

# ---------------------
# LƯU Ý
# ---------------------
st.caption("Lưu ý: Dữ liệu được tải từ Google Sheets và được làm mới sau mỗi 10 phút. Việc thêm công việc sẽ ghi trực tiếp vào Sheet gốc.")
