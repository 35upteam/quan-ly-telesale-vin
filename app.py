import streamlit as st
import pandas as pd
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS ĐÁP ỨNG (RESPONSIVE) ---
st.set_page_config(page_title="Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { display: none; }

    /* Header sát phải tuyệt đối */
    .header-right-container {
        display: flex; justify-content: flex-end; align-items: center;
        gap: 8px; margin-top: -50px; margin-bottom: 15px;
    }

    /* Hệ thống lưới (Grid) tự động chia cột */
    .main-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
        gap: 15px;
    }

    /* Thiết kế thẻ (Card) */
    .apartment-card {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .card-title { color: #1a73e8; font-size: 17px; font-weight: 700; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    .card-info { font-size: 14px; color: #444; line-height: 1.5; margin-bottom: 10px; }
    .card-label { font-weight: 600; color: #202124; width: 80px; display: inline-block; }

    /* Nút bấm */
    .stButton button { border-radius: 6px; font-weight: 600; }
    .logout-btn-style button { width: 30px !important; height: 30px !important; background-color: #ff4b4b !important; color: white !important; border: none !important; }
    .error-msg { color: #ff4b4b; font-size: 13px; font-weight: bold; margin-top: 5px; }
    
    /* Ẩn bớt padding thừa của Streamlit trên mobile */
    @media (max-width: 640px) {
        .main-grid { grid-template-columns: 1fr; }
        .stApp { padding: 0px; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. TỐI ƯU TỐC ĐỘ: CACHING ---
@st.cache_resource
def get_gspread_client():
    creds_info = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n").strip()
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_full_data(sheet_name):
    try:
        client = get_gspread_client()
        doc = client.open("Data Vin")
        sh = doc.worksheet(sheet_name)
        data = sh.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df.applymap(lambda x: str(x).strip() if x else "")
    except:
        return pd.DataFrame()

# --- 3. LOGIC APP ---
if 'res_df' not in st.session_state: st.session_state['res_df'] = pd.DataFrame()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'search_error' not in st.session_state: st.session_state['search_error'] = ""

if not st.session_state['logged_in']:
    _, mid, _ = st.columns([1, 1.5, 1])
    with mid:
        st.markdown("<h2 style='text-align: center;'>Hệ thống Giỏ hàng</h2>", unsafe_allow_html=True)
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập"):
            users_df = load_full_data("QUAN_LY_USER")
            auth = users_df[(users_df['Username'] == u) & (users_df['Password'] == p)]
            if not auth.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = auth.iloc[0]['Tên nhân viên']
                st.rerun()
            else: st.error("Sai tài khoản/mật khẩu")
else:
    # Header sát phải
    st.markdown(f'''<div class="header-right-container">
        <span class="user-greet">Chào <b>{st.session_state["user_name"]}</b></span>
        <div class="logout-btn-style">''', unsafe_allow_html=True)
    if st.button("❌", key="logout_btn"):
        st.session_state.clear()
        st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)

    # Nút làm mới dữ liệu nhanh
    if st.button("🔄 Làm mới dữ liệu", help="Cập nhật lại từ Google Sheets ngay lập tức"):
        st.cache_data.clear()
        st.rerun()

    df_main = load_full_data("DATA_CAN_HO")

    t1, t2 = st.tabs(["🔍 Tìm nhanh", "📊 Lọc chi tiết"])
    
    with t1:
        c_in, c_btn = st.columns([3, 1])
        search_ma = c_in.text_input("Mã căn", placeholder="S1.01.10.20", label_visibility="collapsed")
        if c_btn.button("TÌM KIẾM"):
            if search_ma:
                res = df_main[df_main['Mã đầy đủ'].str.contains(search_ma, case=False)]
                if res.empty:
                    st.session_state['search_error'] = f"Không thấy mã: {search_ma}"
                    st.session_state['res_df'] = pd.DataFrame()
                else:
                    st.session_state['search_error'] = ""
                    st.session_state['res_df'] = res
                st.rerun()
        if st.session_state['search_error']:
            st.markdown(f"<div class='error-msg'>⚠️ {st.session_state['search_error']}</div>", unsafe_allow_html=True)

    # --- HIỂN THỊ ĐÁP ỨNG (GRID CARD) ---
    res_display = st.session_state['res_df']
    if not res_display.empty:
        st.write(f"Tìm thấy **{len(res_display)}** căn")
        
        # Bắt đầu container Grid
        st.markdown('<div class="main-grid">', unsafe_allow_html=True)
        
        # Vì Streamlit không cho lồng button vào HTML trực tiếp dễ dàng, 
        # ta dùng layout columns bên trong Grid của Streamlit
        for i, r in res_display.iterrows():
            with st.container():
                # Vẽ Card bằng HTML
                st.markdown(f"""
                <div class="apartment-card">
                    <div class="card-title">🏢 {r['Mã đầy đủ']}</div>
                    <div class="card-info">
                        <span class="card-label">Chủ nhà:</span> {r['Chủ nhà']}<br>
                        <span class="card-label">Diện tích:</span> {r['Diện tích']}m²<br>
                        <span class="card-label">Loại:</span> {r.get('Loại hình','-')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Nút chức năng (SĐT và Ghi chú)
                c1, c2 = st.columns([1, 1])
                s_key = f"v_{r['Mã đầy đủ']}"
                if st.session_state.get(s_key):
                    c1.code(r['Số điện thoại'])
                else:
                    if c1.button(f"📞 Xem SĐT", key=f"b_{i}"):
                        st.session_state[s_key] = True
                        st.rerun()
                
                # Ghi chú & Lưu
                note = c2.text_input("Note", value=r.get('Ghi chú',''), key=f"n_{i}", label_visibility="collapsed")
                if c2.button("💾 Lưu", key=f"s_{i}"):
                    # Logic lưu vào Google Sheets ở đây
                    st.toast("Đã lưu ghi chú!")
        
        st.markdown('</div>', unsafe_allow_html=True)
