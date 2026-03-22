import streamlit as st
import pandas as pd
import gspread
import time 
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS (GIỮ NGUYÊN BẢN BẠN ƯNG Ý - KHÔNG THAY ĐỔI 1 CĂN CHỈNH NÀO) ---
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
    
    /* Giữ màu đỏ cho nút đăng nhập chính */
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

# --- 3. PHẦN CHỨC NĂNG (SAU KHI ĐĂNG NHẬP) ---
else:
    # Header: Xin chào (Dùng đúng class header-right-container của bạn)
    st.markdown(f'<div class="header-right-container"><span class="user-greet">Xin chào <b>{st.session_state["user_name"]}!</b></span></div>', unsafe_allow_html=True)
    
    # Nút thoát nằm riêng để không phá vỡ dòng xin chào
    _, c_logout = st.columns([9, 1])
    with c_logout:
        if st.button("Thoát", key="logout_btn"):
            st.session_state.clear()
            st.rerun()

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw = sh_data.get_all_values()
        df_main = pd.DataFrame(raw[1:], columns=raw[0]).applymap(lambda x: str(x).strip())

        # Khu vực lọc
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1: toa_sel = st.multiselect("Tòa", sorted(df_main['Tòa'].unique()))
        with c2: tang_sel = st.multiselect("Tầng", LIST_TANG_PHYSICAL)
        with c3: truc_sel = st.multiselect("Trục", LIST_TRUC)

        if st.button("Lọc căn hộ", use_container_width=True):
            res = df_main.copy()
            if toa_sel: res = res[res['Tòa'].isin(toa_sel)]
            if tang_sel: res = res[res['Tầng'].isin(tang_sel)]
            if truc_sel: res = res[res['Trục'].isin(truc_sel)]
            st.session_state['res_df'] = res

        # Hiển thị danh sách
        res_df = st.session_state['res_df']
        if not res_df.empty:
            st.divider()
            # Tận dụng st.columns để khớp với CSS overflow-x của bạn
            h_cols = st.columns([1.5, 1.5, 1, 2, 3, 1])
            t_names = ["Mã Căn", "Chủ Nhà", "DT", "SĐT", "Ghi chú", "Lưu"]
            for col, t in zip(h_cols, t_names):
                col.markdown(f"<div class='header-text'>{t}</div>", unsafe_allow_html=True)
            
            for i, r in res_df.iterrows():
                r_cols = st.columns([1.5, 1.5, 1, 2, 3, 1])
                r_cols[0].write(f"**{r['Mã đầy đủ']}**")
                r_cols[1].write(r['Chủ nhà'])
                r_cols[2].write(f"{r['Diện tích']}m²")
                r_cols[3].write(r['Số điện thoại'])
                
                # Ghi chú & Lưu
                note_val = r_cols[4].text_input("G", value=r.get('Ghi chú', ''), key=f"n_{i}", label_visibility="collapsed")
                if r_cols[5].button("💾", key=f"s_{i}"):
                    try:
                        cell = sh_data.find(r['Mã đầy đủ'])
                        sh_data.update_cell(cell.row, raw[0].index('Ghi chú') + 1, note_val)
                        st.toast("Đã lưu!")
                    except: st.error("Lỗi!")
                st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)

    except Exception as e:
        st.error("Vui lòng kiểm tra lại Google Sheets.")
