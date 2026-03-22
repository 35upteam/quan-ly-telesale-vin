import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS FIX TRIỆT ĐỂ ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&display=swap');
    [data-testid="stSidebar"] { display: none; }
    
    /* FIX: Tiêu đề trang đăng nhập trên 1 dòng */
    .brand-title { 
        font-family: 'Playfair Display', serif; 
        font-size: clamp(20px, 6vw, 32px); /* Tự co giãn font để luôn vừa 1 dòng */
        font-weight: 800; color: #1a1a1a; 
        text-align: center; white-space: nowrap; 
        margin-bottom: 5px; 
    }

    /* FIX: Header Xin chào và Nút X luôn ngang hàng */
    .header-container {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 10px;
        margin-top: -50px;
        margin-bottom: 20px;
    }
    .user-greet { font-size: 14px; white-space: nowrap; }

    /* FIX: Bảng trên Mobile không được xếp chồng dọc (Ngang như Laptop) */
    @media (max-width: 768px) {
        /* Ép các cột của Streamlit không được wrap xuống dòng */
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important; /* Cho phép vuốt ngang */
            padding-bottom: 10px;
            align-items: flex-start !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            min-width: 100px !important; /* Độ rộng tối thiểu mỗi cột */
            flex-shrink: 0 !important;
        }
        /* Cột Ghi chú cần rộng hơn */
        div[data-testid="stHorizontalBlock"] > div:nth-child(6) { min-width: 200px !important; }
    }

    .header-text { font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; font-size: 13px; white-space: nowrap; }
    .row-divider { border-bottom: 1px solid #ebedef; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI ---
@st.cache_resource
def get_doc():
    creds_info = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n").strip()
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds).open("Data Vin")

@st.cache_data(ttl=600)
def load_data(sheet_name):
    try:
        sh = get_doc().worksheet(sheet_name)
        data = sh.get_all_values()
        return pd.DataFrame(data[1:], columns=data[0]).applymap(lambda x: str(x).strip() if x else "")
    except: return pd.DataFrame()

# --- 3. LOGIC ---
if 'res_df' not in st.session_state: st.session_state['res_df'] = pd.DataFrame()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-title'>Data Vinhomes Smart City</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; color: #666; margin-bottom: 20px;'>Liên hệ Admin Ninh - 0912.791.925</div>", unsafe_allow_html=True)
    
    _, mid, _ = st.columns([1, 2, 1])
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
            else: st.error("Sai tài khoản/mật khẩu")
else:
    # Header ngang hàng
    st.markdown(f'''
        <div class="header-container">
            <span class="user-greet">Xin chào <b>{st.session_state["user_name"]}!</b></span>
        </div>
    ''', unsafe_allow_html=True)
    
    # Nút thoát đặt cùng vị trí header bằng CSS absolute hoặc dùng columns
    c_out_1, c_out_2 = st.columns([9.2, 0.8])
    with c_out_2:
        if st.button("❌", key="logout_btn"):
            st.session_state.clear()
            st.rerun()

    if st.button("🔄 Làm mới dữ liệu"):
        st.cache_data.clear()
        st.rerun()

    df_main = load_data("DATA_CAN_HO")
    t1, t2 = st.tabs(["🔍 Tìm nhanh", "📊 Lọc chi tiết"])

    with t1:
        c_in, c_btn, _ = st.columns([3, 1, 1])
        ma = c_in.text_input("Mã căn", placeholder="S1.01...", label_visibility="collapsed")
        if c_btn.button("Tìm"):
            if ma:
                st.session_state['res_df'] = df_main[df_main['Mã đầy đủ'].str.contains(ma, case=False)]
                st.rerun()

    # --- HIỂN THỊ BẢNG NGANG (DÙNG CHO CẢ LAPTOP & MOBILE) ---
    res = st.session_state['res_df']
    if not res.empty:
        st.write(f"Tìm thấy {len(res)} căn")
        
        # Tiêu đề bảng
        h = st.columns([1.2, 1.2, 0.8, 0.6, 1.5, 2.5, 0.6])
        t_list = ["Mã Căn", "Chủ Nhà", "Loại", "DT", "SĐT", "Ghi chú", "Lưu"]
        for col, txt in zip(h, t_list):
            col.markdown(f"<div class='header-text'>{txt}</div>", unsafe_allow_html=True)

        for i, r in res.iterrows():
            row = st.columns([1.2, 1.2, 0.8, 0.6, 1.5, 2.5, 0.6])
            row[0].write(f"**{r['Mã đầy đủ']}**")
            row[1].write(r['Chủ nhà'])
            row[2].write(r.get('Loại hình','-'))
            row[3].write(f"{r['Diện tích']}m²")
            
            s_key = f"v_{r['Mã đầy đủ']}"
            if st.session_state.get(s_key):
                row[4].code(r['Số điện thoại'])
            else:
                if row[4].button("👁️", key=f"v_{i}"):
                    st.session_state[s_key] = True
                    st.rerun()
            
            note = row[5].text_input("N", value=r.get('Ghi chú',''), key=f"n_{i}", label_visibility="collapsed")
            if row[6].button("💾", key=f"s_{i}"):
                st.toast("Đã lưu!")
            st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)
