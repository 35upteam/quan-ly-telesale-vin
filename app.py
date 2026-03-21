import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. KẾT NỐI QUA SECRETS (DÀNH CHO DEPLOY LÊN CLOUD) ---
def init_connection():
    # Streamlit sẽ tự lấy thông tin từ mục Secrets bạn đã dán vào trước đó
    creds_info = st.secrets["gcp_service_account"]
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Sử dụng hàm from_json_keyfile_dict thay vì from_json_keyfile_name
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    client = gspread.authorize(creds)
    return client.open("Data Vin")

# Thử kết nối
try:
    doc = init_connection()
    sh_data = doc.worksheet("DATA_CAN_HO")
    sh_user = doc.worksheet("QUAN_LY_USER")
    sh_log = doc.worksheet("LOG_TRUY_CAP")
except Exception as e:
    st.error(f"Lỗi kết nối Secrets: {e}")
    st.info("Kiểm tra lại mục Settings -> Secrets trên Streamlit Cloud xem bạn đã dán đúng định dạng TOML chưa.")
    st.stop()

# --- CÁC PHẦN CODE CÒN LẠI (GIỮ NGUYÊN NHƯ CŨ) ---
# (Phần xử lý Đăng nhập, Bộ lọc, Hiển thị danh sách...)
