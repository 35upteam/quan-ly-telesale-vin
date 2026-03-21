import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Telesale", layout="wide")

# --- 1. KẾT NỐI HỆ THỐNG (XỬ LÝ TRIỆT ĐỂ LỖI PADDING) ---
@st.cache_resource
def init_connection():
    try:
        # Lấy bản sao của Secrets để chỉnh sửa (tránh lỗi read-only)
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # Tự động sửa lỗi Incorrect Padding và xuống dòng
        if "private_key" in creds_info:
            # Sửa các ký tự xuống dòng bị lỗi khi dán vào TOML
            cleaned_key = creds_info["private_key"].replace("\\n", "\n")
            creds_info["private_key"] = cleaned_key
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        
        # Mở file Google Sheets "Data Vin"
        return client.open("Data Vin")
    except Exception as e:
        st.error(f"Lỗi kết nối hệ thống: {e}")
        st.stop()
        return None

# Khởi tạo các Sheet
doc = init_connection()
if doc:
    sh_data = doc.worksheet("DATA_CAN_HO")
    sh_user = doc.worksheet("QUAN_LY_USER")
    sh_log = doc.worksheet("LOG_TRUY_CAP")
else:
    st.stop()

# --- 2. HÀM ĐỌC DỮ LIỆU ---
@st.cache_data(ttl=300) # Cập nhật dữ liệu mới mỗi 5 phút
def get_data(worksheet):
    return pd.DataFrame(worksheet.get_all_records())

# --- 3. LOGIC ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập Hệ thống Telesale")
    u = st.text_input("Tên đăng nhập")
    p = st.text_input("Mật khẩu", type="password")
    
    if st.button("Đăng nhập"):
        users_df = get_data(sh_user)
        # Kiểm tra Username và Password
        auth = users_df[(users_df['Username'] == u) & (users_df['Password'].astype(str) == p)]
        
        if not auth.empty:
            st.session_state['logged_in'] = True
            st.session_state['user_name'] = u
            st.rerun()
        else:
            st.error("Sai tài khoản hoặc mật khẩu!")
else:
    # --- 4. GIAO DIỆN CHÍNH ---
    st.sidebar.success(f"Người dùng: {st.session_state['user_name']}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("🏘️ Tra cứu Căn hộ & Bảo mật SĐT")

    # Đọc dữ liệu căn hộ
    df = get_data(sh_data)
    df['Tầng'] = pd.to_numeric(df['Tầng'], errors='coerce')
    df['Trục'] = df['Trục'].astype(str)

    # BỘ LỌC TẠI SIDEBAR
    st.sidebar.header("🔍 Bộ lọc")
    t_list = ["Tất cả"] + sorted(list(df['Tòa'].unique()))
    sel_toa = st.sidebar.selectbox("Chọn Tòa", t_list)
    
    tr_list = sorted(list(df['Trục'].unique()))
    sel_truc = st.sidebar.multiselect("Chọn Trục", tr_list)
    
    f_min, f_max = int(df['Tầng'].min()), int(df['Tầng'].max())
    f_range = st.sidebar.slider("Khoảng tầng", f_min, f_max, (f_min, f_max))

    # LỌC DỮ LIỆU
    f_df = df.copy()
    if sel_toa != "Tất cả":
        f_df = f_df[f_df['Tòa'] == sel_toa]
    if sel_truc:
        f_df = f_df[f_df['Trục'].isin(sel_truc)]
    f_df = f_df[f_df['Tầng'].between(f_range[0], f_range[1])]

    st.write(f"Tìm thấy **{len(f_df)}** kết quả.")

    # HIỂN THỊ DANH SÁCH
    for i, r in f_df.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.subheader(f"📍 Mã: {r['Mã đầy đủ']}")
                st.write(f"**Loại:** {r['Loại hình']} | **Diện tích:** {r['Diện tích']}m²")
                st.markdown(f"📞 **SĐT:** `{str(r['Số điện thoại'])[:4]}.xxx.xxx`")
            with c2:
                if st.button(f"Hiện số", key=f"btn_{r['Mã đầy đủ']}"):
                    st.success(f"SĐT: {r['Số điện thoại']}")
                    # Ghi Log
                    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    sh_log.append_row([now, st.session_state['user_name'], r['Mã đầy đủ'], "Xem SĐT"])
                    st.toast("Đã ghi log!")
