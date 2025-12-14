# --- Hàm Tải Dữ liệu (Dùng cache để tối ưu) ---
@st.cache_data(ttl=600)  # Cache trong 10 phút
def load_data_from_gsheets():
    try:
        # Lấy thông tin kết nối từ Streamlit Secrets (.streamlit/secrets.toml)

        # 1. Kết nối với Google API bằng Service Account
        # Cấu trúc TỐI THIỂU để gspread hoạt động.
        credentials = {
            "type": "service_account",
            "private_key": st.secrets["gdrive"]["private_key"].replace('\\n', '\n'),
            "client_email": st.secrets["gdrive"]["client_email"],
        }

        # 2. Mở Google Sheet theo ID
        gc = gspread.service_account_from_dict(credentials)
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
