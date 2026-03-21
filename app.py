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

# Khởi tạo trạng thái lưu trữ kết quả lọc để không bị reset khi bấm nút
if 'search_results' not in st.session_state:
    st.session_state['search_results'] = pd.DataFrame()
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = None # 'single' hoặc 'table'

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
        st.session_state.clear()
        st.rerun()

    st.title("🏘️ Tra cứu Căn hộ")

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_data = sh_data.get_all_values()
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        df['Tầng'] = pd.to_numeric(df['Tầng'], errors='coerce').fillna(0)

        # KHU VỰC BỘ LỌC
        tab1, tab2 = st.tabs(["🔍 Tìm theo Mã căn", "📂 Tìm nâng cao (Xem bảng)"])
        
        with tab1:
            ma_can_input = st.text_input("Nhập mã căn (Ví dụ: S1.02-15-05)").strip()
            if st.button("Tìm mã cụ thể"):
                st.session_state['search_results'] = df[df['Mã đầy đủ'].str.contains(ma_can_input, case=False, na=False)]
                st.session_state['view_mode'] = 'single'

        with tab2:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                toa_list = ["Tất cả"] + sorted(list(df['Tòa'].unique()))
                sel_toa = st.selectbox("Chọn Tòa", toa_list)
            with col2:
                f_from = st.number_input("Tầng từ", value=1, step=1)
            with col3:
                f_to = st.number_input("Đến tầng", value=50, step=1)
            with col4:
                truc_list = sorted(list(df['Trục'].unique()))
                sel_truc = st.multiselect("Chọn Trục căn", truc_list)
            
            if st.button("Lọc danh sách"):
                temp_df = df.copy()
                if sel_toa != "Tất cả":
                    temp_df = temp_df[temp_df['Tòa'] == sel_toa]
                if sel_truc:
                    temp_df = temp_df[temp_df['Trục'].isin(sel_truc)]
                temp_df = temp_df[temp_df['Tầng'].between(f_from, f_to)]
                st.session_state['search_results'] = temp_df
                st.session_state['view_mode'] = 'table'

        # HIỂN THỊ KẾT QUẢ
        st.divider()
        res = st.session_state['search_results']

        if not res.empty:
            if st.session_state['view_mode'] == 'single':
                # HIỂN THỊ DẠNG Ô (CHO 1 MÃ CĂN)
                for i, r in res.iterrows():
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.subheader(f"🏠 {r['Mã đầy đủ']}")
                            st.write(f"**Chủ nhà:** {r['Chủ nhà']} | **Trạng thái:** {r['Trạng thái']}")
                            st.write(f"**Thông tin:** {r['Loại hình']} - {r['Diện tích']}m2 - Tầng {r['Tầng']}")
                            st.info(f"📞 SĐT: `{str(r['Số điện thoại'])[:4]}.xxx.xxx`")
                        with c2:
                            if st.button(f"Hiện số", key=f"single_{r['Mã đầy đủ']}"):
                                st.success(f"SĐT: {r['Số điện thoại']}")
                                # Ghi log
                                doc.worksheet("LOG_TRUY_CAP").append_row([datetime.now().strftime("%H:%M %d/%m"), st.session_state['user_name'], r['Mã đầy đủ']])

            else:
                # HIỂN THỊ DẠNG BẢNG NGANG (CHO LỌC NÂNG CAO)
                # Tạo tiêu đề bảng
                cols = st.columns([1.5, 0.8, 0.8, 0.8, 1.5, 1.5, 1.2, 1, 1.2])
                headers = ["Mã Căn", "Tòa", "Tầng", "Trục", "Chủ Nhà", "SĐT", "Loại", "D.Tích", "Xem"]
                for col, h in zip(cols, headers):
                    col.write(f"**{h}**")
                
                for i, r in res.iterrows():
                    c = st.columns([1.5, 0.8, 0.8, 0.8, 1.5, 1.5, 1.2, 1, 1.2])
                    c[0].write(r['Mã đầy đủ'])
                    c[1].write(r['Tòa'])
                    c[2].write(str(r['Tầng']))
                    c[3].write(r['Trục'])
                    c[4].write(r['Chủ nhà'])
                    c[5].write(f"{str(r['Số điện thoại'])[:4]}...")
                    c[6].write(r['Loại hình'])
                    c[7].write(f"{r['Diện tích']}m2")
                    if c[8].button("Hiện", key=f"tab_{r['Mã đầy đủ']}"):
                        st.toast(f"SĐT {r['Mã đầy đủ']}: {r['Số điện thoại']}", icon="📞")
                        st.sidebar.warning(f"SĐT {r['Mã đầy đủ']}: {r['Số điện thoại']}")
                        # Ghi log
                        doc.worksheet("LOG_TRUY_CAP").append_row([datetime.now().strftime("%H:%M %d/%m"), st.session_state['user_name'], r['Mã đầy đủ']])
        
        elif st.session_state['view_mode'] is not None:
            st.warning("Không tìm thấy kết quả phù hợp.")

    except Exception as e:
        st.error(f"Lỗi: {e}")
