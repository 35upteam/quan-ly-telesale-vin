import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Telesale Vin", layout="wide")

# CSS để làm đẹp bảng và nút bấm
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 5px; height: 2em; }
    .main-table { font-size: 14px; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
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
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        st.stop()

doc = init_connection()

# Quản lý trạng thái hiển thị SĐT
if 'show_phone' not in st.session_state:
    st.session_state['show_phone'] = {}
if 'search_results' not in st.session_state:
    st.session_state['search_results'] = pd.DataFrame()
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = None

# --- ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập")
    u = st.text_input("Tên đăng nhập")
    p = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
        sh_user = doc.worksheet("QUAN_LY_USER")
        data_u = sh_user.get_all_values()
        u_df = pd.DataFrame(data_u[1:], columns=data_u[0])
        auth = u_df[(u_df['Username'] == u) & (u_df['Password'].astype(str) == p)]
        if not auth.empty:
            st.session_state['logged_in'] = True
            st.session_state['user_name'] = u
            st.rerun()
        else:
            st.error("Sai thông tin!")
else:
    st.sidebar.subheader(f"👤 {st.session_state['user_name']}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.clear()
        st.rerun()

    st.title("🏘️ Tra cứu Căn hộ")

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_data = sh_data.get_all_values()
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        df['Tầng'] = pd.to_numeric(df['Tầng'], errors='coerce').fillna(0)

        # BỘ LỌC
        tab1, tab2 = st.tabs(["🔍 Tìm theo Mã căn", "📂 Lọc nâng cao"])
        
        with tab1:
            m_input = st.text_input("Nhập mã căn cụ thể").strip()
            if st.button("🔍 Tìm kiếm"):
                st.session_state['search_results'] = df[df['Mã đầy đủ'].str.contains(m_input, case=False, na=False)]
                st.session_state['view_mode'] = 'single'

        with tab2:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                t_list = ["Tất cả"] + sorted(list(df['Tòa'].unique()))
                s_toa = st.selectbox("Chọn Tòa", t_list)
            with c2:
                f_f = st.number_input("Tầng từ", value=1, step=1)
            with c3:
                f_t = st.number_input("Đến tầng", value=50, step=1)
            with c4:
                tr_list = sorted(list(df['Trục'].unique()))
                s_truc = st.multiselect("Chọn Trục", tr_list)
            
            if st.button("🚀 Bắt đầu lọc"):
                t_df = df.copy()
                if s_toa != "Tất cả": t_df = t_df[t_df['Tòa'] == s_toa]
                if s_truc: t_df = t_df[t_df['Trục'].isin(s_truc)]
                t_df = t_df[t_df['Tầng'].between(f_f, f_t)]
                st.session_state['search_results'] = t_df
                st.session_state['view_mode'] = 'table'

        # HIỂN THỊ
        st.divider()
        res = st.session_state['search_results']

        if not res.empty:
            if st.session_state['view_mode'] == 'single':
                # Giao diện cho 1 mã căn (giữ nguyên hoặc tùy biến thêm)
                for i, r in res.iterrows():
                    with st.container(border=True):
                        st.subheader(f"🏠 {r['Mã đầy đủ']}")
                        st.write(f"Chủ nhà: {r['Chủ nhà']} | Loại: {r['Loại hình']} | Diện tích: {r['Diện tích']}m2")
                        st.write(f"Trạng thái: **{r['Trạng thái']}**")
                        # Nút hiện số
                        if st.button(f"👁️ Hiện SĐT {r['Mã đầy đủ']}", key=f"s_{r['Mã đầy đủ']}"):
                            st.code(r['Số điện thoại'], language="text") # Hiện dạng code để dễ copy

            else:
                # GIAO DIỆN BẢNG NGANG (LOẠI BỎ TÒA, TẦNG, TRỤC)
                # Tiêu đề bảng
                h = st.columns([1.5, 1.5, 1.5, 1, 1, 1.2])
                cols_name = ["Mã Căn", "Chủ Nhà", "SĐT", "Loại", "D.Tích", "Trạng Thái"]
                for col, name in zip(h, cols_name):
                    col.markdown(f"**{name}**")
                
                for i, r in res.iterrows():
                    c = st.columns([1.5, 1.5, 1.5, 1, 1, 1.2])
                    c[0].write(r['Mã đầy đủ'])
                    c[1].write(r['Chủ nhà'])
                    
                    # Cột SĐT với Icon Mắt và Copy
                    sdt_key = f"show_{r['Mã đầy đủ']}"
                    if sdt_key in st.session_state and st.session_state[sdt_key]:
                        # Hiện số và nút copy
                        c[2].code(r['Số điện thoại'], language="text")
                    else:
                        # Hiện nút Mắt để mở
                        if c[2].button(f"👁️ {str(r['Số điện thoại'])[:4]}...", key=f"eye_{r['Mã đầy đủ']}"):
                            st.session_state[sdt_key] = True
                            # Ghi log
                            doc.worksheet("LOG_TRUY_CAP").append_row([datetime.now().strftime("%H:%M %d/%m"), st.session_state['user_name'], r['Mã đầy đủ']])
                            st.rerun()
                    
                    c[3].write(r['Loại hình'])
                    c[4].write(f"{r['Diện tích']}m2")
                    # Định dạng màu sắc cho trạng thái
                    tt = r['Trạng thái']
                    color = "green" if "Trống" in tt else "red" if "Đã bán" in tt else "orange"
                    c[5].markdown(f":{color}[{tt}]")
        
        elif st.session_state['view_mode'] is not None:
            st.warning("Không tìm thấy kết quả.")

    except Exception as e:
        st.error(f"Lỗi: {e}")
