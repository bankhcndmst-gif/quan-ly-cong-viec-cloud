import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# =========================================================
# 1. CẤU HÌNH GIAO DIỆN
# =========================================================
st.set_page_config(
    page_title="QLCV Ban KHCNĐMST",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🏢"
)

# =========================================================
# 2. HÀM KẾT NỐI GOOGLE SHEETS (Dùng chung cho các Tab)
# =========================================================
def get_data(sheet_name):
    """Kết nối và lấy dữ liệu từ Google Sheet (Realtime)"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # ttl=0 để luôn lấy dữ liệu mới nhất
        return conn.read(worksheet=sheet_name, ttl=0)
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối Sheet '{sheet_name}': {e}")
        return pd.DataFrame()

# =========================================================
# 3. ĐỊNH NGHĨA CÁC TAB CHỨC NĂNG (Gộp vào đây để không lỗi)
# =========================================================

def render_home_tab():
    st.info("👋 Chào mừng đến với Hệ thống Quản lý Công việc Ban KHCNĐMST.")
    st.write("Vui lòng chọn chức năng ở menu bên trái.")

def render_data_manager_tab():
    st.header("📂 Quản lý dữ liệu gốc")
    tab1, tab2, tab3 = st.tabs(["Nhân sự (1_NHAN_SU)", "Công việc (7_CONG_VIEC)", "Trao đổi (10_TRAO_DOI)"])
    
    with tab1:
        st.dataframe(get_data("1_NHAN_SU"), use_container_width=True)
    with tab2:
        st.dataframe(get_data("7_CONG_VIEC"), use_container_width=True)
    with tab3:
        st.dataframe(get_data("10_TRAO_DOI"), use_container_width=True)

def render_report_tab():
    st.header("📊 Báo cáo công việc (Sheet 7_CONG_VIEC)")
    df = get_data("7_CONG_VIEC")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Chưa có dữ liệu.")

def render_chat_tab():
    st.header("💬 Trao đổi công việc (Sheet 10_TRAO_DOI)")
    
    # Load dữ liệu
    if "chat_data" not in st.session_state:
        df_chat = get_data("10_TRAO_DOI")
        if not df_chat.empty and len(df_chat.columns) >= 3:
            df_temp = df_chat.copy()
            # Đổi tên cột tạm thời để hiển thị
            df_temp.columns.values[0] = "Time"
            df_temp.columns.values[1] = "User"
            df_temp.columns.values[2] = "Message"
            st.session_state.chat_data = df_temp
        else:
            st.session_state.chat_data = pd.DataFrame(columns=["Time", "User", "Message"])

    # Hiển thị Chat
    chat_container = st.container(height=400)
    with chat_container:
        for i, row in st.session_state.chat_data.iterrows():
            st.chat_message("user").write(f"**{row['User']}**: {row['Message']}")

    # Nhập tin nhắn (Tạm thời chỉ hiện, chưa ghi ngược vào Sheet vì cần quyền Write)
    if prompt := st.chat_input("Nhập nội dung..."):
        # Lưu tạm vào phiên làm việc
        new_msg = {"Time": datetime.now().strftime("%H:%M"), "User": "Bạn", "Message": prompt}
        st.session_state.chat_data = pd.concat([st.session_state.chat_data, pd.DataFrame([new_msg])], ignore_index=True)
        st.rerun()

# --- Các hàm Placeholder (Chờ bạn phát triển thêm) ---
def render_gemini_chat_tab():
    st.info("🤖 Tính năng Hỏi-đáp Gemini đang phát triển...")

def render_new_task_tab():
    st.info("📝 Tính năng Giao việc thủ công đang phát triển...")

def render_gemini_task_tab():
    st.info("✨ Tính năng Giao việc bằng AI đang phát triển...")

def render_guide_tab():
    st.markdown("### 📖 Hướng dẫn sử dụng hệ thống")
    st.write("Đang cập nhật...")

# =========================================================
# 4. GIAO DIỆN CHÍNH (SIDEBAR & MAIN)
# =========================================================

# --- HEADER ---
st.markdown(
    """
    <h3 style='text-align: center; color: #1E88E5;'>
        HỆ THỐNG QUẢN LÝ CÔNG VIỆC BAN KHCNĐMST
    </h3>
    <hr>
    """, 
    unsafe_allow_html=True
)

# --- MENU BÊN TRÁI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2921/2921222.png", width=80)
    st.title("Menu Chức năng")
    
    menu = st.radio(
        "Chọn tác vụ:",
        [
            "Trang chủ",
            "Giao việc bằng Gemini",
            "Giao việc thủ công",
            "Báo cáo công việc", # Xem dữ liệu 7_CONG_VIEC
            "Trao đổi công việc", # Xem dữ liệu 10_TRAO_DOI
            "Hỏi – đáp Gemini",
            "Quản lý dữ liệu gốc", # Xem tất cả
            "Hướng dẫn sử dụng"
        ]
    )
    
    st.markdown("---")
    st.caption("Phiên bản: Cloud 1.0 (No-Login)")

# --- ĐIỀU HƯỚNG ---
if menu == "Trang chủ":
    render_home_tab()

elif menu == "Quản lý dữ liệu gốc":
    render_data_manager_tab()

elif menu == "Giao việc thủ công":
    render_new_task_tab()

elif menu == "Báo cáo công việc":
    render_report_tab()

elif menu == "Trao đổi công việc":
    render_chat_tab()

elif menu == "Hỏi – đáp Gemini":
    render_gemini_chat_tab()

elif menu == "Giao việc bằng Gemini":
    render_gemini_task_tab()

elif menu == "Hướng dẫn sử dụng":
    render_guide_tab()
