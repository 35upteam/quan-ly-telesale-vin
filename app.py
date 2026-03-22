import streamlit as st
import pandas as pd
import gspread
import time 
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS (GIỮ NGUYÊN BẢN BẠN ƯNG Ý) ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap');
    [data-testid="stSidebar"] { display: none; }
    
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

    @media (max-width: 768px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            padding: 0 10px !important;
        }
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        .brand-title { font-size: 26px; white-space: normal !important; }
        
        /* Cấu hình thêm để bảng dữ liệu bên trong không bị vỡ trên mobile */
        div[data-testid="stHorizontalBlock"] {
            overflow-x: auto !important;
            display: flex !important;
            flex-wrap: nowrap !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            min-width: 130px !important;
            flex-shrink: 0 !important;
        }
    }

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
    
    /* Đảm bảo các nút bấm chính (như Đăng nhập) có màu đỏ đồng bộ */
    .stButton > button {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

LIST_TANG_PHYSICAL = ["1", "2", "3", "05A", "05", "06", "07", "08", "08A", "09", "10", "11", "12", "12A", "15A", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]
LIST_TRUC = [f"{i:02d}" for i in range(1, 31)]

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

if 'res_df' not in st.session_state: st.session_state['res_df'] = pd.DataFrame()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

# --- 2. ĐĂNG NHẬP (GIỮ NGUYÊN BẢN BẠN ƯNG Ý) ---
if not st.session_state['logged_in']:
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

# --- 3. LOGIC HIỂN THỊ SAU ĐĂNG NHẬP ---
else:
    # Header hiển thị lời chào
    st.markdown(f'<div class="header-right-container"><span class="user-greet">Xin chào <b>{st.session_state["user_name"]}!</b></span></div>', unsafe_allow_html=True)
    
    # Nút đăng xuất (Logout)
    _, c_logout = st.columns([9, 1])
    with c_logout:
        if st.button("Thoát", key="logout_btn"):
            st.session_state.clear()
            st.rerun()

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw = sh_data.get_all_values()
        df_main = pd.DataFrame(raw[1:], columns=raw[0])

        # Bộ lọc tìm kiếm
        t1, t2 = st.tabs(["🔍 Tìm nhanh", "📊 Lọc chi tiết"])
        with t1:
            m_id = st.text_input("Nhập mã căn hộ...")
            if st.button("Tìm kiếm"):
                st.session_state['res_df'] = df_main[df_main['Mã đầy đủ'].str.contains(m_id, case=False)]

        with t2:
            c1, c2, c3 = st.columns(3)
            with c1: toa = st.multiselect("Tòa", sorted(df_main['Tòa'].unique()))
            with c2: tang = st.multiselect("Tầng", LIST_TANG_PHYSICAL)
            with c3: truc = st.multiselect("Trục", LIST_TRUC)
            if st.button("Áp dụng lọc"):
                res = df_main.copy()
                if toa: res = res[res['Tòa'].isin(toa)]
                if tang: res = res[res['Tầng'].isin(tang)]
                if truc: res = res[res['Trục'].isin(truc)]
                st.session_
