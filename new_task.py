import streamlit as st
import pandas as pd
from datetime import datetime
from gsheet import load_all_sheets, save_raw_sheet
from utils import get_display_list_multi, format_date_vn

def generate_task_id(df):
    """Tự động sinh ID mới: CV001 -> CV002"""
    if df.empty or "ID_CONG_VIEC" not in df.columns:
        return "CV001"
    
    # Lấy danh sách ID cũ
    ids = df["ID_CONG_VIEC"].dropna().astype(str).tolist()
    max_num = 0
    for i in ids:
        # Lọc lấy số từ chuỗi (CV001 -> 1)
        clean_id = ''.join(filter(str.isdigit, i))
        if clean_id:
            try:
                n = int(clean_id)
                if n > max_num: max_num = n
            except: pass
            
    return f"CV{max_num + 1:03d}"

def render_new_task_tab():
    st.header("📝 Giao việc thủ công (Chi tiết)")

    # 1. Tải dữ liệu nền
    try:
        all_sheets = load_all_sheets()
        df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame())
        df_ns = all_sheets.get("1_NHAN_SU", pd.DataFrame())
        df_da = all_sheets.get("4_DU_AN", pd.DataFrame())
        df_gt = all_sheets.get("5_GOI_THAU", pd.DataFrame())
        df_hd = all_sheets.get("6_HOP_DONG", pd.DataFrame())
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return

    # Chuẩn bị danh sách chọn
    list_ns, map_ns = get_display_list_multi(df_ns, "ID_NHAN_SU", ["HO_TEN"], "Chọn nhân sự...")
    list_da, map_da = get_display_list_multi(df_da, "ID_DU_AN", ["TEN_DU_AN"], "Không thuộc dự án")
    list_hd, map_hd = get_display_list_multi(df_hd, "ID_HOP_DONG", ["TEN_HD", "SO_HD"], "Không thuộc hợp đồng")
    list_gt, map_gt = get_display_list_multi(df_gt, "ID_GOI_THAU", ["TEN_GOI_THAU"], "Không thuộc gói thầu")

    # 2. Tạo Form nhập liệu
    with st.form("form_giao_viec_full"):
        
        # --- NHÓM 1: THÔNG TIN CƠ BẢN ---
        st.subheader("1. Thông tin chung")
        col1, col2 = st.columns(2)
        with col1:
            ten_viec = st.text_input("Tên công việc (*)", placeholder="Nhập tên công việc ngắn gọn")
            loai_viec = st.selectbox("Loại việc", ["Thường xuyên", "Đột xuất", "Dự án", "Khác"])
        with col2:
            nguon_giao = st.selectbox("Nguồn giao việc", ["Lãnh đạo Ban", "Phòng ban đề xuất", "Văn bản đến", "Khác"])
            noi_dung = st.text_area("Nội dung chi tiết", height=100)

        # --- NHÓM 2: NHÂN SỰ & THỜI GIAN ---
        st.subheader("2. Nhân sự & Thời gian")
        col3, col4 = st.columns(2)
        with col3:
            nguoi_giao_display = st.selectbox("Người giao", list_ns, index=0)
            nguoi_nhan_display = st.selectbox("Người chủ trì (Nhận)", list_ns, index=0)
            
            # Chọn nhiều người phối hợp (Multiselect)
            # Lọc bỏ dòng "Chọn nhân sự..." để list đẹp hơn
            list_ns_real = [x for x in list_ns if "Chọn" not in x]
            nguoi_phoi_hop_display = st.multiselect("Người phối hợp", list_ns_real)

        with col4:
            ngay_giao = st.date_input("Ngày giao", value=datetime.now())
            han_chot = st.date_input("Hạn chót", value=None)
            trang_thai = st.selectbox("Trạng thái tổng", ["Chưa thực hiện", "Đang thực hiện", "Hoàn thành", "Tạm dừng"])

        # --- NHÓM 3: LIÊN KẾT (Dự án/Hợp đồng) ---
        st.subheader("3. Liên kết hồ sơ")
        col5, col6, col7 = st.columns(3)
        with col5:
            da_display = st.selectbox("Dự án", list_da)
        with col6:
            hd_display = st.selectbox("Hợp đồng", list_hd)
        with col7:
            gt_display = st.selectbox("Gói thầu", list_gt)
            
        # Các ID phụ khác (nhập text tạm thời)
        with st.expander("➕ Thông tin bổ sung (Văn bản, Đơn vị, Vướng mắc...)"):
            c_a, c_b = st.columns(2)
            id_van_ban = c_a.text_input("ID Văn bản liên quan (IDVB_VAN_BAN)")
            id_don_vi = c_b.text_input("ID Đơn vị phối hợp (IDDV_CV)")
            
            vuong_mac = st.text_area("Vướng mắc (nếu có)")
            de_xuat = st.text_area("Đề xuất (nếu có)")
            ghi_chu = st.text_area("Ghi chú khác")
            email_bc = st.text_input("Email báo cáo (EMAIL_BC_CV)")

        # --- Nút Gửi ---
        submitted = st.form_submit_button("✅ Lưu công việc", type="primary")

        if submitted:
            # 1. Validate
            if not ten_viec.strip():
                st.error("⚠️ Tên công việc không được để trống!")
                return
            
            # 2. Map ID từ tên hiển thị
            id_nguoi_giao = map_ns.get(nguoi_giao_display, "")
            id_nguoi_nhan = map_ns.get(nguoi_nhan_display, "")
            
            # Xử lý người phối hợp (nối chuỗi các ID lại)
            ids_phoi_hop = []
            for name in nguoi_phoi_hop_display:
                if name in map_ns: ids_phoi_hop.append(map_ns[name])
            str_phoi_hop = ", ".join(ids_phoi_hop)

            id_da = map_da.get(da_display, "")
            id_hd = map_hd.get(hd_display, "")
            id_gt = map_gt.get(gt_display, "")

            # 3. Tạo row dữ liệu (ĐÚNG THỨ TỰ CỘT BẠN GỬI)
            new_id = generate_task_id(df_cv)
            
            # Chuẩn hóa ngày
            s_ngay_giao = ngay_giao.strftime("%d/%m/%Y") if ngay_giao else ""
            s_han_chot = han_chot.strftime("%d/%m/%Y") if han_chot else ""

            # Danh sách cột chuẩn (22 cột)
            cols_chuan = [
                "ID_CONG_VIEC", "TEN_VIEC", "NOI_DUNG", "LOAI_VIEC", "NGUON_GIAO_VIEC",
                "NGUOI_GIAO", "NGUOI_NHAN", "NGAY_GIAO", "HAN_CHOT", "NGUOI_PHOI_HOP",
                "TRANG_THAI_TONG", "TRANG_THAI_CHI_TIET", "NGAY_THUC_TE_XONG",
                "IDVB_VAN_BAN", "IDHD_CV", "IDDA_CV", "IDGT_CV",
                "VUONG_MAC", "DE_XUAT", "IDDV_CV", "GHI_CHU_CV", "EMAIL_BC_CV"
            ]
            
            # Đảm bảo DataFrame đủ cột
            for c in cols_chuan:
                if c not in df_cv.columns: df_cv[c] = ""

            new_row = {
                "ID_CONG_VIEC": new_id,
                "TEN_VIEC": ten_viec,
                "NOI_DUNG": noi_dung,
                "LOAI_VIEC": loai_viec,
                "NGUON_GIAO_VIEC": nguon_giao,
                "NGUOI_GIAO": id_nguoi_giao,
                "NGUOI_NHAN": id_nguoi_nhan,
                "NGAY_GIAO": s_ngay_giao,
                "HAN_CHOT": s_han_chot,
                "NGUOI_PHOI_HOP": str_phoi_hop,
                "TRANG_THAI_TONG": trang_thai,
                "TRANG_THAI_CHI_TIET": "", # Mới tạo thì chưa có chi tiết
                "NGAY_THUC_TE_XONG": "",   # Mới tạo thì chưa xong
                "IDVB_VAN_BAN": id_van_ban,
                "IDHD_CV": id_hd,
                "IDDA_CV": id_da,
                "IDGT_CV": id_gt,
                "VUONG_MAC": vuong_mac,
                "DE_XUAT": de_xuat,
                "IDDV_CV": id_don_vi,
                "GHI_CHU_CV": ghi_chu,
                "EMAIL_BC_CV": email_bc
            }
            
            # 4. Lưu
            df_new = pd.concat([df_cv, pd.DataFrame([new_row])], ignore_index=True)
            save_raw_sheet("7_CONG_VIEC", df_new)
            
            st.success(f"🎉 Đã lưu công việc mới: **{new_id} - {ten_viec}**")
            st.cache_data.clear()
