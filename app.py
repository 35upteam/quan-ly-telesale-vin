import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS TÁCH BIỆT LAPTOP - MOBILE ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&display=swap');
    [data-testid="stSidebar"] { display: none; }
    
    /* Trang đăng nhập: Luôn 1 dòng */
    .brand-title { 
        font-family: 'Playfair Display', serif; 
        font-size: clamp(20px, 5vw, 30px); 
        font-weight: 800; color: #1a1a1a; 
        text-align: center; white-space: nowrap; 
    }

    /* Header Xin chào & Nút X */
    .header-box {
        display: flex; justify-content: flex-end; align-items: center;
        gap: 10px; margin-top: -50px; margin-bottom: 20px;
    }

    /* CSS CHO LAPTOP (Màn hình > 768px) */
    @media (min-width: 769px) {
        .mobile-only { display: none !important; }
        .header-text { font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; font-size: 14px; }
    }

    /* CSS CHO MOBILE (Màn hình <= 768px) */
    @media (max-width: 768px) {
        .laptop-only { display: none !important; }
        .mobile-row { 
            background: #f8f9fa; border-radius: 8px; padding: 10px; 
            margin-bottom: 10px; border-left: 4px solid #3498db;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    }

    .row-divider { border-bottom: 1px solid #ebedef; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI & LOAD DATA ---
@st.cache_resource
def get_db():
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n").strip()
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        return gspread.authorize(creds).open("Data Vin")
    except: return None

@st.cache_data(ttl=300)
def load_data(name):
    try:
        sh = get_db().worksheet(name)
        data = sh.get_all_values()
        return pd.DataFrame(data[1:], columns=data[0]).applymap(lambda x: str(x).strip() if x else "")
    except: return pd.DataFrame()

# --- 3. KHỞI TẠO STATE (QUAN TRỌNG ĐỂ KHÔNG LỖI TAB) ---
if 'res_df' not in st.session_state: st.session_state['res_df'] = pd.DataFrame()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

# --- 4. GIAO DIỆN ---
if not st.session_state['logged_in']:
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-title'>Data Vinhomes Smart City</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; color: #666;'>Admin Ninh - 0912.791.925</div>", unsafe_allow_html=True)
    
    _, mid, _ = st.columns([1, 1.5, 1])
    with mid:
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập", use_container_width=True):
            users = load_data("QUAN_LY_USER")
            auth = users[(users['Username'] == u) & (users['Password'] == p)]
            if not auth.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = auth.iloc[0]['Tên nhân viên']
                st.rerun()
            else: st.error("Sai thông tin!")
else:
    # Header chuẩn
    st.markdown(f'<div class="header-box"><span class="user-greet">Chào <b>{st.session_state["user_name"]}!</b></span></div>', unsafe_allow_html=True)
    c_out_1, c_out_2 = st.columns([9.3, 0.7])
    if c_out_2.button("❌", key="logout"):
        st.session_state.clear()
        st.rerun()

    if st.button("🔄 Làm mới"):
        st.cache_data.clear()
        st.rerun()

    df_main = load_data("DATA_CAN_HO")
    tab1, tab2 = st.tabs(["🔍 Tìm nhanh", "📊 Lọc nâng cao"])

    with tab1:
        with st.form("search_form"):
            ma = st.text_input("Nhập mã căn cụ thể", placeholder="Ví dụ: S1.01...")
            if st.form_submit_button("TÌM KIẾM"):
                if ma:
                    st.session_state['res_df'] = df_main[df_main['Mã đầy đủ'].str.contains(ma, case=False)]
                    st.rerun()

    with tab2:
        with st.form("filter_form"):
            c1, c2 = st.columns(2)
            toa_list = sorted([t for t in df_main['Tòa'].unique() if t])
            sel_t = c1.multiselect("Chọn Tòa", toa_list)
            sel_l = c2.multiselect("Loại hình", ["1N", "1N+1", "2N", "3N"])
            if st.form_submit_button("🚀 LỌC DỮ LIỆU"):
                f_df = df_main.copy()
                if sel_t: f_df = f_df[f_df['Tòa'].isin(sel_t)]
                if sel_l: f_df = f_df[f_df['Loại hình'].isin(sel_l)]
                st.session_state['res_df'] = f_df
                st.rerun()

    # --- 5. HIỂN THỊ KẾT QUẢ ĐA THIẾT BỊ ---
    res = st.session_state['res_df']
    if not res.empty:
        st.write(f"Tìm thấy **{len(res)}** căn")

        # --- GIAO DIỆN LAPTOP (BẢNG NGANG CHUẨN) ---
        st.markdown('<div class="laptop-only">', unsafe_allow_html=True)
        h = st.columns([1.2, 1.2, 0.8, 0.6, 1.5, 2.5, 0.6])
        t_list = ["Mã Căn", "Chủ Nhà", "Loại", "DT", "SĐT", "Ghi chú", "Lưu"]
        for col, txt in zip(h, t_list): col.markdown(f"<div class='header-text'>{txt}</div>", unsafe_allow_html=True)
        
        for i, r in res.iterrows():
            row = st.columns([1.2, 1.2, 0.8, 0.6, 1.5, 2.5, 0.6])
            row[0].write(f"**{r['Mã đầy đủ']}**")
            row[1].write(r['Chủ nhà'])
            row[2].write(r.get('Loại hình','-'))
            row[3].write(f"{r['Diện tích']}m²")
            s_key = f"v_{r['Mã đầy đủ']}"
            if st.session_state.get(s_key): row[4].code(r['Số điện thoại'])
            else: 
                if row[4].button("👁️", key=f"lp_v_{i}"):
                    st.session_state[s_key] = True
                    st.rerun()
            row[5].text_input("N", value=r.get('Ghi chú',''), key=f"lp_n_{i}", label_visibility="collapsed")
            if row[6].button("💾", key=f"lp_s_{i}"): st.toast("Lưu thành công!")
            st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- GIAO DIỆN MOBILE (DỌC THÔNG MINH - KHÔNG KÉO NGANG) ---
        st.markdown('<div class="mobile-only">', unsafe_allow_html=True)
        for i, r in res.iterrows():
            with st.container():
                st.markdown(f"""
                <div class='mobile-row'>
                    <b>🏢 {r['Mã đầy đủ']}</b> | {r.get('Loại hình','-')} | {r['Diện tích']}m²<br>
                    <small>Chủ nhà: {r['Chủ nhà']}</small>
                </div>
                """, unsafe_allow_html=True)
                mc1, mc2 = st.columns(2)
                s_key = f"vm_{r['Mã đầy đủ']}"
                if st.session_state.get(s_key): mc1.code(r['Số điện thoại'])
                else:
                    if mc1.button("📞 Xem SĐT", key=f"mb_v_{i}"):
                        st.session_state[s_key] = True
                        st.rerun()
                if mc2.button("💾 Lưu Note", key=f"mb_s_{i}"): st.toast("Đã lưu!")
                st.text_input("Ghi chú", value=r.get('Ghi chú',''), key=f"mb_n_{i}", label_visibility="collapsed")
                st.divider()
        st.markdown('</div>', unsafe_allow_html=True)
