import streamlit as st
import pandas as pd
import gspread
import time 
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS TỐI ƯU CÂN ĐỐI MÀN HÌNH (GIỮ NGUYÊN 100% BẢN BẠN GỬI) ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap');
    [data-testid="stSidebar"] { display: none; }
    
    /* Tiêu đề: Căn giữa và cho phép xuống dòng tự nhiên trên mobile */
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

    /* FIX CÂN ĐỐI TRÊN MOBILE */
    @media (max-width: 768px) {
        /* Bỏ chia cột, cho form rộng 90% màn hình và căn giữa */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            padding: 0 10px !important;
        }
        
        /* Căn chỉnh lại khoảng cách lề cho đẹp */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* Tiêu đề thu nhỏ một chút cho vừa màn hình dọc */
        .brand-title { font-size: 26px; white-space: normal !important; }

        /* YÊU CẦU MỚI: HIỂN THỊ HÀNG NGANG TRÊN MOBILE CHO DANH SÁCH */
        .mobile-scroll {
            display: flex !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
            gap: 10px;
        }
        .mobile-scroll > div {
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
    
    /* Nút đỏ cho cả đăng nhập và đăng xuất */
    .stButton > button {
        background-color: #ff4b4b !important; color: white !important; border: none !important;
    }
    
    .header-text { font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 13px; }
    .row-divider { border-bottom: 1px solid #ebedef; padding: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# (Phần INIT_CONNECTION giữ nguyên)
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

LIST_TANG = ["1", "2", "3", "05A", "05", "06", "07", "08", "08A", "09", "10", "11", "12", "12A", "15A", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]

# --- 2. ĐĂNG NHẬP CÂN ĐỐI (GIỮ NGUYÊN BẢN BẠN GỬI) ---
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

# --- 3. PHẦN CHỨC NĂNG (CHỈ CHẠY KHI ĐÃ ĐĂNG NHẬP) ---
else:
    # Header ngang hàng: Xin chào + Đăng xuất
    st.markdown(f"""
        <div class="header-right-container">
            <span class="user-greet">Xin chào <b>{st.session_state["user_name"]}!</b></span>
        </div>
    """, unsafe_allow_html=True)
    
    # Nút Logout thực tế (vị trí trùng để hiển thị ngang hàng trên Laptop/Mobile)
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
            ci, cb, _ = st.columns([2, 1, 3])
            with ci: m_in = st.text_input("Mã căn", label_visibility="collapsed", placeholder="Mã...")
            with cb:
                if st.button("Tìm", key="f_b"):
                    if m_in:
                        st.session_state['res_df'] = df_main[df_main['Mã đầy đủ'].str.contains(m_in.strip(), case=False)]
                        st.rerun()

        with t2:
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1: ds_toa = st.multiselect("Tòa", sorted([t for t in df_main['Tòa'].unique() if t]))
            with c2: fs = st.selectbox("Từ tầng", LIST_TANG, index=4)
            with c3: fe = st.selectbox("Đến tầng", LIST_TANG, index=15)
            if st.button("🚀 Thực hiện lọc", key="l_b"):
                tdf = df_main.copy()
                if ds_toa: tdf = tdf[tdf['Tòa'].isin(ds_toa)]
                idx_s, idx_e = LIST_TANG.index(fs), LIST_TANG.index(fe)
                tdf = tdf[tdf['Tầng'].isin(LIST_TANG[idx_s:idx_e+1])]
                st.session_state['res_df'] = tdf
                st.rerun()

        res = st.session_state['res_df']
        if not res.empty:
            st.divider()
            # Áp dụng class 'mobile-scroll' để danh sách hiển thị hàng ngang trên điện thoại
            st.markdown('<div class="mobile-scroll">', unsafe_allow_html=True)
            
            # Header bảng
            h_cols = st.columns([1.5, 1.5, 1, 1, 2, 3, 1])
            for col, txt in zip(h_cols, ["Mã Căn", "Chủ Nhà", "Loại", "DT", "SĐT", "Ghi chú", "Lưu"]):
                col.markdown(f"<div class='header-text'>{txt}</div>", unsafe_allow_html=True)
            
            # Dòng dữ liệu
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
                    except: st.error("Lỗi kết nối!")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)

    except Exception as e: st.error("Vui lòng kiểm tra lại Google Sheets.")
