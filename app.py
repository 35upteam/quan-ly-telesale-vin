import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Quản lý Telesale Vin", layout="wide")

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

# --- ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập Hệ thống")
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
            st.error("Sai tài khoản hoặc mật khẩu!")
else:
    # --- GIAO DIỆN CHÍNH ---
    st.sidebar.subheader(f"👤 {st.session_state['user_name']}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("🏘️ Tra cứu Căn hộ")

    try:
        # 1. Đọc dữ liệu an toàn
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_data = sh_data.get_all_values()
        header = raw_data[0]
        df = pd.DataFrame(raw_data[1:], columns=header)
        df = df.loc[:, df.columns != ''] # Xóa cột trống
        
        # Ép kiểu dữ liệu số để lọc tầng
        df['Tầng'] = pd.to_numeric(df['Tầng'], errors='coerce').fillna(0)

        # 2. KHU VỰC BỘ LỌC
        tab1, tab2 = st.tabs(["🔍 Tìm theo Mã căn", "filters Tìm nâng cao"])
        
        filtered_df = pd.DataFrame() # Mặc định trống

        with tab1:
            ma_can_input = st.text_input("Nhập mã căn cụ thể (Ví dụ: S1.02-15-05)", "").strip()
            btn_tim_ma = st.button("Tìm theo mã")
            if btn_tim_ma and ma_can_input:
                filtered_df = df[df['Mã đầy đủ'].str.contains(ma_can_input, case=False, na=False)]

        with tab2:
            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            with col_t1:
                toa_list = ["Tất cả"] + sorted(list(df['Tòa'].unique()))
                sel_toa = st.selectbox("Chọn Tòa", toa_list)
            with col_t2:
                f_from = st.number_input("Tầng từ", value=int(df['Tầng'].min()), step=1)
            with col_t3:
                f_to = st.number_input("Đến tầng", value=int(df['Tầng'].max()), step=1)
            with col_t4:
                truc_list = sorted(list(df['Trục'].unique()))
                sel_truc = st.multiselect("Chọn Trục căn", truc_list)
            
            btn_tim_nc = st.button("Tìm kiếm ngay")
            
            if btn_tim_nc:
                temp_df = df.copy()
                if sel_toa != "Tất cả":
                    temp_df = temp_df[temp_df['Tòa'] == sel_toa]
                if sel_truc:
                    temp_df = temp_df[temp_df['Trục'].isin(sel_truc)]
                temp_df = temp_df[temp_df['Tầng'].between(f_from, f_to)]
                filtered_df = temp_df

        # 3. HIỂN THỊ KẾT QUẢ
        st.divider()
        if not filtered_df.empty:
            st.success(f"Tìm thấy {len(filtered_df)} căn hộ.")
            for i, r in filtered_df.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.subheader(f"🏠 Mã căn: {r['Mã đầy đủ']}")
                        # Hiển thị thông tin chi tiết theo yêu cầu
                        col_info1, col_info2 = st.columns(2)
                        with col_info1:
                            st.write(f"**Tòa:** {r['Tòa']} | **Tầng:** {r['Tầng']} | **Trục:** {r['Trục']}")
                            st.write(f"**Loại hình:** {r['Loại hình']} | **Diện tích:** {r['Diện tích']} m²")
                        with col_info2:
                            st.write(f"**Chủ nhà:** {r['Chủ nhà']}")
                            st.write(f"**Trạng thái:** :blue[{r['Trạng thái']}]")
                        
                        sdt_raw = str(r['Số điện thoại'])
                        st.markdown(f"📞 **SĐT:** `{sdt_raw[:4]}.xxx.xxx` (Bấm nút bên cạnh để xem)")
                    
                    with c2:
                        st.write("") # Căn chỉnh khoảng cách
                        if st.button(f"Xem số đầy đủ", key=f"btn_{r['Mã đầy đủ']}"):
                            st.info(f"SĐT chủ nhà: **{sdt_raw}**")
                            # Ghi Log
                            try:
                                sh_log = doc.worksheet("LOG_TRUY_CAP")
                                now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
                                sh_log.append_row([now, st.session_state['user_name'], r['Mã đầy đủ'], "Xem SĐT"])
                            except:
                                pass
        elif (btn_tim_ma or btn_tim_nc):
            st.warning("Không tìm thấy căn hộ nào phù hợp với yêu cầu lọc.")
        else:
            st.info("Vui lòng chọn bộ lọc và bấm nút 'Tìm kiếm' để hiển thị dữ liệu.")

    except Exception as e:
        st.error(f"Lỗi hiển thị dữ liệu: {e}")
