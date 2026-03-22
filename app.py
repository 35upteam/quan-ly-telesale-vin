import streamlit as st
import pandas as pd
import gspread
import time 
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS TỐI ƯU CÂN ĐỐI MÀN HÌNH ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap');
    [data-testid="stSidebar"] { display: none; }
    
    /* Tiêu đề: Căn giữa và cho phép xuống dòng tự nhiên trên mobile */
    .brand-title { 
        font-family: 'Playfair Display', serif; 
        font-size: 32px; 
        font-weight: 800; color: #1a1a1a; 
        margin-bottom: 10px; 
        text-align: center;
        line-height: 1.2;
    }
    .brand-sub { 
        font-family: 'Playfair Display', serif; 
        font-size: 18px; color: #444; 
        margin-bottom: 30px; 
        text-align: center; 
    }

    /* FIX CÂN ĐỐI TRÊN MOBILE */
    @media (max-width: 768px) {
        /* Bỏ chia cột, cho form rộng 90% màn hình và căn giữa */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            padding: 0 10px !important;
        }
        
        /* Căn chỉnh lại khoảng cách lề cho đẹp */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* Tiêu đề thu nhỏ một chút cho vừa màn hình dọc */
        .brand-title { font-size: 26px; white-space: normal !important; }
    }

    /* Header sau khi đăng nhập */
    .header-right-container {
        display: flex; justify-content: flex-end; align-items: center;
        gap: 8px; margin-top: -45px; margin-bottom: 25px; width: 100%;
    }
    .user-greet { font-size: 14px; color: #333; white-space: nowrap; }
    .stButton > button[key="logout_btn"] {
        background-color: #ff4b4b !important; color: white !important; border: none !important;
        width: 28px !important; height: 28px !important; border-radius: 4px !important;
    }
    .header-text { font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 13px; }
    .row-divider { border-bottom: 1px solid #ebedef; padding: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# (Phần INIT_CONNECTION giữ nguyên của bạn)
@st.cache_resource
def init_connection():
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n").strip()
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        return client.open("Data Vin")
    except: return None

doc = init_connection()

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

# --- 2. ĐĂNG NHẬP CÂN ĐỐI ---
if not st.session_state['logged_in']:
    # Trên máy tính sẽ căn giữa bằng cột, trên Mobile sẽ tràn 100% nhờ CSS
    _, mid_col, _ = st.columns([1, 1.5, 1]) 
    with mid_col:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-title'>Data Vinhomes Smart City</div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-sub'>Liên hệ Admin Ninh - 0912.791.925</div>", unsafe_allow_html=True)
        
        u_val = st.text_input("Tài khoản").strip()
        p_val = st.text_input("Mật khẩu", type="password").strip()
        
        if st.button("Đăng nhập", use_container_width=True):
            success = False
            for attempt in range(3):
                try:
                    sh_u = doc.worksheet("QUAN_LY_USER")
                    data = sh_u.get_all_values()
                    users_df = pd.DataFrame(data[1:], columns=data[0])
                    auth = users_df[(users_df['Username'].astype(str) == u_val) & (users_df['Password'].astype(str) == p_val)]
                    
                    if not auth.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = auth.iloc[0]['Tên nhân viên']
                        success = True
                        break
                    else:
                        st.error("Tài khoản hoặc mật khẩu không đúng!")
                        success = True
                        break
                except:
                    if attempt < 2: time.sleep(1); continue
            if success: st.rerun()
