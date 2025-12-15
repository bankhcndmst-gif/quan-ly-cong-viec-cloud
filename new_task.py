import streamlit as st

# Import các tab
from data_manager import render_data_manager_tab
from new_task import render_new_task_tab
from report import render_report_tab
from chat import render_chat_tab
from gemini_chat import render_gemini_chat_tab
from gemini_task_tab import render_gemini_task_tab
from gemini_json_import import render_json_import_tab
from memory_tab import render_memory_tab
from guide import render_guide_tab # <--- MỚI THÊM

# =========================================================
# ✅ CẤU HÌNH GIAO DIỆN
# =========================================================
st.set_page_config(
    page_title="QLCV Ban KHCNĐMST",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# ✅ HEADER (CHỮ NHỎ ĐI 20%)
# =========================================================
# Sử dụng HTML để chỉnh cỡ chữ chính xác
st.markdown(
    """
    <h3 style='text-align: center; color: #1E88E5;'>
        HỆ THỐNG QUẢN LÝ CÔNG VIỆC BAN KHCNĐMST + TRỢ LÝ GEMINI
    </h3>
    """, 
    unsafe_allow_html=True
)

# =========================================================
# ✅ MENU CHÍNH
# =========================================================
menu = st.sidebar.radio(
    "📌 CHỨC NĂNG",
    [
        "Hướng dẫn sử dụng", # <--- Đưa lên đầu hoặc để cuối tùy bạn
        "Giao việc bằng Gemini",
        "Giao việc thủ công",
        "Báo cáo công việc",
        "Trao đổi công việc",
        "Hỏi – đáp Gemini",
        "Trí nhớ AI",
        "Quản lý dữ liệu gốc",
        "Nhập liệu từ JSON",
    ]
)

# =========================================================
# ✅ ĐIỀU HƯỚNG TAB
# =========================================================
if menu == "Hướng dẫn sử dụng":
    render_guide_tab()

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

elif menu == "Nhập liệu từ JSON":
    render_json_import_tab()

elif menu == "Trí nhớ AI":
    render_memory_tab()

# Thêm Footer nhỏ
st.sidebar.markdown("---")
st.sidebar.caption("Phiên bản: Cloud 1.2 | Dev: ThangNT")
