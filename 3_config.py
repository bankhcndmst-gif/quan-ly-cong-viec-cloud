# =========================================================
# ✅ CONFIG.PY — CẤU HÌNH CHUNG CHO TOÀN BỘ HỆ THỐNG QLCV + GEMINI
# =========================================================

# =========================================================
# ✅ 1. DANH SÁCH SHEET BẮT BUỘC PHẢI CÓ
# =========================================================
REQUIRED_SHEETS = [
    "1_NHAN_SU",
    "2_DON_VI",
    "3_VAN_BAN",
    "4_DU_AN",
    "5_GOI_THAU",
    "6_HOP_DONG",
    "7_CONG_VIEC",
    "8_CAU_HINH",
    "9_TRI_NHO_AI",     # Lưu hỏi–đáp Gemini
    "10_TRAO_DOI",      # Chat nội bộ theo công việc
    "10_TRI_NHO_AI",    # Trí nhớ AI dài hạn (nhắc việc, biên bản họp…)
]


# =========================================================
# ✅ 2. CÁC CỘT NGÀY CẦN PARSE TỰ ĐỘNG
# =========================================================
DATE_COLS = [
    "NGAY_BAN_HANH",
    "NGAY_BD",
    "NGAY_KT",
    "NGAY_KY",
    "NGAY_HIEU_LUC",
    "NGAY_KET_THUC",
    "NGAY_GIAO",
    "HAN_CHOT",
    "NGAY_THUC_TE_XONG",
    "THOI_GIAN",
    "NGAY_TAO",
]


# =========================================================
# ✅ 3. CẤU HÌNH LIÊN KẾT ID → MÔ TẢ
#    Dùng cho dropdown, lookup, hiển thị mô tả
# =========================================================
LINK_CONFIG_RAW = {
    # -----------------------------------------------------
    # ✅ 1. NHÂN SỰ
    # -----------------------------------------------------
    "1_NHAN_SU": {
        "ID_COL": "ID_NHAN_SU",
        "DISPLAY_COLS": ["HO_TEN", "CHUC_VU", "DIEN_THOAI"],
    },

    # -----------------------------------------------------
    # ✅ 2. ĐƠN VỊ
    # -----------------------------------------------------
    "2_DON_VI": {
        "ID_COL": "ID_DON_VI",
        "DISPLAY_COLS": ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"],
        "LINK_COLS": {
            "IDNS_TEN_GIAM_DOC": ("1_NHAN_SU", "ID_NHAN_SU"),
            "IDNS_TEN_LIEN_HE": ("1_NHAN_SU", "ID_NHAN_SU"),
        },
    },

    # -----------------------------------------------------
    # ✅ 3. VĂN BẢN
    # -----------------------------------------------------
    "3_VAN_BAN": {
        "ID_COL": "ID_VB",
        "DISPLAY_COLS": ["SO_VAN_BAN", "TRICH_YEU", "NGAY_BAN_HANH"],
        "LINK_COLS": {
            "IDNS_NGUOI_KY": ("1_NHAN_SU", "ID_NHAN_SU"),
            "IDNS_CHU_TRI": ("1_NHAN_SU", "ID_NHAN_SU"),
            "IDDV_BAN_HANH": ("2_DON_VI", "ID_DON_VI"),
            "IDDV_NHAN": ("2_DON_VI", "ID_DON_VI"),
            "IDDV_KY_HOP_DONG": ("2_DON_VI", "ID_DON_VI"),
            "IDDA_DU_AN": ("4_DU_AN", "ID_DU_AN"),
            "IDGT_GOI_THAU": ("5_GOI_THAU", "ID_GOI_THAU"),
            "IDHD_HOP_DONG": ("6_HOP_DONG", "ID_HOP_DONG"),
        },
    },

    # -----------------------------------------------------
    # ✅ 4. DỰ ÁN
    # -----------------------------------------------------
    "4_DU_AN": {
        "ID_COL": "ID_DU_AN",
        "DISPLAY_COLS": ["TEN_DU_AN", "MO_TA", "NGAY_BD"],
    },

    # -----------------------------------------------------
    # ✅ 5. GÓI THẦU
    # -----------------------------------------------------
    "5_GOI_THAU": {
        "ID_COL": "ID_GOI_THAU",
        "DISPLAY_COLS": ["TEN_GOI_THAU", "GIA_TRI", "NGAY_BD"],
        "LINK_COLS": {
            "IDDA_DU_AN": ("4_DU_AN", "ID_DU_AN"),
        },
    },

    # -----------------------------------------------------
    # ✅ 6. HỢP ĐỒNG
    # -----------------------------------------------------
    "6_HOP_DONG": {
        "ID_COL": "ID_HOP_DONG",
        "DISPLAY_COLS": ["SO_HD", "TEN_HD", "NGAY_KY"],
        "LINK_COLS": {
            "IDDA_DU_AN": ("4_DU_AN", "ID_DU_AN"),
            "IDGT_GOI_THAU": ("5_GOI_THAU", "ID_GOI_THAU"),
            "IDDV_BEN_A": ("2_DON_VI", "ID_DON_VI"),
            "IDDV_BEN_B": ("2_DON_VI", "ID_DON_VI"),
        },
    },

    # -----------------------------------------------------
    # ✅ 7. CÔNG VIỆC
    # -----------------------------------------------------
    "7_CONG_VIEC": {
        "ID_COL": "ID_CONG_VIEC",
        "DISPLAY_COLS": ["TEN_VIEC", "NOI_DUNG", "HAN_CHOT"],
        "LINK_COLS": {
            "NGUOI_GIAO": ("1_NHAN_SU", "ID_NHAN_SU"),
            "NGUOI_NHAN": ("1_NHAN_SU", "ID_NHAN_SU"),
            "IDDV_CV": ("2_DON_VI", "ID_DON_VI"),
            "IDDA_CV": ("4_DU_AN", "ID_DU_AN"),
            "IDGT_CV": ("5_GOI_THAU", "ID_GOI_THAU"),
            "IDHD_CV": ("6_HOP_DONG", "ID_HOP_DONG"),
            "IDVB_VAN_BAN": ("3_VAN_BAN", "ID_VB"),
        },
    },

    # -----------------------------------------------------
    # ✅ 9. TRÍ NHỚ AI (HỎI–ĐÁP)
    # -----------------------------------------------------
    "9_TRI_NHO_AI": {
        "ID_COL": "ID_CHAT",
        "DISPLAY_COLS": ["THOI_GIAN", "CAU_HOI", "CAU_TRA_LOI"],
    },

    # -----------------------------------------------------
    # ✅ 10. TRAO ĐỔI CÔNG VIỆC
    # -----------------------------------------------------
    "10_TRAO_DOI": {
        "ID_COL": "ID_CONG_VIEC",
        "DISPLAY_COLS": ["NGUOI_GUI", "NOI_DUNG", "THOI_GIAN"],
        "LINK_COLS": {
            "ID_CONG_VIEC": ("7_CONG_VIEC", "ID_CONG_VIEC"),
            "NGUOI_GUI": ("1_NHAN_SU", "ID_NHAN_SU"),
        },
    },

    # -----------------------------------------------------
    # ✅ 10. TRÍ NHỚ AI DÀI HẠN
    # -----------------------------------------------------
    "10_TRI_NHO_AI": {
        "ID_COL": "NOI_DUNG",
        "DISPLAY_COLS": ["LOAI", "THOI_GIAN", "TOM_TAT"],
    },
}
