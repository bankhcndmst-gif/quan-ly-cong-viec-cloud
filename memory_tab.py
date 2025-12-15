import streamlit as st
import pandas as pd
from gsheet import load_all_sheets, save_raw_sheet
# Module này chúng ta sẽ tạo ở Bước 2
from gemini_memory_parser import parse_memory_from_chat 

def render_memory_tab():
    st.header("🧠 Trí nhớ AI (Lưu trữ Tri thức)")

    # 1. Lấy API Key từ Secrets (Ưu tiên) hoặc Config
    api_key = st.secrets.get("general", {}).get("GEMINI_API_KEY", None)

    all_sheets = load_all_sheets()
    
    # Fallback: Tìm trong Sheet cấu hình nếu chưa có trong Secrets
    if not api_key:
        try:
            df_config = all_sheets.get("8_CAU_HINH", pd.DataFrame())
            if not df_config.empty:
                # Logic tìm key linh hoạt
                mask = df_config.iloc[:, 0].astype(str).str.contains("GEMINI_API", case=False, na=False)
                if mask.any():
                    api_key = str(df_config.loc[mask].iloc[0, 1]).strip()
        except: pass

    if not api_key:
        st.error("❌ Chưa tìm thấy GEMINI_API_KEY trong secrets.toml hoặc Sheet Cấu hình.")
        st.info("Vui lòng cập nhật file secrets.toml.")
        return

    # 2. Giao diện nhập liệu
    col1, col2 = st.columns([2, 1])
    with col1:
        user_message = st.text_area("Nhập nội dung cần ghi nhớ (Biên bản họp, ghi chú, nhắc nhở...):", height=150)
    with col2:
        st.info("💡 **Ví dụ:**\n'Họp giao ban ngày 15/12: Sếp yêu cầu đẩy nhanh tiến độ dự án X, hạn chót thứ 6.'")

    if st.button("🚀 Phân tích & Trích xuất", type="primary"):
        if user_message.strip():
            with st.spinner("Gemini đang đọc hiểu..."):
                # Gọi hàm xử lý AI
                df_parsed = parse_memory_from_chat(api_key, user_message)
                
                if not df_parsed.empty:
                    st.session_state["memory_parsed"] = df_parsed
                    st.success("Đã trích xuất thông tin thành công!")
                else:
                    st.error("AI không trích xuất được thông tin nào. Vui lòng thử lại.")
        else:
            st.warning("Vui lòng nhập nội dung.")

    # 3. Hiển thị kết quả phân tích & Lưu
    if "memory_parsed" in st.session_state:
        st.subheader("📝 Kết quả trích xuất")
        df_edit = st.data_editor(st.session_state["memory_parsed"], num_rows="dynamic", use_container_width=True)
        
        if st.button("💾 Lưu vào Trí nhớ AI", type="primary"):
            try:
                # Lấy dữ liệu cũ
                df_mem = all_sheets.get("11_TRI_NHO_AI", pd.DataFrame())
                
                # Nối dữ liệu mới
                df_new = pd.concat([df_mem, df_edit], ignore_index=True)
                
                # Lưu lên Google Sheet
                save_raw_sheet("11_TRI_NHO_AI", df_new)
                
                st.success("✅ Đã lưu vào bộ nhớ dài hạn!")
                del st.session_state["memory_parsed"] # Xóa state để reset
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi khi lưu: {e}")

    # 4. Hiển thị Dữ liệu đã lưu (Lịch sử)
    st.divider()
    st.subheader("🗄️ Dữ liệu đã ghi nhớ")
    try:
        df_mem = load_all_sheets().get("11_TRI_NHO_AI", pd.DataFrame())
        if not df_mem.empty and "LOAI" in df_mem.columns:
            filters = ["Tất cả"] + list(df_mem["LOAI"].unique())
            loai_chon = st.selectbox("Lọc theo loại:", filters)
            
            if loai_chon != "Tất cả":
                df_mem = df_mem[df_mem["LOAI"] == loai_chon]
            
            st.dataframe(df_mem, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu trong Sheet '11_TRI_NHO_AI'")
    except: pass
