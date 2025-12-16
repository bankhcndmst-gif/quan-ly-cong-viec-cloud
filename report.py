def render_report_tab():
    st.header("📊 Báo cáo công việc")

    # 1. Tải dữ liệu
    try:
        all_sheets = load_all_sheets()
        df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame()).copy()
        df_ns = all_sheets.get("1_NHAN_SU", pd.DataFrame()).copy()
        df_da = all_sheets.get("4_DU_AN", pd.DataFrame()).copy()
        df_gt = all_sheets.get("5_GOI_THAU", pd.DataFrame()).copy()
        df_hd = all_sheets.get("6_HOP_DONG", pd.DataFrame()).copy()
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return

    if df_cv.empty:
        st.warning("Chưa có dữ liệu công việc trong sheet 7_CONG_VIEC.")
        return

    # 2. Tính trạng thái
    df_cv["TRANG_THAI_TONG"] = df_cv.apply(compute_status, axis=1)

    # =========================================================
    # 🔍 BỘ LỌC
    # =========================================================
    with st.expander("🔍 Bộ lọc nâng cao", expanded=True):

        colA, colB = st.columns(2)
        date_from = colA.date_input("Từ ngày (NGAY_GIAO)", None)
        date_to = colB.date_input("Đến ngày (NGAY_GIAO)", None)

        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)

        # Map dữ liệu
        da_map = dict(zip(df_da["ID_DU_AN"], df_da["TEN_DU_AN"])) if "ID_DU_AN" in df_da else {}
        list_da = ["Tất cả"] + list(da_map.values())

        gt_map = dict(zip(df_gt["ID_GOI_THAU"], df_gt["TEN_GOI_THAU"])) if "ID_GOI_THAU" in df_gt else {}
        list_gt = ["Tất cả"] + list(gt_map.values())

        hd_map = dict(zip(df_hd["ID_HOP_DONG"], df_hd["TEN_HD"])) if "ID_HOP_DONG" in df_hd else {}
        list_hd = ["Tất cả"] + list(hd_map.values())

        # Bộ lọc
        search_ten = col1.text_input("Tên công việc (Từ khóa)", "")
        filter_da = col2.selectbox("Dự án", list_da)
        filter_gt = col3.selectbox("Gói thầu", list_gt)
        filter_hd = col4.selectbox("Hợp đồng", list_hd)

        list_loai = ["Tất cả"] + list(df_cv["LOAI_VIEC"].dropna().unique()) if "LOAI_VIEC" in df_cv else ["Tất cả"]
        filter_loai = col5.selectbox("Loại việc", list_loai)

        # 🔥 Sửa bộ lọc trạng thái
        list_tt = ["Tất cả"] + sorted(df_cv["TRANG_THAI_TONG"].dropna().unique())
        filter_tt = col6.selectbox("Trạng thái", list_tt)

    # =========================================================
    # ⚙️ XỬ LÝ LỌC
    # =========================================================
    df_filtered = df_cv.copy()

    # Lọc theo ngày giao
    if date_from:
        df_filtered = df_filtered[df_filtered["NGAY_GIAO"] >= pd.to_datetime(date_from)]

    if date_to:
        df_filtered = df_filtered[df_filtered["NGAY_GIAO"] <= pd.to_datetime(date_to)]

    # Lọc tên
    if search_ten:
        df_filtered = df_filtered[df_filtered["TEN_VIEC"].astype(str).str.contains(search_ten, case=False, na=False)]

    # Lọc dự án/gói thầu/hợp đồng
    def find_id(map_dict, value):
        return [k for k, v in map_dict.items() if v == value]

    if filter_da != "Tất cả":
        ids = find_id(da_map, filter_da)
        if ids:
            df_filtered = df_filtered[df_filtered["IDDA_CV"] == ids[0]]

    if filter_gt != "Tất cả":
        ids = find_id(gt_map, filter_gt)
        if ids:
            df_filtered = df_filtered[df_filtered["IDGT_CV"] == ids[0]]

    if filter_hd != "Tất cả":
        ids = find_id(hd_map, filter_hd)
        if ids:
            df_filtered = df_filtered[df_filtered["IDHD_CV"] == ids[0]]

    # Lọc loại
    if filter_loai != "Tất cả":
        df_filtered = df_filtered[df_filtered["LOAI_VIEC"] == filter_loai]

    # Lọc trạng thái
    if filter_tt != "Tất cả":
        df_filtered = df_filtered[df_filtered["TRANG_THAI_TONG"] == filter_tt]

    # =========================================================
    # 📋 HIỂN THỊ KẾT QUẢ
    # =========================================================
    st.markdown(f"**Tìm thấy: {len(df_filtered)} công việc**")

    if df_filtered.empty:
        st.info("Không có dữ liệu phù hợp.")
        return

    df_show = df_filtered.copy()

    # Map tên nhân sự
    if "NGUOI_NHAN" in df_show:
        df_show["NGUOI_NHAN"] = df_show["NGUOI_NHAN"].apply(
            lambda x: lookup_display(x, df_ns, "ID_NHAN_SU", ["HO_TEN"])
        )

    # Map dự án/gói thầu
    df_show["DU_AN"] = df_show["IDDA_CV"].map(da_map).fillna("-")
    df_show["GOI_THAU"] = df_show["IDGT_CV"].map(gt_map).fillna("-")

    # Format ngày
    if "HAN_CHOT" in df_show:
        df_show["HAN_CHOT"] = df_show["HAN_CHOT"].apply(format_date_vn)

    # Xuất Excel
    excel_buffer = io.BytesIO()
    df_show.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    st.download_button(
        label="📥 Tải Excel",
        data=excel_buffer,
        file_name="bao_cao_cong_viec.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Hiển thị bảng
    st.dataframe(
        df_show.style.applymap(highlight_status, subset=['TRANG_THAI_TONG']),
        use_container_width=True,
        hide_index=True
    )
