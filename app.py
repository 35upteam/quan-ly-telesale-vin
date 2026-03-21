import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH GIAO DIỆN (FULL SCREEN) ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

# CSS để tinh chỉnh giao diện phẳng, hiện đại
st.markdown("""
    <style>
    /* Ẩn sidebar hoàn toàn */
    [data-testid="stSidebar"] { display: none; }
    
    /* Tăng kích thước ô nhập liệu và nút */
    .stButton button { width: 100%; border-radius: 6px; height: 40px; font-weight: bold; }
    .header-text { font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 15px; }
    div[data-testid="stTextInput"] input { height: 42px; }
    
    /* Chia dòng kẻ giữa các căn hộ */
    .row-divider { border-bottom: 1px solid #ebedef; padding: 12px 0; }
    
    /* Định dạng ô số điện thoại */
    code { font-size: 15px !important; color: #1e88e5 !important; background-color: #f1f3f4 !important; border: 1px solid #dee2e6 !important; }
    
    /* Header chào nhân viên */
    .user-header {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding: 10px 0;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

LIST_TANG_PHYSICAL = ["1", "2", "3", "05A", "05", "06", "07", "08", "08A", "09", "10", "11", "12", "12A", "15A", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]
LIST_TRUC = [f"{i:02d}" for i in range(1, 31)]

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
        st.error(f"Lỗi kết nối: {e}")
        return None

doc = init_connection()

if 'res_df' not in st.session_state:
    st.session_state['res_df'] = pd.DataFrame()
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 2. MÀN HÌNH ĐĂNG NHẬP ---
if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập hệ thống")
    c_login, _ = st.columns([1, 2])
    with c_login:
        u_val = st.text_input("Tài khoản").strip()
        p_val = st.text_input("Mật khẩu", type="password").strip()
        if st.button("Đăng nhập"):
            try:
                sh_u = doc.worksheet("QUAN_LY_USER")
                users_df = pd.DataFrame(sh_u.get_all_records())
                auth = users_df[(users_df['Username'].astype(str) == u_val) & (users_df['Password'].astype(str) == p_val)]
                if not auth.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = u_val
                    st.rerun()
                else:
                    st.error("Tài khoản hoặc mật khẩu không đúng!")
            except:
                st.error("Không thể kết nối danh sách người dùng.")
else:
    # --- 3. HEADER GÓC PHẢI (CHÀO & ĐĂNG XUẤT) ---
    h_left, h_right = st.columns([7, 3])
    with h_right:
        st.markdown(f"<div style='text-align: right; padding-top: 5px;'>👤 Chào: <b>{st.session_state['user_name']}</b></div>", unsafe_allow_html=True)
        if st.button("🚪 Đăng xuất", key="logout_top"):
            st.session_state.clear()
            st.rerun()

    # --- 4. TẢI DỮ LIỆU ---
    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_vals = sh_data.get_all_values()
        h_names = raw_vals[0]
        df_main = pd.DataFrame(raw_vals[1:], columns=h_names)
        
        # Làm sạch dữ liệu
        df_main = df_main.applymap(lambda x: str(x).strip() if x is not None else "")
        df_main['Tòa_Clean'] = df_main['Tòa'].apply(lambda x: x.replace(".", ""))
        df_main['Trục_Clean'] = df_main['Trục'].apply(lambda x: x.replace(".0", "").zfill(2) if x else "")

        # --- 5. BỘ LỌC CHIA THEO TABS ---
        tab_ma, tab_tieuchi = st.tabs(["🔍 Tìm theo Mã Căn", "📊 Lọc theo Tầng & Trục"])

        with tab_ma:
            col_search, col_btn = st.columns([3, 1])
            with col_search:
                search_ma = st.text_input("Nhập mã đầy đủ (S1010506...)", key="input_ma")
            with col_btn:
                st.write("##")
                btn_find_ma = st.button("Tìm mã căn", key="btn_find_ma")
            
            if btn_find_ma:
                st.session_state['res_df'] = df_main[df_main['Mã đầy đủ'].str.contains(search_ma.strip(), case=False)]

        with tab_tieuchi:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            with c1:
                ds_toa = sorted([t for t in df_main['Tòa'].unique() if t])
                sel_t = st.multiselect("Chọn Tòa", ds_toa)
            with c2: f_s = st.selectbox("Từ tầng", LIST_TANG_PHYSICAL, index=4)
            with c3: f_e = st.selectbox("Đến tầng", LIST_TANG_PHYSICAL, index=15)
            with c4: sel_tr = st.multiselect("Chọn Trục", LIST_TRUC)
            
            btn_filter = st.button("🚀 Thực hiện lọc danh sách", key="btn_filter")
            
            if btn_filter:
                t_df = df_main.copy()
                if len(sel_t) > 0:
                    sel_t_cl = [x.replace(".", "") for x in sel_t]
                    t_df = t_df[t_df['Tòa_Clean'].isin(sel_t_cl)]
                if len(sel_tr) > 0:
                    t_df = t_df[t_df['Trục_Clean'].isin(sel_tr)]
                
                # Lọc tầng
                idx_s, idx_e = LIST_TANG_PHYSICAL.index(f_s), LIST_TANG_PHYSICAL.index(f_e)
                allowed = LIST_TANG_PHYSICAL[idx_s : idx_e + 1]
                t_df = t_df[t_df['Tầng'].isin(allowed)]
                st.session_state['res_df'] = t_df

        # --- 6. HIỂN THỊ KẾT QUẢ ---
        res_display = st.session_state['res_df']
        
        if not res_display.empty:
            st.divider()
            st.success(f"Tìm thấy {len(res_display)} căn hộ.")
            
            # Header bảng hàng ngang
            cols_ui = st.columns([1.2, 1.2, 0.6, 1.5, 2.5, 0.6])
            titles = ["Mã Căn", "Chủ Nhà", "DT", "SĐT (📞 Bấm hiện)", "Ghi chú nội bộ", "Lưu"]
            for ui, txt in zip(cols_ui, titles):
                ui.markdown(f"<div class='header-text'>{txt}</div>", unsafe_allow_html=True)

            for i, r in res_display.iterrows():
                row = st.columns([1.2, 1.2, 0.6, 1.5, 2.5, 0.6])
                row[0].write(f"**{r['Mã đầy đủ']}**")
                row[1].write(r['Chủ nhà'])
                row[2].write(f"{r['Diện tích']}m²")
                
                # SĐT & Icon 📞
                s_key = f"v_{r['Mã đầy đủ']}"
                if s_key in st.session_state and st.session_state[s_key]:
                    row[3].code(r['Số điện thoại'], language="text")
                else:
                    label_sdt = r['Số điện thoại'][:4] + "..." if len(r['Số điện thoại']) > 4 else "Hiện số"
                    if row[3].button(f"📞 {label_sdt}", key=f"btn_{i}"):
                        st.session_state[s_key] = True
                        st.rerun()
                
                # Ghi chú
                n_val = row[4].text_input("N", value=r.get('Ghi chú', ''), key=f"in_{i}", label_visibility="collapsed")
                
                # Nút lưu 💾
                if row[5].button("💾", key=f"sv_{i}"):
                    try:
                        cell = sh_data.find(r['Mã đầy đủ'])
                        g_col = h_names.index('Ghi chú') + 1
                        sh_data.update_cell(cell.row, g_col, n_val)
                        st.toast(f"Đã cập nhật {r['Mã đầy đủ']}!", icon="✅")
                    except: st.error("Lỗi lưu!")
                
                st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)
        else:
            if 'res_df' in st.session_state:
                st.info("Sử dụng các Tab trên để bắt đầu tìm kiếm dữ liệu.")

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
