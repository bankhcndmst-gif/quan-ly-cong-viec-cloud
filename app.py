import streamlit as st
import gspread
import pandas as pd

# --- Hàm Tải Dữ liệu từ Google Sheets (An toàn cho Streamlit Cloud) ---
@st.cache_data(ttl=600)  # Cache 10 phút
def load_data_from_gsheets():
    try:
        # 1. Tạo credentials TỐI THIỂU – CHUẨN GSPREAD (Có token_uri)
        credentials = {
            "type": "service_account",
            "private_key": st.secrets["gdrive"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["gdrive"]["client_email"],
            "token_uri": "https://oauth2.googleapis.com/token", 
        }

        # 2. Kết nối Google Sheet
        gc = gspread.service_account_from_dict(credentials)
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])

        # 3. Load dữ liệu
        sheets = {}
        for name in [
            "1_NHAN_SU",
            "7_CONG_VIEC",
            "2_NHIEM_VU",
            "4_TIEU_CHI"
        ]:
            try:
                ws = sh.worksheet(name)
                sheets[name] = pd.DataFrame(ws.get_all_records())
            except Exception as e:
                st.warning(f"⚠️ Sheet {name}: {e}")
                sheets[name] = pd.DataFrame()

        return sheets

    except Exception as e:
        st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
        return None

# --- Cấu hình và Chạy Ứng dụng ---
st.set_page_config(layout="wide", page_title="Hệ thống Quản lý Công việc", page_icon="📈")
st.title("📈 Hệ thống Quản lý Công việc (Test Cloud)")

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
