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


# =========================================================
# ✅ CẤU HÌNH GIAO DIỆN
# =========================================================
st.set_page_config(
    page_title="Hệ thống QLCV + Gemini",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚀 HỆ THỐNG QUẢN LÝ CÔNG VIỆC + TRỢ LÝ GEMINI")


# =========================================================
# ✅ MENU CHÍNH
# =========================================================
menu = st.sidebar.radio(
    "📌 Chọn chức năng",
    [
        "Quản lý dữ liệu gốc",
        "Giao việc thủ công",
        "Báo cáo công việc",
        "Trao đổi công việc",
        "Hỏi – đáp Gemini",
        "Giao việc bằng Gemini",
        "Nhập liệu từ JSON",
        "Trí nhớ AI"
    ]
)


# =========================================================
# ✅ ĐIỀU HƯỚNG TAB
# =========================================================
if menu == "Quản lý dữ liệu gốc":
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
