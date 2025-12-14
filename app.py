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
# GOOGLE SHEET CONNECT
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
# UTILS (ĐÃ THÊM HÀM GET_UNIQUE_LIST)
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

def get_unique_list(df, col_name, prefix="Tất cả"):
    """Lấy danh sách các giá trị duy nhất (để dùng cho list_trang_thai và list_loai_viec)."""
    if df.empty or col_name not in df.columns:
        return [prefix]
    unique_list = df[col_name].dropna().astype(str).unique().tolist()
    return [prefix] + sorted(unique_list)

def get_display_list(df: pd.DataFrame, id_col: str, name_col: str, prefix="Tất cả"):
    """Tạo danh sách cho Selectbox: [ID: Name]"""
    if df.empty or id_col not in df.columns or name_col not in df.columns:
        return [prefix]
        
    df_temp = df[[id_col, name_col]].dropna()
    df_temp['DISPLAY'] = df_temp[id_col].astype(str) + ": " + df_temp[name_col].astype(str)
    
    unique_list = df_temp['DISPLAY'].unique().tolist()
    return [prefix] + sorted(unique_list)

def extract_id_from_display(display_str: str) -> str:
    """Trích xuất ID từ chuỗi [ID: Name]"""
    if ":" in display_str:
        return display_str.split(":")[0].strip()
    return display_str
    
def get_display_name(id_value: str, df: pd.DataFrame, id_col: str, name_col: str) -> str:
    """Tra cứu Tên từ ID"""
    if df.empty or id_col not in df.columns or name_col not in df.columns or not id_value:
        return id_value
    
    result = df[df[id_col].astype(str).str.strip() == id_value.strip()]
    if not result.empty:
        return result[name_col].iloc[0]
    return id_value


# =========================
# LOAD ONE SHEET
# =========================
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
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"⚠️ Sheet '{sheet_name}' không tồn tại. Vui lòng kiểm tra tên Sheet.")
        return pd.DataFrame()
    except gspread.exceptions.PermissionError:
        st.error(f"❌ Lỗi truy cập Sheet '{sheet_name}'. Vui lòng chia sẻ lại Google Sheet cho Service Account.")
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
    st.info("Đang tải dữ liệu từ Google Sheets...")
    for name in REQUIRED_SHEETS:
        sheets[name] = load_sheet_df(name)
    st.success("✅ Kết nối và tải dữ liệu Google Sheets thành công!")
    return sheets

# =========================
# HÀM GHI DỮ LIỆU
# =========================
def save_raw_sheet(sheet_name: str, edited_df: pd.DataFrame):
    """Ghi DataFrame mới vào Sheet gốc."""
    try:
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        
        # Xóa dữ liệu cũ (Giữ lại hàng tiêu đề)
        ws.clear()
        
        # Ghi dữ liệu mới
        data_to_write = [edited_df.columns.tolist()] + edited_df.values.tolist()
        
        ws.append_rows(data_to_write, value_input_option='USER_ENTERED')
        
        st.success(f"🎉 Đã lưu và cập nhật Sheet '{sheet_name}' thành công!")
        st.cache_data.clear() # Xóa cache để tải lại dữ liệu mới
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Lỗi khi ghi vào Sheet '{sheet_name}': {e}")

def append_new_work(new_data: dict, all_sheets):
    """Thêm dòng công việc mới vào Sheet 7_CONG_VIEC."""
    df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame())
    
    # Tạo ID mới
    max_id_num = df_cv['ID_CONG_VIEC'].str.extract(r'(\d+)').astype(float).max()
    new_id_num = int(max_id_num) + 1 if pd.notna(max_id_num) else 1
    new_id = f"CV{new_id_num:03d}"

    try:
        gc = connect_gsheet()
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
        ws_cv = sh.worksheet("7_CONG_VIEC")
        
        # Sắp xếp giá trị theo thứ tự cột trong Sheet
        header = ws_cv.row_values(1)
        
        new_row_dict = {
            'ID_CONG_VIEC': new_id,
            'TEN_VIEC': new_data['ten_viec'],
            'NOI_DUNG': new_data['noi_dung'],
            'LOAI_VIEC': new_data['loai_viec'],
            'NGUON_GIAO_VIEC': new_data['nguon_giao_viec'], 
            'NGUOI_GIAO': new_data['nguoi_giao'],
            'NGUOI_NHAN': new_data['nguoi_nhan'],
            'NGAY_GIAO': new_data['ngay_giao'].strftime('%Y-%m-%d'),
            'HAN_CHOT': new_data['han_chot'].strftime('%Y-%m-%d'),
            'NGUOI_PHOI_HOP': new_data['nguoi_phoi_hop'],
            'TRANG_THAI_TONG': new_data['trang_thai_tong'],
            'TRANG_THAI_CHI_TIET': new_data['trang_thai_chi_tiet'], 
            'NGAY_THUC_TE_XONG': new_data['ngay_thuc_te_xong'], 
            'IDVB_VAN_BAN': new_data['idvb_van_ban'], 
            'IDHD_CV': new_data['idhd_cv'],
            'IDDA_CV': new_data['idda_cv'],
            'IDGT_CV': new_data['idgt_cv'],
            'VUONG_MAC': new_data['vuong_mac'], 
            'DE_XUAT': new_data['de_xuat'], 
            'IDDV_CV': new_data['iddv_cv'], 
            'GHI_CHU_CV': new_data['ghi_chu_cv'], 
        }
        
        values_to_append = [new_row_dict.get(h, '') for h in header]
        
        ws_cv.append_row(values_to_append, value_input_option='USER_ENTERED')
        
        st.success(f"🎉 Đã thêm công việc mới thành công: **{new_id} - {new_data['ten_viec']}**")
        st.cache_data.clear()
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Lỗi khi ghi vào Google Sheet: {e}")


# =========================
# REPORT LOGIC
# =========================
def filter_report(df, start_date, end_date, id_duan, id_goithau, id_hopdong, trang_thai):
    df = df.copy() 

    if "NGAY_GIAO" in df.columns and pd.api.types.is_datetime64_any_dtype(df["NGAY_GIAO"]):
        df = df[
            (df["NGAY_GIAO"].dt.date >= start_date) & 
            (df["NGAY_GIAO"].dt.date <= end_date)
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

# =========================
# UI
# =========================
st.set_page_config(page_title="Quản lý công việc EVNGENCO1", layout="wide")
st.title("📋 HỆ THỐNG QUẢN LÝ CÔNG VIỆC – GOOGLE SHEET")

# Tải dữ liệu
all_sheets = load_all_sheets()
df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame())
df_ns = all_sheets.get("1_NHAN_SU", pd.DataFrame())
df_dv = all_sheets.get("2_DON_VI", pd.DataFrame())


# ---------------------
# LẤY DANH SÁCH LỌC VÀ NHẬP LIỆU (ĐÃ FIX NAMEERROR)
# ---------------------
def get_display_lists(df_cv, df_ns, df_dv, all_sheets):
    list_trang_thai = get_unique_list(df_cv, "TRANG_THAI_TONG")
    list_loai_viec = get_unique_list(df_cv, "LOAI_VIEC")

    # Danh sách ID (có tên hiển thị)
    list_ns_display = get_display_list(df_ns, "ID_NHAN_SU", "HO_TEN", prefix="Chọn ID")
    list_dv_display = get_display_list(df_dv, "ID_DON_VI", "TEN_DON_VI", prefix="Chọn ID")

    # Danh sách ID liên kết
    df_da = all_sheets.get("4_DU_AN", pd.DataFrame())
    df_gt = all_sheets.get("5_GOI_THAU", pd.DataFrame())
    df_hd = all_sheets.get("6_HOP_DONG", pd.DataFrame())
    df_vb = all_sheets.get("3_VAN_BAN", pd.DataFrame())
    
    list_da_display = get_display_list(df_da, "ID_DU_AN", "TEN_DU_AN")
    list_gt_display = get_display_list(df_gt, "ID_GOI_THAU", "TEN_GOI_THAU")
    list_hd_display = get_display_list(df_hd, "ID_HOP_DONG", "TEN_HD")
    list_vb_display = get_display_list(df_vb, "ID_VB", "SO_VAN_BAN")
    
    return list_trang_thai, list_loai_viec, list_ns_display, list_dv_display, list_da_display, list_gt_display, list_hd_display, list_vb_display

(list_trang_thai, list_loai_viec, list_ns_display, list_dv_display, 
 list_da_display, list_gt_display, list_hd_display, list_vb_display) = get_display_lists(df_cv, df_ns, df_dv, all_sheets)


# ---------------------
# CẤU TRÚC GIAO DIỆN CHÍNH
# ---------------------
tab_report, tab_input, tab_data = st.tabs(["📊 Báo Cáo & Lọc Công Việc", "📝 Giao Việc Mới (Sheet 7)", "📁 Quản lý Dữ Liệu Gốc"])

# ---------------------
# TAB 1: BÁO CÁO VÀ LỌC
# ---------------------
with tab_report:
    st.header("1. BỘ LỌC BÁO CÁO")
    
    # Lấy danh sách ID thô cho bộ lọc (lấy từ các ID đã có trong Sheet 7_CONG_VIEC)
    list_idda_cv = get_unique_list(df_cv, "IDDA_CV")
    list_idgt_cv = get_unique_list(df_cv, "IDGT_CV")
    list_idhd_cv = get_unique_list(df_cv, "IDHD_CV")

    # 1. SIDEBAR FILTER
    with st.sidebar:
        st.header("🎯 Bộ lọc báo cáo")
        
        chon_trang_thai = st.selectbox("Lọc theo Trạng Thái:", list_trang_thai, key="loc_trang_thai")
        st.markdown("---")
        
        # SỬ DỤNG ID THÔ CHO LỌC
        chon_duan = st.selectbox("ID Dự án (IDDA_CV):", list_idda_cv, key="loc_duan")
        chon_goithau = st.selectbox("ID Gói thầu (IDGT_CV):", list_idgt_cv, key="loc_goithau")
        chon_hopdong = st.selectbox("ID Hợp đồng (IDHD_CV):", list_idhd_cv, key="loc_hopdong")
        st.markdown("---")
        
        st.caption("Lọc theo ngày giao:")
        start_date = st.date_input("Từ ngày:", datetime.now().date() - timedelta(days=30), key="loc_start_date")
        end_date = st.date_input("Đến ngày:", datetime.now().date(), key="loc_end_date")

    
    st.subheader("2. KẾT QUẢ BÁO CÁO")
    
    if df_cv.empty:
         st.warning("Không có dữ liệu công việc để báo cáo.")
    else:
        df_report = filter_report(
            df_cv, start_date, end_date, chon_duan, chon_goithau, chon_hopdong, chon_trang_thai
        )

        if df_report.empty:
            st.info("Không có công việc nào khớp với điều kiện lọc.")
        else:
            st.markdown(f"**Tổng số công việc tìm thấy: {len(df_report)}**")
            for _, r in df_report.iterrows():
                ten_viec = r.get("TEN_VIEC") or r.get("NOI_DUNG") or "Không tên"
                han_val = r.get("HAN_CHOT")
                trang_thai = r.get("TRANG_THAI_TONG", "")
                
                han = (han_val.strftime("%d/%m/%Y") if pd.notna(han_val) and hasattr(han_val, "strftime") else "—")
                
                # Hiển thị Tên người nhận
                ten_nguoi_nhan = get_display_name(r.get('NGUOI_NHAN'), df_ns, "ID_NHAN_SU", "HO_TEN")
                
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
                    - Người nhận: **{ten_nguoi_nhan}** ({r.get('NGUOI_NHAN')})
                    - Hạn chót: **{han}**
                    - Trạng thái: {status_display}
                    - Liên kết: DA: {r.get('IDDA_CV')}, HD: {r.get('IDHD_CV')}, GT: {r.get('IDGT_CV')}
                    - **Vướng mắc**: *{r.get('VUONG_MAC')}*
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
            
            # --- CỘT CƠ BẢN ---
            st.subheader("1. Thông tin Chung (Bắt buộc):")
            col1, col2 = st.columns(2)
            with col1:
                new_ten_viec = st.text_input("Tên Công Việc:", placeholder="Nhập tên công việc ngắn gọn")
                new_nguoi_nhan_display = st.selectbox("Người Nhận:", list_ns_display, index=0)
                new_han_chot = st.date_input("Hạn Chót:", datetime.now().date() + timedelta(days=7))
                new_trang_thai = st.selectbox("Trạng Thái TỔNG:", list_trang_thai, index=1 if "Dang_Lam" in list_trang_thai else 0)
                new_trang_thai_chi_tiet = st.text_input("Trạng Thái Chi Tiết:", placeholder="Ví dụ: Đã gửi email, chờ duyệt...")
            with col2:
                new_loai_viec = st.selectbox("Loại Công Việc:", list_loai_viec)
                new_nguoi_giao_display = st.selectbox("Người Giao:", list_ns_display, index=0)
                new_ngay_giao = st.date_input("Ngày Giao:", datetime.now().date())
                new_nguon_giao_viec = st.text_input("Nguồn Giao Việc:", placeholder="Văn bản, email, họp...")
                new_ngay_thuc_te_xong = st.date_input("Ngày Hoàn Thành (Nếu đã xong):", value=None)
            
            new_noi_dung = st.text_area("Nội Dung Chi Tiết:", placeholder="Mô tả chi tiết công việc...")

            # --- CỘT VUÔNG MẮC & KHÁC ---
            st.subheader("2. Vướng Mắc & Ghi Chú:")
            col3, col4 = st.columns(2)
            with col3:
                new_vuong_mac = st.text_area("Vướng Mắc:", placeholder="Chi tiết các vấn đề gặp phải")
            with col4:
                new_de_xuat = st.text_area("Đề Xuất:", placeholder="Đề xuất giải pháp/hỗ trợ")
                new_ghi_chu = st.text_area("Ghi Chú CV:", placeholder="Ghi chú chung cho công việc")

            # --- CỘT LIÊN KẾT ---
            st.subheader("3. Liên kết Dữ liệu (ID):")
            col_link_1, col_link_2, col_link_3 = st.columns(3)
            with col_link_1:
                new_idda_display = st.selectbox("ID Dự án (IDDA_CV):", list_da_display, index=0)
                new_idhd_display = st.selectbox("ID Hợp đồng (IDHD_CV):", list_hd_display, index=0)
                new_idvb_display = st.selectbox("ID Văn bản (IDVB_VAN_BAN):", list_vb_display, index=0)
            with col_link_2:
                new_idgt_display = st.selectbox("ID Gói thầu (IDGT_CV):", list_gt_display, index=0)
                new_iddv_cv_display = st.selectbox("ID Đơn vị (IDDV_CV):", list_dv_display, index=0)
                new_nguoi_phoi_hop = st.text_input("Người Phối Hợp (ID):", placeholder="Ví dụ: NS002, NS005")


            submitted = st.form_submit_button("LƯU VÀ GIAO VIỆC MỚI", type="primary")

            if submitted:
                # Trích xuất ID từ chuỗi hiển thị
                id_nguoi_nhan = extract_id_from_display(new_nguoi_nhan_display)
                id_nguoi_giao = extract_id_from_display(new_nguoi_giao_display)
                id_da = extract_id_from_display(new_idda_display)
                id_hd = extract_id_from_display(new_idhd_display)
                id_gt = extract_id_from_display(new_idgt_display)
                id_vb = extract_id_from_display(new_idvb_display)
                id_dv_cv = extract_id_from_display(new_iddv_cv_display)

                if not new_ten_viec or id_nguoi_nhan == "Chọn ID":
                    st.error("Vui lòng nhập Tên Công Việc và chọn Người Nhận hợp lệ.")
                else:
                    new_data = {
                        'ten_viec': new_ten_viec, 'noi_dung': new_noi_dung, 'loai_viec': new_loai_viec,
                        'nguon_giao_viec': new_nguon_giao_viec,
                        'nguoi_giao': id_nguoi_giao if id_nguoi_giao != "Chọn ID" else "",
                        'nguoi_nhan': id_nguoi_nhan,
                        'ngay_giao': new_ngay_giao, 'han_chot': new_han_chot, 
                        'trang_thai_tong': new_trang_thai,
                        'trang_thai_chi_tiet': new_trang_thai_chi_tiet,
                        'ngay_thuc_te_xong': new_ngay_thuc_te_xong,
                        
                        'idda_cv': id_da if id_da != "Tất cả" else "",
                        'idhd_cv': id_hd if id_hd != "Tất cả" else "",
                        'idgt_cv': id_gt if id_gt != "Tất cả" else "",
                        'idvb_van_ban': id_vb if id_vb != "Tất cả" else "",
                        'iddv_cv': id_dv_cv if id_dv_cv != "Chọn ID" else "",
                        
                        'nguoi_phoi_hop': new_nguoi_phoi_hop,
                        'vuong_mac': new_vuong_mac,
                        'de_xuat': new_de_xuat,
                        'ghi_chu_cv': new_ghi_chu,
                    }
                    append_new_work(new_data, all_sheets)


# ---------------------
# TAB 3: DỮ LIỆU GỐC (THÊM CHỨC NĂNG SỬA/LƯU)
# ---------------------
with tab_data:
    st.header("📁 Quản lý Dữ Liệu Gốc (Thêm, Sửa, Xóa)")
    st.warning("⚠️ CHÚ Ý: Chức năng này ghi đè toàn bộ dữ liệu Sheet đã chọn. Hãy cẩn thận!")
    
    # Loại trừ Sheet 7 vì nó được quản lý qua Tab Giao Việc
    editable_sheets = [name for name in REQUIRED_SHEETS if name != "7_CONG_VIEC"]
    sheet_to_display = st.selectbox("Chọn Sheet Dữ Liệu để chỉnh sửa:", editable_sheets, key="select_raw_sheet")

    df_goc = all_sheets.get(sheet_to_display, pd.DataFrame())
    
    if df_goc.empty:
        st.info(f"Sheet '{sheet_to_display}' không có dữ liệu để hiển thị hoặc tải thất bại.")
    else:
        st.markdown(f"**Nội dung Sheet: {sheet_to_display}** (Tổng số dòng: {len(df_goc)})")
        
        # Cho phép người dùng thêm/xóa dòng, chỉnh sửa
        edited_df = st.data_editor(
            df_goc,
            num_rows="dynamic", 
            use_container_width=True,
            key="data_editor_goc"
        )
        
        if st.button(f"LƯU CẬP NHẬT CHO SHEET {sheet_to_display}", type="primary", key="save_raw"):
            # Lọc các dòng bị xóa (index bắt đầu bằng _st)
            final_df = edited_df[~edited_df.index.astype(str).str.startswith('_st')]
            save_raw_sheet(sheet_to_display, final_df)


# ---------------------
# LƯU Ý
# ---------------------
st.caption("Lưu ý: Dữ liệu được tải từ Google Sheets và được làm mới sau mỗi 10 phút.")
