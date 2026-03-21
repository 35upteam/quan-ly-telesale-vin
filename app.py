import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Telesale Vin", layout="wide")

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
        st.error(f"Lỗi kết nối Google Sheets: {e}")
        st.stop()

def get_col(df, keywords):
    """Hàm tự động tìm cột dựa trên từ khóa gần đúng"""
    for col in df.columns:
        for kw in keywords:
            if kw.lower() in col.lower().strip():
                return col
    return None

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
        try:
            sh_user = doc.worksheet("QUAN_LY_USER")
            data_u = sh_user.get_all_values()
            u_df = pd.DataFrame(data_u[1:], columns=data_u[0])
            c_u = get_col(u_df, ["user", "tài khoản"])
            c_p = get_col(u_df, ["pass", "mật khẩu"])
            auth = u_df[(u_df[c_u].str.strip() == u.strip()) & (u_df[c_p].astype(str).str.strip() == p.strip())]
            if not auth.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = u
                st.rerun()
            else: st.error("Sai thông tin!")
        except: st.error("Không tìm thấy tab QUAN_LY_USER")
else:
    st.sidebar.write(f"👤 {st.session_state['user_name']}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.clear()
        st.rerun()

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_data = sh_data.get_all_values()
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        
        # TỰ ĐỘNG NHẬN DIỆN CỘT
        COL_MA = get_col(df, ["mã đầy đủ", "mã căn", "full mã"])
        COL_TOA = get_col(df, ["tòa", "block"])
        COL_TANG = get_col(df, ["tầng", "floor"])
        COL_TRUC = get_col(df, ["trục", "vị trí"])
        COL_SDT = get_col(df, ["số điện thoại", "sđt", "phone"])
        COL_CHU = get_col(df, ["chủ nhà", "tên chủ"])
        COL_TT = get_col(df, ["trạng thái", "status"])

        tab1, tab2 = st.tabs(["🔍 Tìm nhanh", "📂 Lọc nâng cao"])
        
        with tab1:
            m_input = st.text_input("Nhập mã căn (Ví dụ: S1.02...)").strip()
            if st.button("Tìm kiếm"):
                st.session_state['search_results'] = df[df[COL_MA].str.contains(m_input, case=False, na=False)]
                st.session_state['view_mode'] = 'single'

        with tab2:
            c1, c2 = st.columns(2)
            with c1:
                list_t = sorted(list(df[COL_TOA].unique()))
                sel_t = st.multiselect("Chọn Tòa", list_t)
            with c2:
                list_tr = sorted(list(df[COL_TRUC].unique()))
                sel_tr = st.multiselect("Chọn Trục", list_tr)
            
            s_t, e_t = st.select_slider('Khoảng tầng', options=LIST_TANG_CHIEU_NGHI, value=("1", "39"))
            
            if st.button("🚀 Lọc danh sách"):
                t_df = df.copy()
                if sel_t: t_df = t_df[t_df[COL_TOA].isin(sel_t)]
                if sel_tr: t_df = t_df[t_df[COL_TRUC].isin(sel_tr)]
                
                idx_s = LIST_TANG_CHIEU_NGHI.index(s_t)
                idx_e = LIST_TANG_CHIEU_NGHI.index(e_t)
                allowed = LIST_TANG_CHIEU_NGHI[idx_s : idx_e + 1]
                t_df = t_df[t_df[COL_TANG].astype(str).str.strip().isin(allowed)]
                
                st.session_state['search_results'] = t_df
                st.session_state['view_mode'] = 'table'

        st.divider()
        res = st.session_state['search_results']

        if not res.empty:
            st.write(f"Tìm thấy **{len(res)}** kết quả.")
            h = st.columns([1.5, 1.5, 1.5, 1, 1])
            for col, n in zip(h, ["Mã Căn", "Chủ Nhà", "SĐT", "Loại", "Trạng Thái"]): col.markdown(f"**{n}**")
            
            for i, r in res.iterrows():
                c = st.columns([1.5, 1.5, 1.5, 1, 1])
                c[0].write(r[COL_MA])
                c[1].write(r[COL_CHU])
                
                sk = f"sh_{r[COL_MA]}"
                if sk in st.session_state and st.session_state[sk]:
                    c[2].code(r[COL_SDT], language="text")
                else:
                    if c[2].button(f"👁️ {str(r[COL_SDT])[:3]}...", key=f"e_{r[COL_MA]}"):
                        st.session_state[sk] = True
                        st.rerun()
                
                c[3].write(r.get('Loại hình', '---'))
                tt = r.get(COL_TT, 'Trống')
                color = "green" if "Trống" in tt else "red" if "Đã bán" in tt else "orange"
                c[4].markdown(f":{color}[{tt}]")
        elif st.session_state['view_mode']:
            st.warning("Không tìm thấy căn nào. Hãy thử nới lỏng bộ lọc.")

    except Exception as e:
        st.error(f"Lỗi: {e}. Vui lòng kiểm tra tên các tab trong Google Sheets.")
