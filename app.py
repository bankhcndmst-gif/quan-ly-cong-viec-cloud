import streamlit as st
import time
import pandas as pd

# Import các tab
from gsheet import load_all_sheets
from data_manager import render_data_manager_tab
from new_task import render_new_task_tab # (Nếu chưa có file này thì comment dòng này lại)
from report import render_report_tab # (Nếu chưa có file này thì comment dòng này lại)
from chat import render_chat_tab
from gemini_chat import render_gemini_chat_tab
from gemini_task_tab import render_gemini_task_tab
from gemini_json_import import render_json_import_tab
from memory_tab import render_memory_tab
from guide import render_guide_tab 

# =========================================================
# ✅ CẤU HÌNH GIAO DIỆN
# =========================================================
st.set_page_config(
    page_title="QLCV Ban KHCNĐMST",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🔐"
)

# =========================================================
# ✅ LOGIC ĐĂNG NHẬP
# =========================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_role" not in st.session_state: st.session_state.user_role = ""
if "current_user" not in st.session_state: st.session_state.current_user = ""

def login_logic(username, password):
    # Tải dữ liệu từ Sheet
    all_sheets = load_all_sheets()
    df = all_sheets.get("1_NHAN_SU", pd.DataFrame())
    
    if df.empty:
        st.error("⚠️ Không kết nối được dữ liệu nhân sự (1_NHAN_SU)!")
        return

    # Kiểm tra cột GMAIL có tồn tại không (Code gsheet.py đã chuẩn hóa thành chữ hoa)
    if 'GMAIL' not in df.columns:
        st.error(f"❌ Lỗi: Không tìm thấy cột 'GMAIL'. Các cột máy đọc được: {df.columns.tolist()}")
        st.info("💡 Gợi ý: Hãy kiểm tra file Excel, đảm bảo dòng 1 không có ô trống giữa các cột.")
        return

    # Tìm cột mật khẩu (PASSWORD hoặc MAT_KHAU)
    pass_col = 'PASSWORD'
    if 'PASSWORD' not in df.columns:
        if 'MAT_KHAU' in df.columns:
            pass_col = 'MAT_KHAU'
        else:
            st.error("❌ Thiếu cột mật khẩu (PASSWORD) trong file Excel.")
            return

    # Xử lý đăng nhập
    u_input = str(username).strip().lower()
    p_input = str(password).strip()
    
    # Tạo cột phụ để so sánh email
    df['GMAIL_CLEAN'] = df['GMAIL'].astype(str).str.strip().str.lower()
    
    user_row = df[df['GMAIL_CLEAN'] == u_input]
    
    if not user_row.empty:
        stored_pass = str(user_row.iloc[0][pass_col]).strip()
        
        if stored_pass == p_input:
            st.session_state.logged_in = True
            
            # Lấy tên và vai trò
            if 'HO_TEN' in df.columns:
                st.session_state.current_user = user_row.iloc[0]['HO_TEN']
            else:
                st.session_state.current_user = "User"
                
            role_raw = ""
            if 'VAI_TRO' in df.columns:
                role_raw = str(user_row.iloc[0]['VAI_TRO']).strip().upper()
                
            if role_raw in ["ADMIN", "QUẢN TRỊ", "SẾP"]:
                st.session_state.user_role = "ADMIN"
            else:
                st.session_state.user_role = "NHAN_VIEN"
                
            st.success("✅ Đăng nhập thành công!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("❌ Sai mật khẩu!")
    else:
        st.error(f"❌ Email không tồn tại: {u_input}")

# =========================================================
# ✅ GIAO DIỆN CHÍNH (MAIN APP)
# =========================================================

if not st.session_state.logged_in:
    # --- MÀN HÌNH ĐĂNG NHẬP ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔐 Đăng nhập Hệ thống</h2>", unsafe_allow_html=True)
        st.info("Tài khoản demo: ban.khcndmst@gmail.com / Genco1$123")
        
        with st.form("login_form"):
            u = st.text_input("Gmail")
            p = st.text_input("Mật khẩu", type="password")
            btn = st.form_submit_button("Vào hệ thống", use_container_width=True)
            
            if btn:
                login_logic(u, p)

else:
    # --- GIAO DIỆN SAU KHI ĐĂNG NHẬP ---
    
    # Header
    st.markdown(
        """
        <h3 style='text-align: center; color: #1E88E5;'>
            QUẢN LÝ CÔNG VIỆC BAN KHCNĐMST + AI GEMINI
        </h3>
        """, 
        unsafe_allow_html=True
    )

    # Menu Sidebar
    with st.sidebar:
        st.success(f"👤 **{st.session_state.current_user}**")
        st.caption(f"Vai trò: {st.session_state.user_role}")
        
        if st.button("🚪 Đăng xuất"):
            st.session_state.logged_in = False
            st.rerun()
            
        st.markdown("---")
        
        menu = st.radio(
            "📌 CHỨC NĂNG",
            [
                "Hướng dẫn sử dụng",
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
        st.sidebar.caption("v1.2 Cloud")

    # Điều hướng
    if menu == "Hướng dẫn sử dụng":
        render_guide_tab()

    elif menu == "Quản lý dữ liệu gốc":
        # Chỉ Admin mới được sửa
        if st.session_state.user_role == "ADMIN":
            render_data_manager_tab()
        else:
            st.warning("⛔ Bạn không có quyền truy cập menu này.")

    elif menu == "Giao việc thủ công":
        # render_new_task_tab() # Mở comment khi có file
        st.info("Tính năng đang cập nhật file new_task.py")

    elif menu == "Báo cáo công việc":
        # render_report_tab() # Mở comment khi có file
        st.info("Tính năng đang cập nhật file report.py")

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
