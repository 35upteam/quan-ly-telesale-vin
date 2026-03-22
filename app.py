import streamlit as st
import pandas as pd
import gspread
import time 
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS TỐI ƯU RIÊNG TRANG ĐĂNG NHẬP ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap');
    [data-testid="stSidebar"] { display: none; }
    
    /* FIX: Tiêu đề đăng nhập luôn 1 dòng */
    .brand-title { 
        font-family: 'Playfair Display', serif; 
        font-size: clamp(20px, 7vw, 30px); 
        font-weight: 800; color: #1a1a1a; 
        margin-bottom: 5px; text-align: center; 
        white-space: nowrap; 
    }
    .brand-sub { font-family: 'Playfair Display', serif; font-size: 16px; color: #444; margin-bottom: 30px; text-align: center; }

    /* FIX CỰC MẠNH: Trang đăng nhập trên Điện thoại */
    @media (max-width: 768px) {
        /* Ép tất cả các cột của Streamlit phải tràn 100% chiều rộng */
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            display: block !important;
            padding: 0px !important;
        }
        
        /* Chỉnh lại padding cho form đăng nhập bớt sát mép màn hình */
        div[data-testid="stVerticalBlock"] > div {
            padding-left: 5px;
            padding-right: 5px;
        }

        /* Vẫn giữ khả năng cuộn ngang bảng kết quả sau khi đăng nhập */
        div[data-testid="stHorizontalBlock"] {
            overflow-x: auto !important;
            display: flex !important;
            flex-wrap: nowrap !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            min-width: 140px !important;
            flex-shrink: 0 !important;
        }
    }

    /* Header Xin chào & Nút X sát phải */
    .header-right-container {
        display: flex; justify-content: flex-end; align-items: center;
        gap: 8px; margin-top: -45px; margin-bottom: 25px; width: 100%;
    }
    .user-greet { font-size: 14px; color: #333; white-space: nowrap; }

    .stButton > button[key="logout_btn"] {
        background-color: #ff4b4b !important; color: white !important; border: none !important;
        width: 28px !important; height: 28px !important; border-radius: 4px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }
    .header-text { font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 13px; white-space: nowrap; }
    .row-divider { border-bottom: 1px solid #ebedef; padding: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- GIỮ NGUYÊN TOÀN BỘ LOGIC CÒN LẠI ---
# (Phần INIT_CONNECTION, LOGIN LOGIC và DATA DISPLAY giữ y hệt bản cũ của bạn)

if not st.session_state.get('logged_in', False):
    # Laptop: Form nằm giữa (1-1.2-1)
    # Mobile: CSS trên sẽ ép 3 cột này thành 3 hàng dọc, hàng giữa chứa Form sẽ rộng 100%
    _, mid_col, _ = st.columns([1, 1.2, 1])
    with mid_col:
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-title'>Data Vinhomes Smart City</div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-sub'>Liên hệ Admin Ninh - 0912.791.925</div>", unsafe_allow_html=True)
        u_val = st.text_input("Tài khoản").strip()
        p_val = st.text_input("Mật khẩu", type="password").strip()
        
        # Nút đăng nhập to rõ trên Mobile
        if st.button("Đăng nhập", use_container_width=True):
            # ... (Giữ nguyên logic kiểm tra Username/Password của bạn)
            pass
