import streamlit as st
import pandas as pd
import gspread
import time 
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS (GIỮ NGUYÊN 100% BẢN GỐC CỦA BẠN) ---
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

        /* FIX HIỂN THỊ BẢNG NGANG TRÊN ĐIỆN THOẠI */
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            min-width: 130px !important;
            flex-shrink: 0 !important;
        }
    }

    /* Header sau khi đăng nhập */
    .header-right-container {
        display: flex; justify-content: flex-end; align-items: center;
        gap: 8px; margin-top: -45px; margin-bottom: 25px; width: 100%;
    }
    .user-greet { font-size: 14px; color: #333; white-space: nowrap; }
    
    /* NÚT ĐỎ ĐĂNG NHẬP & ĐĂNG XUẤT (GIỮ MÀU ĐỎ) */
    .stButton > button {
        background-color: #ff4b4b !important; color: white !important; border: none !important;
    }
    .header-text { font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 13px; }
    .row-divider { border-bottom: 1px solid #ebedef; padding: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

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
if 'res_df' not in st.session_state: st.session_state['res_df'] = pd.DataFrame()

LIST_TANG_PHYSICAL = ["1", "2", "3", "05A", "05", "06", "07", "08", "08A", "09", "10", "11", "12", "12A", "15A", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]
LIST_TRUC = [f"{i:02d}" for i in range(1, 31)]

# --- 2. ĐĂNG NHẬP (GIỮ NGUYÊN 100% - NÚT ĐỎ) ---
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

# --- 3. CHỨC NĂNG SAU ĐĂNG NHẬP ---
else:
    # Header: Đưa Xin chào và Nút Đăng xuất lên ngang hàng (Flexbox)
    st.markdown(f"""
        <div class="header-right-container">
            <span class="user-greet">Xin chào <b>{st.session_state["user_name"]}!</b></span>
        </div>
    """, unsafe_allow_html=True)
    
    # Dùng columns để nút bấm Streamlit hiển thị được logic logout
    _, c_logout = st.columns([8.5, 1.5])
    with c_logout:
        if st.button("Đăng xuất", key="logout_btn"):
            st.session_state.clear()
            st.rerun()

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw = sh_data.get_all_values()
        h_names = raw[0]
        df_main = pd.DataFrame(raw[1:], columns=h_names).applymap(lambda x: str(x).strip() if x else "")

        t1, t2 = st.tabs(["🔍 Tìm nhanh", "📊 Lọc chi tiết"])
        with t1:
            ci, cb, _ = st.columns([2, 0.8, 3])
            with ci: m = st.text_input("Mã căn", label_visibility="collapsed", placeholder="Mã...")
            with cb:
                if st.button("Tìm", key="f_b"):
                    if m:
                        st.session_state['res_df'] = df_main[df_main['Mã đầy đủ'].str.contains(m.strip(), case=False)]
                        st.rerun()
        with t2:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            with c1: st_toa = st.multiselect("Tòa", sorted([t for t in df_main['Tòa'].unique() if t]))
            with c2: fs = st.selectbox("Từ", LIST_TANG_PHYSICAL, index=4)
            with c3: fe = st.selectbox("Đến", LIST_TANG_PHYSICAL, index=15)
            with c4: str_tr = st.multiselect("Trục", LIST_TRUC)
            if st.button("🚀 Lọc", key="l_b"):
                tdf = df_main.copy()
                if st_toa: tdf = tdf[tdf['Tòa'].isin(st_toa)]
                if str_tr:
                    tdf['Trục_C'] = tdf['Trục'].apply(lambda x: x.replace(".0", "").zfill(2) if x else "")
                    tdf = tdf[tdf['Trục_C'].isin(str_tr)]
                idx_s, idx_e = LIST_TANG_PHYSICAL.index(fs), LIST_TANG_PHYSICAL.index(fe)
                tdf = tdf[tdf['Tầng'].isin(LIST_TANG_PHYSICAL[idx_s:idx_e+1])]
                st.session_state['res_df'] = tdf
                st.rerun()

        res = st.session_state['res_df']
        if not res.empty:
            st.divider()
            # Toàn bộ phần này sẽ tự động cuộn ngang trên điện thoại nhờ CSS ở trên
            h_cols = st.columns([1.5, 1.5, 1, 1, 2, 3, 1])
            titles = ["Mã Căn", "Chủ Nhà", "Loại", "DT", "SĐT", "Ghi chú", "Lưu"]
            for col, title in zip(h_cols, titles):
                col.markdown(f"<div class='header-text'>{title}</div>", unsafe_allow_html=True)
            
            for i, r in res.iterrows():
                row = st.columns([1.5, 1.5, 1, 1, 2, 3, 1])
                row[0].write(f"**{r['Mã đầy đủ']}**")
                row[1].write(r['Chủ nhà'])
                row[2].write(r.get('Loại hình', '-'))
                row[3].write(f"{r['Diện tích']}m²")
                sk = f"v_{r['Mã đầy đủ']}"
                if st.session_state.get(sk): row[4].code(r['Số điện thoại'], language="text")
                elif row[4].button("👁️", key=f"b_{i}"):
                    st.session_state[sk] = True
                    st.rerun()
                gv = row[5].text_input("G", value=r.get('Ghi chú', ''), key=f"i_{i}", label_visibility="collapsed")
                if row[6].button("💾", key=f"s_{i}"):
                    try:
                        cell = sh_data.find(r['Mã đầy đủ'])
                        sh_data.update_cell(cell.row, h_names.index('Ghi chú') + 1, gv)
                        st.toast("Đã lưu!")
                    except: st.error("Lỗi!")
                st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)
    except Exception as e: st.error(f"Lỗi: {e}")
