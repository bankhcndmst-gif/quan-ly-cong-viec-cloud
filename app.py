import streamlit as st
import gspread
import pandas as pd
from io import BytesIO

# --- Cấu hình chung ---
st.set_page_config(layout="wide", page_title="Hệ thống Quản lý Công việc", page_icon="📈")
st.title("📈 Hệ thống Quản lý Công việc (Test Cloud)")

# --- Hàm Tải Dữ liệu (Dùng cache để tối ưu) ---
@st.cache_data(ttl=600)  # Cache trong 10 phút
def load_data_from_gsheets():
    try:
        # Lấy thông tin kết nối từ Streamlit Secrets (.streamlit/secrets.toml)
        # Sử dụng BytesIO để xử lý private_key (có chứa ký tự \n)
        
        # 1. Kết nối với Google API bằng Service Account
        credentials = {
            "type": "service_account",
            "project_id": st.secrets["gdrive"]["project_id"],
            "private_key_id": st.secrets["gdrive"]["private_key_id"],
            "private_key": st.secrets["gdrive"]["private_key"].replace('\\n', '\n'),
            "client_email": st.secrets["gdrive"]["client_email"],
            "client_id": st.secrets["gdrive"]["client_id"],
            "auth_uri": st.secrets["gdrive"]["auth_uri"],
            "token_uri": st.secrets["gdrive"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gdrive"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gdrive"]["client_x509_cert_url"],
            "universe_domain": st.secrets["gdrive"]["universe_domain"]
        }
        
        gc = gspread.service_account_from_dict(credentials)
        
        # 2. Mở Google Sheet theo ID
        spreadsheet_id = st.secrets["gdrive"]["spreadsheet_id"]
        sh = gc.open_by_key(spreadsheet_id)

        # 3. Tải dữ liệu từ các sheets cần thiết
        sheets = {}
        sheet_titles = ["1_NHAN_SU", "7_CONG_VIEC", "2_NHIEM_VU", "4_TIEU_CHI"]
        
        for title in sheet_titles:
            try:
                worksheet = sh.worksheet(title)
                data = worksheet.get_all_records()
                sheets[title] = pd.DataFrame(data)
            except gspread.WorksheetNotFound:
                st.error(f"Lỗi: Không tìm thấy sheet '{title}' trong Google Sheet. Vui lòng kiểm tra lại tên sheet.")
                sheets[title] = pd.DataFrame() # Trả về DF rỗng nếu lỗi
            except Exception as e:
                st.error(f"Lỗi khi tải sheet '{title}': {e}")
                sheets[title] = pd.DataFrame()
                
        return sheets

    except Exception as e:
        st.error(f"Lỗi kết nối hoặc cấu hình: Vui lòng kiểm tra file secrets.toml và quyền chia sẻ Google Sheet. Chi tiết: {e}")
        return None

# --- Chạy Ứng dụng ---
data_sheets = load_data_from_gsheets()

if data_sheets:
    
    st.success("✅ Kết nối và tải dữ liệu Google Sheets thành công!")
    
    # ----------------------------------------------------
    # PHẦN HIỂN THỊ DỮ LIỆU
    # ----------------------------------------------------
    
    st.subheader("Bảng Dữ liệu Đã Tải về")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Nhân Sự (1_NHAN_SU)", 
        "Công Việc (7_CONG_VIEC)", 
        "Nhiệm Vụ (2_NHIEM_VU)", 
        "Tiêu Chí (4_TIEU_CHI)"
    ])

    with tab1:
        st.dataframe(data_sheets.get("1_NHAN_SU", pd.DataFrame()), use_container_width=True)

    with tab2:
        df_cv = data_sheets.get("7_CONG_VIEC", pd.DataFrame())
        st.dataframe(df_cv, use_container_width=True)
        
        # Ví dụ phân tích nhỏ: Thống kê trạng thái công việc
        if not df_cv.empty and 'Trạng thái CV' in df_cv.columns:
            st.markdown("##### Thống kê Trạng thái Công việc:")
            status_counts = df_cv['Trạng thái CV'].value_counts().reset_index()
            status_counts.columns = ['Trạng thái', 'Số lượng']
            st.bar_chart(status_counts, x='Trạng thái', y='Số lượng')

    with tab3:
        st.dataframe(data_sheets.get("2_NHIEM_VU", pd.DataFrame()), use_container_width=True)
        
    with tab4:
        st.dataframe(data_sheets.get("4_TIEU_CHI", pd.DataFrame()), use_container_width=True)
        
    st.caption("Dữ liệu được làm mới sau mỗi 10 phút.")