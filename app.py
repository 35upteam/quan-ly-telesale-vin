import streamlit as st
import pandas as pd
import gspread
import time 
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS FIX TRANG ĐĂNG NHẬP ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap');
    [data-testid="stSidebar"] { display: none; }
    
    /* FIX: Tiêu đề đăng nhập luôn 1 dòng và co giãn theo màn hình */
    .brand-title { 
        font-family: 'Playfair Display', serif; 
        font-size: clamp(22px, 7vw, 32px); 
        font-weight: 800; color: #1a1a1a; 
        margin-bottom: 5px; text-align: center; 
        white-space: nowrap; 
    }
    .brand-sub { font-family: 'Playfair Display', serif; font-size: 16px; color: #444; margin-bottom: 30px; text-align: center; }

    /* FIX: Tối ưu khung đăng nhập trên Mobile */
    @media (max-width: 768px) {
        /* Ép các cột căn giữa giãn ra 100% trên điện thoại */
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
        /* Cho phép cuộn ngang bảng kết quả */
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

    /* FIX: Header Xin chào và Nút X luôn ngang hàng sát phải */
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

# --- GIỮ NGUYÊN TOÀN BỘ PHẦN KẾT NỐI VÀ LOGIC BÊN DƯỚI ---
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
if 'search_error' not in st.session_state: st.session_state['search_error'] = ""

# --- 2. ĐĂNG NHẬP ---
if not st.session_state['logged_in']:
    # Trên Laptop sẽ là 1-1.2-1, trên Mobile CSS trên sẽ ép thành 100%
    _, mid_col, _ = st.columns([1, 1.2, 1])
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
                except Exception as e:
                    if attempt < 2:
                        time.sleep(1)
                        continue
            if success: st.rerun()
else:
    # --- HEADER & DATA (GIỮ NGUYÊN NHƯ BẢN BẠN GỬI) ---
    st.markdown('<div class="header-right-container">', unsafe_allow_html=True)
    c_greet, c_logout = st.columns([9, 1]) 
    with c_greet:
        st.markdown(f'<div class="user-greet" style="text-align: right; padding-top: 5px;">Xin chào <b>{st.session_state["user_name"]}!</b></div>', unsafe_allow_html=True)
    with c_logout:
        if st.button("❌", key="logout_btn"):
            st.session_state.clear()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_vals = sh_data.get_all_values()
        h_names = raw_vals[0]
        df_main = pd.DataFrame(raw_vals[1:], columns=h_names)
        df_main = df_main.applymap(lambda x: str(x).strip() if x is not None else "")

        tab_ma, tab_tieuchi = st.tabs(["🔍 Tìm nhanh", "📊 Lọc chi tiết"])

        with tab_ma:
            c_in, c_btn, _ = st.columns([2, 0.8, 3])
            with c_in:
                search_ma = st.text_input("Mã căn", key="input_ma", label_visibility="collapsed", placeholder="Nhập mã căn...")
                if st.session_state['search_error']:
                    st.markdown(f"<div class='error-msg'>⚠️ {st.session_state['search_error']}</div>", unsafe_allow_html=True)
            with c_btn:
                if st.button("Tìm kiếm", key="btn_find_ma"):
                    if search_ma:
                        res = df_main[df_main['Mã đầy đủ'].str.contains(search_ma.strip(), case=False)]
                        if res.empty:
                            st.session_state['search_error'] = f"Không tìm thấy mã này."
                            st.session_state['res_df'] = pd.DataFrame()
                        else:
                            st.session_state['search_error'] = ""
                            st.session_state['res_df'] = res
                        st.rerun()

        with tab_tieuchi:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            with c1: 
                ds_toa = sorted([t for t in df_main['Tòa'].unique() if t])
                sel_t = st.multiselect("Tòa", ds_toa)
            with c2: f_s = st.selectbox("Từ tầng", LIST_TANG_PHYSICAL, index=4)
            with c3: f_e = st.selectbox("Đến tầng", LIST_TANG_PHYSICAL, index=15)
            with c4: sel_tr = st.multiselect("Trục", LIST_TRUC)
            
            if st.button("🚀 Thực hiện lọc", key="btn_filter"):
                st.session_state['search_error'] = ""
                t_df = df_main.copy()
                if sel_t: t_df = t_df[t_df['Tòa'].isin(sel_t)]
                if sel_tr:
                    t_df['Trục_Clean'] = t_df['Trục'].apply(lambda x: x.replace(".0", "").zfill(2) if x else "")
                    t_df = t_df[t_df['Trục_Clean'].isin(sel_tr)]
                idx_s, idx_e = LIST_TANG_PHYSICAL.index(f_s), LIST_TANG_PHYSICAL.index(f_e)
                allowed = LIST_TANG_PHYSICAL[idx_s : idx_e + 1]
                t_df = t_df[t_df['Tầng'].isin(allowed)]
                st.session_state['res_df'] = t_df
                st.rerun()

        res_display = st.session_state['res_df']
        if not res_display.empty:
            st.divider()
            cols_ui = st.columns([1.2, 1.2, 0.8, 0.6, 1.5, 2.5, 0.5])
            titles = ["Mã Căn", "Chủ Nhà", "Loại", "DT", "SĐT", "Ghi chú", "Lưu"]
            for ui, txt in zip(cols_ui, titles): ui.markdown(f"<div class='header-text'>{txt}</div>", unsafe_allow_html=True)
            for i, r in res_display.iterrows():
                row = st.columns([1.2, 1.2, 0.8, 0.6, 1.5, 2.5, 0.5])
                row[0].write(f"**{r['Mã đầy đủ']}**")
                row[1].write(r['Chủ nhà'])
                row[2].write(r.get('Loại hình', '-'))
                row[3].write(f"{r['Diện tích']}m²")
                s_key = f"v_{r['Mã đầy đủ']}"
                if s_key in st.session_state and st.session_state[s_key]:
                    row[4].code(r['Số điện thoại'], language="text")
                else:
                    if row[4].button(f"👁️", key=f"btn_{i}"):
                        st.session_state[s_key] = True
                        st.rerun()
                n_val = row[5].text_input("G", value=r.get('Ghi chú', ''), key=f"in_{i}", label_visibility="collapsed")
                if row[6].button("💾", key=f"sv_{i}"):
                    try:
                        cell = sh_data.find(r['Mã đầy đủ'])
                        g_col = h_names.index('Ghi chú') + 1
                        sh_data.update_cell(cell.row, g_col, n_val)
                        st.toast(f"Đã lưu!", icon="✅")
                    except: st.error("Lỗi!")
                st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)
    except Exception as e: st.error(f"Lỗi: {e}")
