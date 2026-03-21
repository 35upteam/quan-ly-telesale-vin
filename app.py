import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide")

st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 4px; height: 32px; font-size: 13px; }
    .header-text { font-weight: bold; color: #1f2d3d; border-bottom: 2px solid #dee2e6; padding-bottom: 5px; font-size: 14px; }
    div[data-testid="stTextInput"] input { height: 32px; font-size: 13px; }
    .row-divider { border-bottom: 1px solid #f0f2f6; padding: 10px 0; }
    code { font-size: 14px !important; color: #007bff; background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# Danh sách chuẩn cho bộ lọc
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

# Khởi tạo session state
if 'res_df' not in st.session_state:
    st.session_state['res_df'] = pd.DataFrame()
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 2. ĐĂNG NHẬP ---
if st.session_state['logged_in'] == False:
    st.title("🔐 Đăng nhập hệ thống")
    u_val = st.text_input("Tài khoản").strip()
    p_val = st.text_input("Mật khẩu", type="password").strip()
    
    if st.button("Đăng nhập"):
        try:
            sh_u = doc.worksheet("QUAN_LY_USER")
            users_df = pd.DataFrame(sh_u.get_all_records())
            
            # FIX: Dùng .empty để kiểm tra bảng thay vì dùng 'if auth'
            auth_filter = users_df[(users_df['Username'].astype(str) == u_val) & (users_df['Password'].astype(str) == p_val)]
            
            if not auth_filter.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = u_val
                st.rerun()
            else:
                st.error("Tài khoản hoặc mật khẩu không đúng!")
        except Exception as e:
            st.error(f"Lỗi truy cập User: {e}")
else:
    # --- 3. BỘ LỌC DỮ LIỆU ---
    st.sidebar.write(f"👤 Chào: **{st.session_state['user_name']}**")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.clear()
        st.rerun()

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_vals = sh_data.get_all_values()
        h_names = raw_vals[0]
        df_main = pd.DataFrame(raw_vals[1:], columns=h_names)
        
        for c in df_main.columns:
            df_main[c] = df_main[c].apply(lambda x: str(x).strip() if x else "")

        c1, c2, c3, c4 = st.columns([1, 1, 1, 1.5])
        with c1: 
            toas = sorted([t for t in df_main['Tòa'].unique() if t])
            sel_t = st.multiselect("Chọn Tòa", toas)
        with c2: f_s = st.selectbox("Từ tầng", LIST_TANG_PHYSICAL, index=4)
        with c3: f_e = st.selectbox("Đến tầng", LIST_TANG_PHYSICAL, index=15)
        with c4: sel_tr = st.multiselect("Chọn Trục", LIST_TRUC)

        if st.button("🚀 Thực hiện lọc"):
            t_df = df_main.copy()
            # FIX: Dùng len() để kiểm tra list chọn, tránh lỗi Ambiguous
            if len(sel_t) > 0:
                t_df = t_df[t_df['Tòa'].isin(sel_t)]
            if len(sel_tr) > 0:
                t_df = t_df[t_df['Trục'].isin(sel_tr)]
            
            idx_s = LIST_TANG_PHYSICAL.index(f_s)
            idx_e = LIST_TANG_PHYSICAL.index(f_e)
            allowed = LIST_TANG_PHYSICAL[idx_s : idx_e + 1]
            t_df = t_df[t_df['Tầng'].isin(allowed)]
            
            st.session_state['res_df'] = t_df

        # --- 4. HIỂN THỊ DẠNG BẢNG ---
        res_display = st.session_state['res_df']
        
        if not res_display.empty:
            st.divider()
            h_cols = st.columns([1.2, 1.2, 0.7, 1.5, 2.5, 0.7])
            labels = ["Mã Căn", "Chủ Nhà", "DT", "SĐT (Bấm 👁️)", "Ghi chú nội bộ", "Lưu"]
            for ui, lb in zip(h_cols, labels):
                ui.markdown(f"<div class='header-text'>{lb}</div>", unsafe_allow_html=True)

            for i, r in res_display.iterrows():
                row_ui = st.columns([1.2, 1.2, 0.7, 1.5, 2.5, 0.7])
                row_ui[0].write(f"**{r['Mã đầy đủ']}**")
                row_ui[1].write(r['Chủ nhà'])
                row_ui[2].write(f"{r['Diện tích']}m²")
                
                # SĐT & Icon mắt & Copy nhanh
                s_key = f"v_{r['Mã đầy đủ']}"
                if s_key in st.session_state and st.session_state[s_key] == True:
                    # st.code tự động có nút Copy ở góc trên bên phải
                    row_ui[3].code(r['Số điện thoại'], language="text")
                else:
                    pre = r['Số điện thoại'][:4] if len(r['Số điện thoại']) > 4 else "0xxx"
                    if row_ui[3].button(f"👁️ {pre}...", key=f"btn_{i}"):
                        st.session_state[s_key] = True
                        st.rerun()
                
                # Note & Save
                note_val = row_ui[4].text_input("N", value=r.get('Ghi chú', ''), key=f"in_{i}", label_visibility="collapsed")
                if row_ui[5].button("💾", key=f"sv_{i}"):
                    try:
                        cell = sh_data.find(r['Mã đầy đủ'])
                        if 'Ghi chú' in h_names:
                            g_idx = h_names.index('Ghi chú') + 1
                            sh_data.update_cell(cell.row, g_idx, note_val)
                            st.toast(f"Đã cập nhật!", icon="✅")
                        else: st.error("Thiếu cột Ghi chú")
                    except: st.error("Lỗi lưu!")
                
                st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)
        
        elif 'res_df' in st.session_state and len(st.session_state['res_df']) == 0:
            st.info("Sử dụng bộ lọc phía trên và bấm 'Lọc' để xem danh sách.")

    except Exception as e:
        st.error(f"Lỗi: {e}")
