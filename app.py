import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    
    /* Căn giữa màn hình đăng nhập */
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding-top: 50px;
    }
    
    .login-box {
        width: 350px;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        background-color: white;
        text-align: center;
    }

    .stButton button { width: 100%; border-radius: 6px; height: 38px; }
    div[data-testid="stTextInput"] input { height: 40px; }
    
    /* Header nội dung */
    .header-text { font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 14px; }
    .row-divider { border-bottom: 1px solid #ebedef; padding: 12px 0; }
    code { font-size: 14px !important; color: #1e88e5 !important; background-color: #f1f3f4 !important; border: 1px solid #dee2e6 !important; }
    
    /* Text giới thiệu */
    .sub-text { color: #666; font-size: 14px; margin-bottom: 20px; }
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
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return None

doc = init_connection()

if 'res_df' not in st.session_state:
    st.session_state['res_df'] = pd.DataFrame()
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 2. GIAO DIỆN ĐĂNG NHẬP (CĂN GIỮA) ---
if not st.session_state['logged_in']:
    _, mid_col, _ = st.columns([1, 1, 1])
    with mid_col:
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
        st.title("🔐 Đăng nhập")
        st.markdown("""
            <div style='color: #555; margin-bottom: 20px;'>
                <b>Data Vinhomes Smart City</b><br>
                Liên hệ Admin Ninh - 0912.791.925
            </div>
        """, unsafe_allow_html=True)
        
        u_val = st.text_input("Tài khoản").strip()
        p_val = st.text_input("Mật khẩu", type="password").strip()
        
        if st.button("Đăng nhập"):
            try:
                sh_u = doc.worksheet("QUAN_LY_USER")
                users_df = pd.DataFrame(sh_u.get_all_records())
                auth = users_df[(users_df['Username'].astype(str) == u_val) & (users_df['Password'].astype(str) == p_val)]
                if not auth.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = auth.iloc[0]['Tên nhân viên']
                    st.rerun()
                else:
                    st.error("Tài khoản hoặc mật khẩu không đúng!")
            except:
                st.error("Lỗi kết nối dữ liệu người dùng.")
else:
    # --- 3. HEADER (XIN CHÀO & NÚT X ĐỎ) ---
    h_left, h_right = st.columns([8, 2])
    with h_right:
        c_user, c_logout = st.columns([4, 1])
        with c_user:
            st.markdown(f"<div style='padding-top: 8px; text-align: right; font-size: 14px;'>Xin chào <b>{st.session_state['user_name']}!</b></div>", unsafe_allow_html=True)
        with c_logout:
            if st.button("❌", key="logout_btn"):
                st.session_state.clear()
                st.rerun()

    # --- 4. TẢI DỮ LIỆU ---
    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_vals = sh_data.get_all_values()
        h_names = raw_vals[0]
        df_main = pd.DataFrame(raw_vals[1:], columns=h_names)
        
        df_main = df_main.applymap(lambda x: str(x).strip() if x is not None else "")
        df_main['Tòa_Clean'] = df_main['Tòa'].apply(lambda x: x.replace(".", ""))
        df_main['Trục_Clean'] = df_main['Trục'].apply(lambda x: x.replace(".0", "").zfill(2) if x else "")

        # --- 5. BỘ LỌC TABS ---
        tab_ma, tab_tieuchi = st.tabs(["🔍 Tìm nhanh", "📊 Lọc chi tiết"])

        with tab_ma:
            c_in, c_btn, _ = st.columns([2, 0.8, 3])
            with c_in:
                search_ma = st.text_input("Mã căn", key="input_ma", label_visibility="collapsed", placeholder="Nhập mã căn...")
            with c_btn:
                if st.button("Tìm kiếm", key="btn_find_ma"):
                    if search_ma:
                        st.session_state['res_df'] = df_main[df_main['Mã đầy đủ'].str.contains(search_ma.strip(), case=False)]
                    else:
                        st.warning("Nhập mã căn!")

        with tab_tieuchi:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            with c1: 
                ds_toa = sorted([t for t in df_main['Tòa'].unique() if t])
                sel_t = st.multiselect("Chọn Tòa", ds_toa)
            with c2
