import streamlit as st

def render_guide_tab():
    st.markdown("""
    # 📘 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG
    
    Chào mừng bạn đến với **Hệ thống Quản lý Công việc Ban KHCNĐMST + Trợ lý Gemini**.
    Dưới đây là hướng dẫn chi tiết từng chức năng.

    ---

    ### 1. 🤖 Giao việc bằng Gemini 
    Đây là tính năng giúp bạn giao việc nhanh bằng ngôn ngữ tự nhiên.
    
    * **Bước 1:** Chọn menu **"Giao việc bằng Gemini"**.
    * **Bước 2:** Nhập câu lệnh vào ô trống.
        * *Ví dụ 1:* "Giao cho anh Thắng làm báo cáo hàng tuần, hạn chót thứ 6 hàng tuần."
        * *Ví dụ 2:* "Hoàn thiện hồ sơ 3 dự án chuyển đổi số."
    * **Bước 3:** Bấm **"🚀 Phân tích bằng Gemini"**.
    * **Bước 4:** Kiểm tra lại bảng nháp (AI có thể hiểu sai ngày tháng, bạn có thể sửa lại trực tiếp trên bảng).
    * **Bước 5:** Bấm **"💾 Lưu vào hệ thống"**.

    ---

    ### 2. 📝 Giao việc Thủ công
    Dùng khi cần nhập liệu chính xác, chi tiết từng trường thông tin.
    
    * Điền đầy đủ: Tên việc, Người giao, Người nhận, Ngày, Hạn chót...
    * **Quan trọng:** Hãy chọn các liên kết (Dự án, Hợp đồng, Gói thầu) để sau này báo cáo lọc được dữ liệu.

    ---

    ### 3. 📊 Báo cáo công việc
    Nơi theo dõi toàn bộ công việc của Ban.
    
    * **Màu sắc:** Hệ thống tự động tô 🔴 **Đỏ** cho việc trễ hạn, 🟢 **Xanh** cho việc hoàn thành.
    * **Bộ lọc đa năng:** Bạn có thể lọc theo:
        * Nhân sự (Ai làm gì?)
        * Dự án / Gói thầu / Hợp đồng (Tiến độ của dự án đó thế nào?)
        * Trạng thái (Việc nào đang cháy tiến độ?)

    ---

    ### 4. 💬 Trao đổi công việc
    Thay vì chat Zalo trôi tin, hãy chat ngay trong công việc đó.
    
    * Chọn công việc cụ thể -> Xem lịch sử trao đổi.
    * Gửi nội dung mới hoặc đính kèm link tài liệu.

    ---

    ### 5. 🧠 Trí nhớ AI (Thư ký cuộc họp)
    Dùng để lưu lại biên bản họp, ghi chú quan trọng không phải là đầu việc cụ thể.
    
    * Nhập nội dung: *"Họp giao ban ngày 15/12: Sếp yêu cầu đẩy nhanh tiến độ..."*
    * Sau này có thể vào mục **"Hỏi - đáp Gemini"** để hỏi lại: *"Cuộc họp ngày 15/12 có nội dung gì?"*

    ---
    
    ### ⚠️ Một số lưu ý quan trọng
    1.  **Dữ liệu:** Toàn bộ dữ liệu nằm trong file Google Sheet trên Gmail của bạn. Bạn có thể vào đó sửa xóa thoải mái.
    2.  **App bị ngủ:** Nếu lâu không dùng, App sẽ tạm dừng. Bấm **"Yes, wake it up"** để đánh thức.
    3.  **Cập nhật:** Nếu sửa file Excel mà App chưa hiện, bấm nút **Rerun** (hoặc F5) để tải lại.
    """)
