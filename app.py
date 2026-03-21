import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap');
    [data-testid="stSidebar"] { display: none; }
    
    /* Đẩy toàn bộ cụm Header sang sát bên phải */
    .header-right-container {
        float: right;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: -30px;
        margin-bottom: 20px;
    }
    
    .user-greet {
        font-size: 15px;
        color: #333;
        font-weight: 500;
    }

    /* Nút đăng xuất nhỏ gọn sát lời chào */
    .stButton > button[key="logout_btn"] {
        background-color: #ff4b4b !important;
        color: white !important;
        border: none !important;
        width: 28px !important;
        height: 28px !important;
        border-radius: 4px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    .stButton button { width: 100%; border-radius: 6px; height: 38px; font-weight: bold; }
    div[data-testid="column"]:nth-of-type(2) button[kind="secondary"] { background-color: #007bff; color: white; border: none; }
    .save-btn button { background-color: #28a745 !important; color: white !important; border: none !important; }
    div[data-testid="stTextInput"] input { height: 42px; border-radius: 6px; }
    .header-text { font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 14px; }
    .row-divider { border-bottom: 1px solid #ebedef; padding: 12px 0; }
    
    /* Thông báo lỗi đỏ dưới ô nhập */
    .error-msg { color: #ff4b4b; font-size: 13px; margin-top: 5px; font-weight: bold; }
    
    .brand-title { font-family: 'Playfair Display', serif; font-size: 32px; font-weight: 800; color: #1a1a1a; margin-bottom: 5px; text-align: center; }
    .brand-sub { font-family: 'Playfair Display', serif; font-size: 18px; color: #444; margin-bottom: 30px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI DATA ---
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
if 'search_error' not in st.session_state: st.session_state['search_error'] = ""

# --- LOGIN ---
if not st.session_state['logged_in']:
    _, mid_col, _ = st.columns([1, 1.2, 1])
    with mid_col:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-title'>Data Vinhomes Smart City</div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-sub'>Liên hệ Admin Ninh - 0912.791.925</div>", unsafe_allow_html=True)
        u_val = st.text_input("Tài khoản").strip()
        p_val = st.text_input("Mật khẩu", type="password").strip()
        if st.button("Đăng nhập"):
            try:
                sh_u = doc.worksheet("QUAN_LY_USER")
                data = sh_u.get_all_values()
                users_df = pd.DataFrame(data[1:], columns=data[0])
                auth = users_df[(users_df['Username'].astype(str) == u_val) & (users_df['Password'].astype(str) == p_val)]
                if not auth.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = auth.iloc[0]['Tên nhân viên']
                    st.rerun()
                else: st.error("Sai tài khoản hoặc mật khẩu!")
            except: st.error("Lỗi kết nối.")
else:
    # --- HEADER SÁT PHẢI ---
    # Container này sẽ ép cụm chào + nút X về mép phải màn hình
    st.markdown('<div class="header-right-container">', unsafe_allow_html=True)
    cols_h = st.columns([15, 1]) # Tỷ lệ cực lớn để đẩy nút về cuối
    with cols_h[0]:
        st.markdown(f'<div class="user-greet" style="text-align: right;">Xin chào <b>{st.session_state["user_name"]}!</b></div>', unsafe_allow_html=True)
    with cols_h[1]:
        if st.button("❌", key="logout_btn"):
            st.session_state.clear()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- TẢI DỮ LIỆU ---
    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_vals = sh_data.get_all_values()
        h_names = raw_vals[0]
        df_main = pd.DataFrame(raw_vals[1:], columns=h_names)
        df_main = df_main.applymap(lambda x: str(x).strip() if x is not None else "")

        # --- TÌM KIẾM ---
        tab_ma, tab_tieuchi = st.tabs(["🔍 Tìm nhanh", "📊 Lọc chi tiết"])

        with tab_ma:
            c_in, c_btn, _ = st.columns([2, 0.8, 3])
            with c_in:
                search_ma = st.text_input("Mã căn", key="input_ma", label_visibility="collapsed", placeholder="Nhập mã căn (VD: S1.01.10.20)...")
                if st.session_state['search_error']:
                    st.markdown(f"<div class='error-msg'>⚠️ {st.session_state['search_error']}</div>", unsafe_allow_html=True)
            
            with c_btn:
                if st.button("Tìm kiếm", key="btn_find_ma") or (search_ma and st.session_state.get('last_trigger') != search_ma):
                    st.session_state['last_trigger'] = search_ma
                    if search_ma:
                        res = df_main[df_main['Mã đầy đủ'].str.contains(search_ma.strip(), case=False)]
                        if res.empty:
                            st.session_state['search_error'] = f"Mã căn '{search_ma}' không tồn tại."
                            st.session_state['res_df'] = pd.DataFrame()
                        else:
                            st.session_state['search_error'] = ""
                            st.session_state['res_df'] = res
                        st.rerun()
        
        # ... (Phần lọc chi tiết và hiển thị bảng giữ nguyên) ...
        # [Để ngắn gọn, tôi không lặp lại code phần bảng hiển thị bên dưới]
