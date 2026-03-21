import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. CẤU HÌNH KẾT NỐI (KHỚP VỚI CÁC BƯỚC TRƯỚC) ---
def init_connection():
    filename = "key_nha_dat.json"
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(filename, scope)
    client = gspread.authorize(creds)
    return client.open("Data Vin")

try:
    doc = init_connection()
    sh_data = doc.worksheet("DATA_CAN_HO")
    sh_user = doc.worksheet("QUAN_LY_USER")
    sh_log = doc.worksheet("LOG_TRUY_CAP")
except Exception as e:
    st.error(f"Lỗi kết nối: {e}")
    st.stop()

# --- 2. HÀM BỔ TRỢ ---
def get_all_data(worksheet):
    return pd.DataFrame(worksheet.get_all_records())

# --- 3. GIAO DIỆN ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập Hệ thống Telesale")
    user_input = st.text_input("Tên đăng nhập")
    pass_input = st.text_input("Mật khẩu", type="password")
    
    if st.button("Đăng nhập"):
        users_df = get_all_data(sh_user)
        # Kiểm tra user và pass trong sheet QUAN_LY_USER
        user_auth = users_df[(users_df['Username'] == user_input) & (users_df['Password'].astype(str) == pass_input)]
        
        if not user_auth.empty:
            st.session_state['logged_in'] = True
            st.session_state['user_name'] = user_input
            st.rerun()
        else:
            st.error("Sai tên đăng nhập hoặc mật khẩu!")
else:
    # --- 4. GIAO DIỆN CHÍNH SAU KHI ĐĂNG NHẬP ---
    st.sidebar.write(f"Chào, **{st.session_state['user_name']}**")
    if st.sidebar.button("Đăng xuất"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("🏘️ Tra cứu Căn hộ & Bảo mật SĐT")

    # Load dữ liệu căn hộ
    df = get_all_data(sh_data)
    df['Tầng'] = pd.to_numeric(df['Tầng'], errors='coerce')

    # BỘ LỌC SIDEBAR
    st.sidebar.header("🔍 Bộ lọc")
    list_toa = ["Tất cả"] + list(df['Tòa'].unique())
    selected_toa = st.sidebar.selectbox("Chọn Tòa", list_toa)
    
    selected_truc = st.sidebar.multiselect("Chọn Trục căn", options=sorted(df['Trục'].unique()))
    
    min_f, max_f = int(df['Tầng'].min()), int(df['Tầng'].max())
    floor_range = st.sidebar.slider("Khoảng tầng", min_f, max_f, (min_f, max_f))

    # Xử lý lọc
    filtered_df = df.copy()
    if selected_toa != "Tất cả":
        filtered_df = filtered_df[filtered_df['Tòa'] == selected_toa]
    if selected_truc:
        filtered_df = filtered_df[filtered_df['Trục'].isin(selected_truc)]
    filtered_df = filtered_df[filtered_df['Tầng'].between(floor_range[0], floor_range[1])]

    st.write(f"Tìm thấy **{len(filtered_df)}** căn hộ.")

    # HIỂN THỊ DANH SÁCH
    for index, row in filtered_df.iterrows():
        with st.expander(f"📍 Căn: {row['Mã đầy đủ']} - {row['Loại hình']} ({row['Diện tích']}m2)"):
            col1, col2 = st.columns([3, 2])
            with col1:
                st.write(f"**Chủ nhà:** {row['Chủ nhà']}")
                st.write(f"**Trạng thái:** {row['Trạng thái']}")
                # Che số điện thoại
                phone_hidden = str(row['Số điện thoại'])[:4] + ".xxx.xxx"
                st.subheader(f"📞 {phone_hidden}")
            
            with col2:
                if st.button(f"Hiện số đầy đủ", key=f"btn_{row['Mã đầy đủ']}"):
                    # Hiển thị số thật
                    st.info(f"SĐT: {row['Số điện thoại']}")
                    
                    # Ghi Log vào Trang tính
                    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    sh_log.append_row([now, st.session_state['user_name'], row['Mã đầy đủ'], "Xem SĐT"])
                    st.toast("Đã ghi nhận lượt truy cập!")