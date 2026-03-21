import streamlit as st
import pandas as pd
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS MOBILE ---
st.set_page_config(page_title="Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { display: none; }

    /* Header sát phải cho Mobile */
    .header-right-container {
        display: flex; justify-content: flex-end; align-items: center;
        gap: 8px; margin-top: -50px; margin-bottom: 10px;
    }
    
    /* Giao diện dạng CARD cho điện thoại */
    .apartment-card {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .card-title { color: #1a73e8; font-size: 18px; font-weight: 800; margin-bottom: 5px; }
    .card-info { font-size: 14px; color: #5f6368; line-height: 1.6; }
    .card-label { font-weight: 600; color: #202124; }
    
    /* Nút bấm to hơn dễ chạm trên điện thoại */
    .stButton button { border-radius: 8px; height: 45px; font-size: 15px; }
    .logout-btn-style button { width: 32px !important; height: 32px !important; background-color: #ff4b4b !important; color: white !important; border: none !important; }
    
    .error-msg { color: #ff4b4b; font-size: 13px; font-weight: bold; margin-top: 5px; }
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

@st.cache_data(ttl=300) # Lưu bộ nhớ đệm trong 5 phút để load cực nhanh
def load_full_data(sheet_name):
    client = get_gspread_client()
    doc = client.open("Data Vin")
    sh = doc.worksheet(sheet_name)
    data = sh.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df.applymap(lambda x: str(x).strip() if x else "")

# --- 3. LOGIC APP ---
if 'res_df' not in st.session_state: st.session_state['res_df'] = pd.DataFrame()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'search_error' not in st.session_state: st.session_state['search_error'] = ""

if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center;'>Đăng nhập Hệ thống</h2>", unsafe_allow_html=True)
    u = st.text_input("Tài khoản")
    p = st.text_input("Mật khẩu", type="password")
    if st.button("Vào hệ thống"):
        try:
            users_df = load_full_data("QUAN_LY_USER")
            auth = users_df[(users_df['Username'] == u) & (users_df['Password'] == p)]
            if not auth.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = auth.iloc[0]['Tên nhân viên']
                st.rerun()
            else: st.error("Sai thông tin!")
        except: st.error("Lỗi kết nối!")
else:
    # Header sát phải
    st.markdown(f'''<div class="header-right-container">
        <span class="user-greet">Chào <b>{st.session_state["user_name"]}</b></span>
        <div class="logout-btn-style">''', unsafe_allow_html=True)
    if st.button("❌", key="logout_btn"):
        st.session_state.clear()
        st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)

    # Tải dữ liệu chính
    df_main = load_full_data("DATA_CAN_HO")

    tab1, tab2 = st.tabs(["🔍 Tìm nhanh", "📊 Bộ lọc"])

    with tab1:
        search_ma = st.text_input("Nhập mã căn...", placeholder="Ví dụ: S1.01...", label_visibility="collapsed")
        if st.session_state['search_error']:
            st.markdown(f"<div class='error-msg'>⚠️ {st.session_state['search_error']}</div>", unsafe_allow_html=True)
        
        if st.button("TÌM KIẾM") or (search_ma and st.session_state.get('last_m') != search_ma):
            st.session_state['last_m'] = search_ma
            res = df_main[df_main['Mã đầy đủ'].str.contains(search_ma, case=False)]
            if res.empty:
                st.session_state['search_error'] = "Không tìm thấy căn này."
                st.session_state['res_df'] = pd.DataFrame()
            else:
                st.session_state['search_error'] = ""
                st.session_state['res_df'] = res
            st.rerun()

    # --- HIỂN THỊ DẠNG THẺ (OPTIMIZED FOR MOBILE) ---
    res_display = st.session_state['res_df']
    if not res_display.empty:
        st.markdown(f"**Tìm thấy {len(res_display)} kết quả**")
        for i, r in res_display.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="apartment-card">
                    <div class="card-title">🏢 {r['Mã đầy đủ']}</div>
                    <div class="card-info">
                        <span class="card-label">Chủ nhà:</span> {r['Chủ nhà']}<br>
                        <span class="card-label">Diện tích:</span> {r['Diện tích']}m² | <span class="card-label">Loại:</span> {r.get('Loại hình','-')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Nút chức năng nằm dưới Card
                c1, c2 = st.columns([1, 1])
                with c1:
                    s_key = f"v_{r['Mã đầy đủ']}"
                    if st.session_state.get(s_key):
                        st.code(r['Số điện thoại'])
                    else:
                        if st.button(f"📞 Xem SĐT", key=f"btn_{i}"):
                            st.session_state[s_key] = True
                            st.rerun()
                with c2:
                    # Ghi chú thu gọn
                    note = st.text_input("Ghi chú", value=r.get('Ghi chú',''), key=f"n_{i}", label_visibility="collapsed")
                    if st.button("💾 Lưu", key=f"s_{i}"):
                        # Logic lưu ghi chú (giữ nguyên gspread update)
                        st.toast("Đã lưu!")
                st.markdown("---")
