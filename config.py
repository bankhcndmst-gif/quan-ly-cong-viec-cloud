# =========================================================
# CONFIG.PY — CẤU HÌNH CHUNG CHO TOÀN BỘ ỨNG DỤNG
# =========================================================

# Danh sách các sheet bắt buộc phải có trong Google Sheets
REQUIRED_SHEETS = [
    "1_NHAN_SU",
    "2_DON_VI",
    "3_VAN_BAN",
    "4_DU_AN",
    "5_GOI_THAU",
    "6_HOP_DONG",
    "7_CONG_VIEC",
    "8_CAU_HINH",
    "9_CHAT_GEMINI",
]

# Danh sách các cột ngày cần parse và định dạng dd/mm/yyyy
DATE_COLS = [
    "NGAY_GIAO",
    "HAN_CHOT",
    "NGAY_THUC_TE_XONG",
    "NGAY_BAN_HANH",
    "NGAY_BD",
    "NGAY_KY",
]

# =========================================================
# CẤU HÌNH LIÊN KẾT GIỮA CÁC BẢNG
# Dùng cho Tab 3 – Quản lý dữ liệu gốc
# =========================================================

# Format:
# sheet_name: {
#     "COLUMN_ID": (ref_sheet, ref_id_col, [list các cột mô tả])
# }

LINK_CONFIG_RAW = {
    "2_DON_VI": {
        "IDNS_TEN_GIAM_DOC": (
            "1_NHAN_SU",
            "ID_NHAN_SU",
            ["HO_TEN", "CHUC_VU", "DIEN_THOAI"],
        ),
        "IDNS_TEN_LIEN_HE": (
            "1_NHAN_SU",
            "ID_NHAN_SU",
            ["HO_TEN", "CHUC_VU", "DIEN_THOAI"],
        ),
    },

    "3_VAN_BAN": {
        "IDNS_NGUOI_KY": (
            "1_NHAN_SU",
            "ID_NHAN_SU",
            ["HO_TEN", "CHUC_VU", "DIEN_THOAI"],
        ),
        "IDDV_BAN_HANH": (
            "2_DON_VI",
            "ID_DON_VI",
            ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"],
        ),
        "IDDV_NHAN": (
            "2_DON_VI",
            "ID_DON_VI",
            ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"],
        ),
        "IDNS_CHU_TRI": (
            "1_NHAN_SU",
            "ID_NHAN_SU",
            ["HO_TEN", "CHUC_VU", "DIEN_THOAI"],
        ),
        "IDGT_GOI_THAU": (
            "5_GOI_THAU",
            "ID_GOI_THAU",
            ["TEN_GOI_THAU", "GIA_TRI", "NGAY_BD"],
        ),
        "IDDA_DU_AN": (
            "4_DU_AN",
            "ID_DU_AN",
            ["TEN_DU_AN", "MO_TA", "NGAY_BD"],
        ),
        "IDDV_KY_HOP_DONG": (
            "2_DON_VI",
            "ID_DON_VI",
            ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"],
        ),
        "IDHD_HOP_DONG": (
            "6_HOP_DONG",
            "ID_HOP_DONG",
            ["TEN_HD", "SO_HD", "NGAY_KY"],
        ),
    },

    "4_DU_AN": {
        "IDDV_CHU_DAU_TU": (
            "2_DON_VI",
            "ID_DON_VI",
            ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"],
        ),
    },

    "5_GOI_THAU": {
        "IDDA_DU_AN": (
            "4_DU_AN",
            "ID_DU_AN",
            ["TEN_DU_AN", "MO_TA", "NGAY_BD"],
        ),
    },

    "6_HOP_DONG": {
        "IDGT_GOI_THAU": (
            "5_GOI_THAU",
            "ID_GOI_THAU",
            ["TEN_GOI_THAU", "GIA_TRI", "NGAY_BD"],
        ),
        "IDDV_NHA_THAU": (
            "2_DON_VI",
            "ID_DON_VI",
            ["TEN_DON_VI", "DIA_CHI", "DIEN_THOAI"],
        ),
    },
}
