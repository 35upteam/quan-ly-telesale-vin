import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Telesale Vin", layout="wide")

# Danh sách Tòa chuẩn Vinhomes Smart City theo yêu cầu
LIST_TOA = [
    "S1.01", "S1.02", "S1.03", "S1.05", "S1.06", "S2.01", "S2.02", "S2.03", "S2.05", 
    "S3.01", "S3.02", "S3.03", "S4.01", "S4.02", "S4.03", "GS1", "GS2", "GS3", "GS5", "GS6", 
    "SA1", "SA2", "SA3", "SA5", "V1", "V2", "V3", "TK1", "TK2", "TC1", "TC2", "TC3", 
    "West A", "West B", "West C", "West D", "The Aura (A3)", "The Atmos (A2)", "The Aqua (A1)", 
    "I1", "I2", "I3", "I4", "I5", "G1", "G2", "G3", "G5", "G6"
]

# Danh sách Tầng chuẩn (bao gồm các tầng đặc thù)
LIST_TANG = [
    "1", "2", "3", "05A", "05", "06", "07", "08", "08A", "09", "10", "11", "12", "12A", 
    "15A", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", 
    "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"
]

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

if 'show_phone' not in st.session_state: st.session_state['show_phone'] = {}
if 'search_results' not in st.session_state: st.session_state['search_results'] = pd.DataFrame()
if 'view_mode' not in st.session_state: st.session_state['view_mode'] = None

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

    st.title("🏘️ Tra cứu Căn hộ Smart City")

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_data = sh_data.get_all_values()
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])

        tab1, tab2 = st.tabs(["🔍 Tìm theo Mã căn", "📂 Lọc nâng cao"])
        
        with tab1:
            m_input = st.text_input("Nhập mã căn cụ thể (Ví dụ: S1.02-15-05)").strip()
            if st.button("🔍 Tìm nhanh"):
                st.session_state['search_results'] = df[df['Mã đầy đủ'].str.contains(m_input, case=False, na=False)]
                st.session_state['view_mode'] = 'single'

        with tab2:
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                sel_toas = st.multiselect("Chọn Tòa (có thể chọn nhiều)", LIST_TOA)
            with c2:
                # Dùng multiselect cho tầng để xử lý chính xác 05A, 12A...
                sel_tangs = st.multiselect("Chọn Tầng (có thể chọn nhiều)", LIST_TANG)
            with c3:
                # Lấy danh sách trục thực tế từ Sheet
                truc_list = sorted(list(df['Trục'].unique()))
                sel_trucs = st.multiselect("Chọn Trục", truc_list)
            
            if st.button("🚀 Bắt đầu lọc dữ liệu"):
                t_df = df.copy()
                if sel_toas:
                    t_df = t_df[t_df['Tòa'].isin(sel_toas)]
                if sel_tangs:
                    # Chuyển cả hai về string để so sánh chính xác các tầng có chữ
                    t_df = t_df[t_df['Tầng'].astype(str).isin(sel_tangs)]
                if sel_trucs:
                    t_df = t_df[t_df['Trục'].isin(sel_trucs)]
                
                st.session_state['search_results'] = t_df
                st.session_state['view_mode'] = 'table'

        st.divider()
        res = st.session_state['search_results']

        if not res.empty:
            if st.session_state['view_mode'] == 'single':
                for i, r in res.iterrows():
                    with st.container(border=True):
                        st.subheader(f"🏠 {r['Mã đầy đủ']}")
                        st.write(f"Chủ nhà: {r['Chủ nhà']} | Loại: {r['Loại hình']} | Diện tích: {r['Diện tích']}m2")
                        if st.button(f"👁️ Hiện SĐT {r['Mã đầy đủ']}", key=f"s_{r['Mã đầy đủ']}"):
                            st.code(r['Số điện thoại'], language="text")
                            doc.worksheet("LOG_TRUY_CAP").append_row([datetime.now().strftime("%H:%M %d/%m"), st.session_state['user_name'], r['Mã đầy đủ']])

            else:
                # GIAO DIỆN BẢNG GỌN GÀNG
                st.write(f"Tìm thấy **{len(res)}** kết quả phù hợp.")
                h = st.columns([1.5, 1.5, 1.5, 1, 1, 1.2])
                cols_name = ["Mã Căn", "Chủ Nhà", "SĐT", "Loại", "D.Tích", "Trạng Thái"]
                for col, name in zip(h, cols_name):
                    col.markdown(f"**{name}**")
                
                for i, r in res.iterrows():
                    c = st.columns([1.5, 1.5, 1.5, 1, 1, 1.2])
                    c[0].write(r['Mã đầy đủ'])
                    c[1].write(r['Chủ nhà'])
                    
                    sdt_key = f"show_{r['Mã đầy đủ']}"
                    if sdt_key in st.session_state and st.session_state[sdt_key]:
                        c[2].code(r['Số điện thoại'], language="text")
                    else:
                        if c[2].button(f"👁️ {str(r['Số điện thoại'])[:3]}...", key=f"eye_{r['Mã đầy đủ']}"):
                            st.session_state[sdt_key] = True
                            doc.worksheet("LOG_TRUY_CAP").append_row([datetime.now().strftime("%H:%M %d/%m"), st.session_state['user_name'], r['Mã đầy đủ']])
                            st.rerun()
                    
                    c[3].write(r['Loại hình'])
                    c[4].write(f"{r['Diện tích']}m2")
                    tt = r['Trạng thái']
                    color = "green" if "Trống" in tt else "red" if "Đã bán" in tt else "orange"
                    c[5].markdown(f":{color}[{tt}]")
        
        elif st.session_state['view_mode'] is not None:
            st.info("Không có dữ liệu phù hợp với bộ lọc.")

    except Exception as e:
        st.error(f"Lỗi: {e}")
