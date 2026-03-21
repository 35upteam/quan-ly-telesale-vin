import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Telesale", layout="wide")

# --- 1. KẾT NỐI HỆ THỐNG (DÙNG SECRETS TRÊN CLOUD) ---
@st.cache_resource # Lưu bộ nhớ tạm kết nối để web chạy nhanh hơn
def init_connection():
    try:
        # Lấy dữ liệu từ Secrets và tạo một bản sao (dict) để có thể chỉnh sửa
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # Tự động xử lý lỗi ký tự xuống dòng trong Private Key
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Sử dụng bản sao đã sửa để kết nối
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        
        # Mở file Google Sheets "Data Vin"
        return client.open("Data Vin")
    except Exception as e:
        st.error(f"Lỗi kết nối Secrets: {e}")
        st.info("Kiểm tra lại mục Settings -> Secrets trên Streamlit Cloud xem bạn đã dán đúng định dạng TOML chưa.")
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
@st.cache_data(ttl=600) # Lưu bộ nhớ tạm 10 phút để web chạy nhanh
def get_data(worksheet):
    return pd.DataFrame(worksheet.get_all_records())

# --- 3. LOGIC ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập Hệ thống Telesale")
    user_input = st.text_input("Tên đăng nhập")
    pass_input = st.text_input("Mật khẩu", type="password")
    
    if st.button("Đăng nhập"):
        users_df = get_data(sh_user)
        # Kiểm tra tài khoản trong sheet QUAN_LY_USER
        user_auth = users_df[(users_df['Username'] == user_input) & (users_df['Password'].astype(str) == pass_input)]
        
        if not user_auth.empty:
            st.session_state['logged_in'] = True
            st.session_state['user_name'] = user_input
            st.rerun()
        else:
            st.error("Sai tài khoản hoặc mật khẩu!")
else:
    # --- 4. GIAO DIỆN CHÍNH (SAU KHI ĐĂNG NHẬP) ---
    st.sidebar.success(f"Chào mừng: {st.session_state['user_name']}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("🏘️ Tra cứu Căn hộ & Bảo mật SĐT")

    # Đọc dữ liệu căn hộ
    df = get_data(sh_data)
    # Ép kiểu dữ liệu để lọc chuẩn
    df['Tầng'] = pd.to_numeric(df['Tầng'], errors='coerce')
    df['Trục'] = df['Trục'].astype(str)

    # BỘ LỌC TẠI SIDEBAR
    st.sidebar.header("🔍 Bộ lọc thông minh")
    
    list_toa = ["Tất cả"] + sorted(list(df['Tòa'].unique()))
    selected_toa = st.sidebar.selectbox("Chọn Tòa nhà", list_toa)
    
    list_truc = sorted(list(df['Trục'].unique()))
    selected_truc = st.sidebar.multiselect("Chọn Trục căn", list_truc)
    
    min_f = int(df['Tầng'].min())
    max_f = int(df['Tầng'].max())
    floor_range = st.sidebar.slider("Khoảng tầng", min_f, max_f, (min_f, max_f))

    # XỬ LÝ LỌC
    filtered_df = df.copy()
    if selected_toa != "Tất cả":
        filtered_df = filtered_df[filtered_df['Tòa'] == selected_toa]
    if selected_truc:
        filtered_df = filtered_df[filtered_df['Trục'].isin(selected_truc)]
    filtered_df = filtered_df[filtered_df['Tầng'].between(floor_range[0], floor_range[1])]

    st.write(f"Tìm thấy **{len(filtered_df)}** căn hộ phù hợp.")

    # HIỂN THỊ KẾT QUẢ
    for index, row in filtered_df.iterrows():
        # Tạo khung bao quanh mỗi căn hộ
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(f"📍 {row['Mã đầy đủ']}")
                st.write(f"**Loại:** {row['Loại hình']} | **Diện tích:** {row['Diện tích']}m²")
                st.write(f"**Chủ nhà:** {row['Chủ nhà']}")
                
                # Hiển thị SĐT đã che
                phone_raw = str(row['Số điện thoại'])
                phone_hidden = phone_raw[:4] + ".xxx.xxx"
                st.markdown(f"📞 **SĐT:** `{phone_hidden}`")
                
            with col2:
                # Nút bấm hiện số đầy đủ
                if st.button(f"Hiện số căn {row['Mã đầy đủ']}", key=f"btn_{row['Mã đầy đủ']}"):
                    st.success(f"SĐT: {phone_raw}")
                    
                    # Ghi Log vào Google Sheets
                    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    try:
                        sh_log.append_row([now, st.session_state['user_name'], row['Mã đầy đủ'], "Xem SĐT"])
                        st.toast("Đã ghi nhận lịch sử!")
                    except:
                        pass
            st.divider()
