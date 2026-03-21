import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Telesale Vin", layout="wide")

LIST_TOA = ["S1.01", "S1.02", "S1.03", "S1.05", "S1.06", "S2.01", "S2.02", "S2.03", "S2.05", "S3.01", "S3.02", "S3.03", "S4.01", "S4.02", "S4.03", "GS1", "GS2", "GS3", "GS5", "GS6", "SA1", "SA2", "SA3", "SA5", "V1", "V2", "V3", "TK1", "TK2", "TC1", "TC2", "TC3", "West A", "West B", "West C", "West D", "The Aura (A3)", "The Atmos (A2)", "The Aqua (A1)", "I1", "I2", "I3", "I4", "I5", "G1", "G2", "G3", "G5", "G6"]
LIST_TANG_CHIEU_NGHI = ["1", "2", "3", "05A", "05", "06", "07", "08", "08A", "09", "10", "11", "12", "12A", "15A", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]

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
        auth = u_df[(u_df['Username'].str.strip() == u.strip()) & (u_df['Password'].astype(str).str.strip() == p.strip())]
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
        
        # Làm sạch dữ liệu Sheet (Xóa khoảng trắng thừa ở các cột quan trọng)
        for col in ['Tòa', 'Tầng', 'Trục', 'Mã đầy đủ']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        tab1, tab2 = st.tabs(["🔍 Tìm theo Mã căn", "📂 Lọc nâng cao"])
        
        with tab1:
            m_input = st.text_input("Nhập mã căn cụ thể").strip()
            if st.button("🔍 Tìm nhanh"):
                st.session_state['search_results'] = df[df['Mã đầy đủ'].str.contains(m_input, case=False, na=False)]
                st.session_state['view_mode'] = 'single'

        with tab2:
            c_toa, c_truc = st.columns(2)
            with c_toa:
                sel_toas = st.multiselect("Chọn Tòa", LIST_TOA)
            with c_truc:
                # Lấy danh sách trục thực tế từ Sheet để đảm bảo luôn có dữ liệu
                actual_trucs = sorted(list(df['Trục'].unique()))
                sel_trucs = st.multiselect("Chọn Trục", actual_trucs)
            
            st.write("**Chọn khoảng tầng:**")
            start_t, end_t = st.select_slider('Kéo để chọn khoảng tầng', options=LIST_TANG_CHIEU_NGHI, value=("1", "39"))
            
            if st.button("🚀 Bắt đầu lọc"):
                t_df = df.copy()
                if sel_toas:
                    t_df = t_df[t_df['Tòa'].isin(sel_toas)]
                if sel_trucs:
                    t_df = t_df[t_df['Trục'].isin(sel_trucs)]
                
                # Lọc tầng dựa trên danh sách thứ tự
                idx_s = LIST_TANG_CHIEU_NGHI.index(start_t)
                idx_e = LIST_TANG_CHIEU_NGHI.index(end_t)
                allowed_tangs = LIST_TANG_CHIEU_NGHI[idx_s : idx_e + 1]
                t_df = t_df[t_df['Tầng'].isin(allowed_tangs)]
                
                st.session_state['search_results'] = t_df
                st.session_state['view_mode'] = 'table'

        st.divider()
        res = st.session_state['search_results']

        if not res.empty:
            if st.session_state['view_mode'] == 'single':
                for i, r in res.iterrows():
                    with st.container(border=True):
                        st.subheader(f"🏠 {r['Mã đầy đủ']}")
                        st.write(f"Chủ nhà: {r.get('Chủ nhà','N/A')} | Loại: {r.get('Loại hình','N/A')} | DT: {r.get('Diện tích','N/A')}m2")
                        if st.button(f"👁️ Hiện SĐT {r['Mã đầy đủ']}", key=f"s_{r['Mã đầy đủ']}"):
                            st.code(r.get('Số điện thoại','N/A'), language="text")
            else:
                st.write(f"Tìm thấy **{len(res)}** căn hộ.")
                h = st.columns([1.5, 1.5, 1.5, 1, 1, 1.2])
                names = ["Mã Căn", "Chủ Nhà", "SĐT", "Loại", "D.Tích", "Trạng Thái"]
                for col, n in zip(h, names): col.markdown(f"**{n}**")
                
                for i, r in res.iterrows():
                    c = st.columns([1.5, 1.5, 1.5, 1, 1, 1.2])
                    c[0].write(r.get('Mã đầy đủ','N/A'))
                    c[1].write(r.get('Chủ nhà','N/A'))
                    
                    s_k = f"sh_{r['Mã đầy đủ']}"
                    if s_k in st.session_state and st.session_state[s_k]:
                        c[2].code(r.get('Số điện thoại',''), language="text")
                    else:
                        if c[2].button(f"👁️ {str(r.get('Số điện thoại',''))[:3]}...", key=f"e_{r['Mã đầy đủ']}"):
                            st.session_state[s_k] = True
                            # Ghi log
                            try:
                                doc.worksheet("LOG_TRUY_CAP").append_row([datetime.now().strftime("%H:%M %d/%m"), st.session_state['user_name'], r['Mã đầy đủ']])
                            except: pass
                            st.rerun()
                    
                    c[3].write(r.get('Loại hình','N/A'))
                    c[4].write(f"{r.get('Diện tích','N/A')}m2")
                    tt = r.get('Trạng thái','Trống')
                    color = "green" if "Trống" in tt else "red" if "Đã bán" in tt else "orange"
                    c[5].markdown(f":{color}[{tt}]")
        elif st.session_state['view_mode'] is not None:
            st.warning("Không có dữ liệu phù hợp. Vui lòng kiểm tra lại Tòa hoặc Trục căn trong Sheet.")

    except Exception as e:
        st.error(f"Lỗi: {e}")
