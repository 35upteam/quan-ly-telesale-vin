import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Telesale", layout="wide")

# --- 1. KẾT NỐI HỆ THỐNG (SỬA LỖI PADDING) ---
@st.cache_resource
def init_connection():
    try:
        # Lấy bản sao của Secrets để chỉnh sửa
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # SỬA LỖI INCORRECT PADDING: Tự động thay thế ký tự xuống dòng
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        
        # Mở file Google Sheets
        return client.open("Data Vin")
    except Exception as e:
        st.error(f"Lỗi kết nối Secrets: {e}")
        st.stop()
        return None

# Khởi tạo các Sheet
doc = init_connection()
if doc:
    sh_data = doc.worksheet("DATA_CAN_HO")
    sh_user = doc.worksheet("QUAN_LY_USER")
    sh_log = doc.worksheet("LOG_TRUY_CAP")
else:
    st.stop()

# --- 2. HÀM ĐỌC DỮ LIỆU ---
@st.cache_data(ttl=600)
def get_data(worksheet):
    return pd.DataFrame(worksheet.get_all_records())

# --- 3. LOGIC ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập Hệ thống Telesale")
    user_input = st.text_input("Tên đăng nhập")
    pass_input = st.text_input("Mật khẩu", type="password")
    
    if st.button("Đăng nhập"):
        users_df = get_data(sh_user)
        user_auth = users_df[(users_df['Username'] == user_input) & (users_df['Password'].astype(str) == pass_input)]
        
        if not user_auth.empty:
            st.session_state['logged_in'] = True
            st.session_state['user_name'] = user_input
            st.rerun()
        else:
            st.error("Sai tài khoản hoặc mật khẩu!")
else:
    # --- 4. GIAO DIỆN CHÍNH ---
    st.sidebar.success(f"Chào mừng: {st.session_state['user_name']}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("🏘️ Tra cứu Căn hộ & Bảo mật SĐT")

    # Đọc dữ liệu căn hộ
    df = get_data(sh_data)
    df['Tầng'] = pd.to_numeric(df['Tầng'], errors='coerce')
    df['Trục'] = df['Trục'].astype(str)

    # BỘ LỌC SIDEBAR
    st.sidebar.header("🔍 Bộ lọc thông minh")
    list_toa = ["Tất cả"] + sorted(list(df['Tòa'].unique()))
    selected_toa = st.sidebar.selectbox("Chọn Tòa nhà", list_toa)
    
    list_truc = sorted(list(df['Trục'].unique()))
    selected_truc = st.sidebar.multiselect("Chọn Trục căn", list_truc)
    
    min_f = int(df['Tầng'].min())
    max_f = int(df['Tầng'].max())
    floor_range = st.sidebar.slider("Khoảng tầng", min_f, max_f, (min_f, max_f))
