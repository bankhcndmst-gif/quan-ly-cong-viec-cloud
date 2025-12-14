with tab_input:
    st.header("📝 Giao Công Việc Mới (Sheet 7_CONG_VIEC)")

    lists = get_display_lists(all_sheets)
    df_ns = all_sheets["1_NHAN_SU"]
    df_dv = all_sheets["2_DON_VI"]

    with st.form("form_new_work_full"):

        # ============================
        # PHẦN A – THÔNG TIN CHÍNH
        # ============================
        st.subheader("A. Thông tin chính (bắt buộc)")

        colA1, colA2 = st.columns(2)

        with colA1:
            ten_viec = st.text_input("Tên công việc *")
            loai_viec = st.selectbox("Loại công việc", lists["loai_viec"])
            nguon_giao_viec = st.text_input("Nguồn giao việc (Văn bản, email, họp...)")
            nguoi_giao_display = st.selectbox("Người giao", lists["ns_display"])
            ngay_giao = st.date_input("Ngày giao", datetime.now().date())

        with colA2:
            noi_dung = st.text_area("Nội dung chi tiết")
            nguoi_nhan_display = st.selectbox("Người nhận *", lists["ns_display"])
            han_chot = st.date_input("Hạn chót", datetime.now().date() + timedelta(days=7))
            trang_thai_tong = st.selectbox("Trạng thái tổng", lists["trang_thai"])
            trang_thai_chi_tiet = st.text_input("Trạng thái chi tiết")

        # Ngày hoàn thành
        da_xong = st.checkbox("Đã hoàn thành?")
        ngay_thuc_te_xong = (
            st.date_input("Ngày thực tế hoàn thành", datetime.now().date())
            if da_xong else None
        )

        st.markdown("---")

        # ============================
        # PHẦN B – LIÊN KẾT & BỔ SUNG
        # ============================
        st.subheader("B. Liên kết dữ liệu & thông tin bổ sung")

        colB1, colB2, colB3 = st.columns(3)

        with colB1:
            idvb_display = st.selectbox("ID Văn bản (IDVB_VAN_BAN)", lists["vb_display"])
            idda_display = st.selectbox("ID Dự án (IDDA_CV)", lists["da_display"])
            iddv_display = st.selectbox("ID Đơn vị (IDDV_CV)", lists["dv_display"])

        with colB2:
            idhd_display = st.selectbox("ID Hợp đồng (IDHD_CV)", lists["hd_display"])
            idgt_display = st.selectbox("ID Gói thầu (IDGT_CV)", lists["gt_display"])
            nguoi_phoi_hop = st.text_input("Người phối hợp (ID)")

        with colB3:
            vuong_mac = st.text_area("Vướng mắc")
            de_xuat = st.text_area("Đề xuất")
            ghi_chu_cv = st.text_area("Ghi chú công việc")

        submitted = st.form_submit_button("✅ LƯU VÀ GIAO VIỆC MỚI", type="primary")

        if submitted:
            if not ten_viec or nguoi_nhan_display == "Chọn ID":
                st.error("⚠️ Vui lòng nhập Tên công việc và chọn Người nhận hợp lệ.")
            else:
                new_data = {
                    "ten_viec": ten_viec,
                    "noi_dung": noi_dung,
                    "loai_viec": loai_viec,
                    "nguon_giao_viec": nguon_giao_viec,
                    "nguoi_giao": extract_id_from_display(nguoi_giao_display),
                    "nguoi_nhan": extract_id_from_display(nguoi_nhan_display),
                    "ngay_giao": ngay_giao,
                    "han_chot": han_chot,
                    "nguoi_phoi_hop": nguoi_phoi_hop,
                    "trang_thai_tong": trang_thai_tong,
                    "trang_thai_chi_tiet": trang_thai_chi_tiet,
                    "ngay_thuc_te_xong": ngay_thuc_te_xong,

                    "idvb_van_ban": extract_id_from_display(idvb_display),
                    "idhd_cv": extract_id_from_display(idhd_display),
                    "idda_cv": extract_id_from_display(idda_display),
                    "idgt_cv": extract_id_from_display(idgt_display),
                    "iddv_cv": extract_id_from_display(iddv_display),

                    "vuong_mac": vuong_mac,
                    "de_xuat": de_xuat,
                    "ghi_chu_cv": ghi_chu_cv,
                }

                append_new_work(new_data, df_cv)
