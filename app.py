import streamlit as st
import pandas as pd

# =========================================================
# ⚙️ CẤU HÌNH TRANG (PHẢI ĐỂ ĐẦU TIÊN)
# =========================================================
st.set_page_config(
    page_title="Quản lý công việc EVNGENCO1",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 🔒 HỆ THỐNG ĐĂNG NHẬP (BẢO MẬT)
# =========================================================
def check_password():
    """Kiểm tra mật khẩu trước khi cho vào App"""
    # 1. Khởi tạo trạng thái đăng nhập
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    # 2. Hàm xử lý khi bấm nút Đăng nhập
    def password_entered():
        # Lấy mật khẩu từ file secrets.toml
        # Lưu ý: Bạn phải có dòng PASSWORD = "admin" trong secrets
        if st.session_state["password"] == st.secrets["general"]["PASSWORD"]:
            st.session_state.password_correct = True
            del st.session_state["password"]  # Xóa pass khỏi bộ nhớ ngay
        else:
            st.session_state.password_correct = False

    # 3. Nếu đã đăng nhập thành công -> Trả về True (Cho vào)
    if st.session_state.password_correct:
        return True

    # 4. Giao diện đăng nhập
    st.markdown("## 🔒 Yêu cầu đăng nhập")
    st.text_input(
        "Nhập mật khẩu quản trị:", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )
    
    # Hiển thị lỗi nếu nhập sai
    if "password_correct" in st.session_state and not st.session_state.password_correct:
        # Chỉ báo lỗi nếu người dùng đã nhập gì đó (để tránh báo lỗi khi vừa mở app)
        if "password" in st.session_state: 
             pass # Logic trên đã xóa key 'password' nếu đúng, nên nếu còn key này nghĩa là sai hoặc chưa nhập
             
    # Gợi ý nhỏ nếu chưa cấu hình
    try:
        if "PASSWORD" not in st.secrets["general"]:
            st.error("⚠️ Cảnh báo: Chưa cài đặt PASSWORD trong secrets.toml")
    except:
        pass

    return False

# 🛑 CHẶN CỬA: Nếu chưa nhập đúng mật khẩu thì DỪNG LẠI NGAY
if not check_password():
    st.stop()

# =========================================================
# 📥 IMPORT CÁC MODULE CHỨC NĂNG
# (Chỉ import sau khi đã đăng nhập thành công để an toàn)
# =========================================================
try:
    from new_task import render_new_task_tab
    from report import render_report_tab
    from data_manager import render_data_manager_tab
    
    # Các module khác (Nếu bạn chưa có file thì tạm thời comment lại để không lỗi)
    # from guide import render_guide_tab 
    # from chat_work import render_chat_work_tab
    # from chat_gemini import render_chat_gemini_tab
    # from ai_memory import render_memory_tab
    # from json_import import render_json_import_tab
    
except ImportError as e:
    st.error(f"⚠️ Lỗi thiếu file module: {e}")
    st.stop()

# =========================================================
# 🎨 GIAO DIỆN CHÍNH (SIDEBAR MENU)
# =========================================================

# 1. Logo (Nếu có file logo.png)
try:
    st.sidebar.image("logo.png", use_column_width=True)
except:
    st.sidebar.markdown("## ⚡ EVNGENCO1")

st.sidebar.markdown("---")

# 2. Menu Chức Năng
menu = st.sidebar.radio(
    "📌 CHỨC NĂNG",
    [
        "Hướng dẫn sử dụng",         # 0
        "Giao việc bằng Gemini",     # 1
        "Giao việc thủ công",        # 2
        "Báo cáo công việc",         # 3
        "Trao đổi công việc",        # 4
        "Hỏi – đáp Gemini",          # 5
        "Trí nhớ AI",                # 6
        "Quản lý dữ liệu gốc",       # 7
        "Nhập liệu từ JSON",         # 8
    ],
    index=2 # Mặc định mở tab Giao việc thủ công
)

# 3. Nút Làm mới dữ liệu (Quan trọng)
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Làm mới dữ liệu", type="primary"):
    st.cache_data.clear()
    st.rerun()

# 4. Footer
st.sidebar.markdown("---")
st.sidebar.caption("Phiên bản: Cloud 2.0")
st.sidebar.caption("Dev: Ban KHCN&DMST")

# =========================================================
# 🚀 ĐIỀU HƯỚNG NỘI DUNG (ROUTING)
# =========================================================

if menu == "Hướng dẫn sử dụng":
    st.header("📖 Hướng dẫn sử dụng")
    st.info("Chức năng đang cập nhật...")
    # render_guide_tab()

elif menu == "Giao việc bằng Gemini":
    st.header("🤖 Giao việc thông minh (Gemini)")
    st.info("Chức năng đang cập nhật...")
    # render_gemini_assign_tab()

elif menu == "Giao việc thủ công":
    # Gọi hàm từ file new_task.py
    render_new_task_tab()

elif menu == "Báo cáo công việc":
    # Gọi hàm từ file report.py
    render_report_tab()

elif menu == "Trao đổi công việc":
    st.header("💬 Trao đổi công việc")
    st.info("Chức năng đang cập nhật...")
    # render_chat_work_tab()

elif menu == "Hỏi – đáp Gemini":
    st.header("💡 Hỏi đáp với AI")
    st.info("Chức năng đang cập nhật...")
    # render_chat_gemini_tab()

elif menu == "Trí nhớ AI":
    st.header("🧠 Quản lý Trí nhớ AI")
    st.info("Chức năng đang cập nhật...")
    # render_memory_tab()

elif menu == "Quản lý dữ liệu gốc":
    # Gọi hàm từ file data_manager.py
    render_data_manager_tab()

elif menu == "Nhập liệu từ JSON":
    st.header("📥 Nhập liệu JSON")
    st.info("Chức năng đang cập nhật...")
    # render_json_import_tab()
