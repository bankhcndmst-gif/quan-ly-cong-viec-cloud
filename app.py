import streamlit as st
from config import REQUIRED_SHEETS

# --- IMPORT CÁC MODULE CON ---
from gsheet import load_all_sheets # Import hàm check kết nối để hiển thị trạng thái
from data_manager import render_data_manager_tab
from guide import render_guide_tab # <--- ĐÃ THÊM FILE HƯỚNG DẪN

# =========================================================
# 1. CẤU HÌNH GIAO DIỆN
# =========================================================
st.set_page_config(
    page_title="Hệ thống Quản lý EVNGENCO1",
    layout="wide",
    page_icon="🏢"
)

# =========================================================
# 2. MENU CHÍNH (SIDEBAR)
# =========================================================
st.markdown("<h3 style='text-align: center; color: #0052cc;'>CỔNG THÔNG TIN BAN KHCNĐMST</h3>", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/906/906343.png", width=100)
    st.title("Menu Chức năng")
    
    # Danh sách các chức năng
    menu = st.radio(
        "Chọn tác vụ:",
        [
            "🏠 Trang chủ",
            "📖 Hướng dẫn sử dụng", # <--- Đã thêm vào Menu
            "📂 Quản lý dữ liệu gốc",
            # "📝 Giao việc thủ công", 
            # "🤖 Giao việc bằng Gemini",
        ]
    )
    
    st.markdown("---")
    st.caption("Phiên bản: Modular 2.1")

# =========================================================
# 3. ĐIỀU HƯỚNG NỘI DUNG
# =========================================================

if menu == "🏠 Trang chủ":
    st.info("👋 Chào mừng quay trở lại!")
    st.write("Hệ thống quản lý công việc tập trung - Tích hợp Trí tuệ nhân tạo Gemini.")
    
    # Kiểm tra nhanh kết nối
    if st.button("Kiểm tra kết nối dữ liệu"):
        try:
            data = load_all_sheets()
            st.success(f"✅ Kết nối thành công! Đã tải {len(data)} bảng dữ liệu.")
        except Exception as e:
            st.error(f"❌ Kết nối thất bại: {e}")

elif menu == "📖 Hướng dẫn sử dụng":
    # Gọi hàm từ file guide.py
    render_guide_tab()

elif menu == "📂 Quản lý dữ liệu gốc":
    # Gọi hàm từ file data_manager.py
    render_data_manager_tab()

# Các menu chờ phát triển tiếp:
# elif menu == "📝 Giao việc thủ công":
#     render_new_task_tab()
