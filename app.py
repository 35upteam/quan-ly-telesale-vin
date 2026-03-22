import streamlit as st
import pandas as pd
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS ĐÁP ỨNG ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap');
    [data-testid="stSidebar"] { display: none; }
    
    /* Header sát phải trên Laptop & Mobile */
    .header-right-container {
        display: flex; justify-content: flex-end; align-items: center;
        gap: 10px; margin-top: -45px; margin-bottom: 25px; width: 100%;
    }
    .user-greet { font-size: 15px; color: #333; white-space: nowrap; }
    .stButton > button[key="logout_btn"] {
        background-color: #ff4b4b !important; color: white !important; border: none !important;
        width: 28px !important; height: 28px !important; border-radius: 4px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }

    /* Định dạng bảng cho Laptop */
    .header-text { font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 14px; }
    .row-divider { border-bottom: 1px solid #ebedef; padding: 12px 0; }
    
    /* Giao diện Card CHỈ HIỆN TRÊN MOBILE (dưới 768px) */
    @media (max-width: 768px) {
        .laptop-view { display: none !important; }
        .mobile-card {
            background: white; border: 1px solid #eee; border-radius: 10px;
            padding: 15px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    }
    @media (min-width: 769px) {
        .mobile-view { display: none !important; }
    }

    .brand-title { font-family: 'Playfair Display', serif; font-size: 32px; font-weight: 800; color: #1a1a1a; margin-bottom: 5px; text-align: center; }
    .brand-sub { font-family: 'Playfair Display', serif; font-size: 18px; color: #444; margin-bottom: 30px; text-align: center; }
    .error-msg { color: #ff4b4b; font-size: 13px; margin-top: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI & CACHE ---
@st.cache_resource
def get_client():
    creds_info = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n").strip()
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def load_data(sheet_name):
    try:
        client = get_client()
        sh = client.open("Data Vin").worksheet(sheet_name)
        data = sh.get_all_values()
        return pd.DataFrame(data[1:], columns=data[0]).applymap(lambda x: str(x).strip() if x else "")
    except: return pd.DataFrame()

# --- 3. LOGIC CHÍNH ---
if 'res_df' not in st.session_state: st.session_state['res_df'] = pd.DataFrame()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'search_error' not in st.session_state: st.session_state['search_error'] = ""

if not st.session_state['logged_in']:
    _, mid_col, _ = st.columns([1, 1.2, 1])
    with mid_col:
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-title'>Data Vinhomes Smart City</div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-sub'>Liên hệ Admin Ninh - 0912.791.925</div>", unsafe_allow_html=True)
        u = st.text_input("Tài khoản").strip()
        p = st.text_input("Mật khẩu", type="password").strip()
        if st.button("Đăng nhập"):
            users = load_data("QUAN_LY_USER")
            auth = users[(users['Username'] == u) & (users['Password'] == p)]
            if not auth.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = auth.iloc[0]['Tên nhân viên']
                st.rerun()
            else: st.error("Sai tài khoản hoặc mật khẩu!")
else:
    # Header sát phải
    st.markdown('<div class="header-right-container">', unsafe_allow_html=True)
    c_g, c_l = st.columns([9, 1])
    with c_g: st.markdown(f'<div class="user-greet" style="text-align: right; padding-top: 5px;">Xin chào <b>{st.session_state["user_name"]}!</b></div>', unsafe_allow_html=True)
    with c_l: 
        if st.button("❌", key="logout_btn"): 
            st.session_state.clear()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🔄 Làm mới dữ liệu"):
        st.cache_data.clear()
        st.rerun()

    df_main = load_data("DATA_CAN_HO")
    t1, t2 = st.tabs(["🔍 Tìm nhanh", "📊 Lọc chi tiết"])

    with t1:
        c_in, c_btn, _ = st.columns([2, 0.8, 3])
        search_ma = c_in.text_input("Mã căn", key="input_ma", label_visibility="collapsed", placeholder="Nhập mã căn...")
        if st.session_state['search_error']:
            st.markdown(f"<div class='error-msg'>⚠️ {st.session_state['search_error']}</div>", unsafe_allow_html=True)
        if c_btn.button("Tìm kiếm"):
            res = df_main[df_main['Mã đầy đủ'].str.contains(search_ma, case=False)] if search_ma else pd.DataFrame()
            if res.empty and search_ma:
                st.session_state['search_error'] = f"Mã '{search_ma}' không tồn tại."
                st.session_state['res_df'] = pd.DataFrame()
            else:
                st.session_state['search_error'] = ""
                st.session_state['res_df'] = res
            st.rerun()

    # --- HIỂN THỊ KẾT QUẢ ---
    res = st.session_state['res_df']
    if not res.empty:
        st.divider()
        
        # --- BẢN LAPTOP (DẠNG BẢNG) ---
        st.markdown('<div class="laptop-view">', unsafe_allow_html=True)
        cols = st.columns([1, 1, 0.8, 0.6, 1.4, 2.2, 0.5])
        titles = ["Mã Căn", "Chủ Nhà", "Loại hình", "DT", "SĐT", "Ghi chú", "Lưu"]
        for col, title in zip(cols, titles): col.markdown(f"<div class='header-text'>{title}</div>", unsafe_allow_html=True)
        
        for i, r in res.iterrows():
            row = st.columns([1, 1, 0.8, 0.6, 1.4, 2.2, 0.5])
            row[0].write(f"**{r['Mã đầy đủ']}**")
            row[1].write(r['Chủ nhà'])
            row[2].write(r.get('Loại hình','-'))
            row[3].write(f"{r['Diện tích']}m²")
            s_key = f"v_{r['Mã đầy đủ']}"
            if st.session_state.get(s_key): row[4].code(r['Số điện thoại'])
            elif row[4].button("👁️ Xem", key=f"lp_v_{i}"): 
                st.session_state[s_key] = True
                st.rerun()
            n_val = row[5].text_input("G", value=r.get('Ghi chú',''), key=f"lp_n_{i}", label_visibility="collapsed")
            if row[6].button("💾", key=f"lp_s_{i}"): st.toast("Đã lưu!")
            st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- BẢN MOBILE (DẠNG THẺ) ---
        st.markdown('<div class="mobile-view">', unsafe_allow_html=True)
        for i, r in res.iterrows():
            st.markdown(f"""
            <div class="mobile-card">
                <div style="color:#1a73e8; font-weight:bold; font-size:16px;">🏢 {r['Mã đầy đủ']}</div>
                <div style="font-size:14px; margin-top:5px;">
                    <b>Chủ:</b> {r['Chủ nhà']} | <b>DT:</b> {r['Diện tích']}m²<br>
                    <b>Loại:</b> {r.get('Loại hình','-')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            mc1, mc2 = st.columns(2)
            s_key = f"v_{r['Mã đầy đủ']}"
            if st.session_state.get(s_key): mc1.code(r['Số điện thoại'])
            elif mc1.button("📞 Xem SĐT", key=f"mb_v_{i}"): 
                st.session_state[s_key] = True
                st.rerun()
            n_mb = mc2.text_input("Ghi chú", value=r.get('Ghi chú',''), key=f"mb_n_{i}", label_visibility="collapsed")
            if mc2.button("💾 Lưu", key=f"mb_s_{i}"): st.toast("Lưu xong!")
            st.divider()
        st.markdown('</div>', unsafe_allow_html=True)
