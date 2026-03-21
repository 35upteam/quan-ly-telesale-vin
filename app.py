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
    div[data-testid="stTextInput"] input { height: 38px; font-size: 14px; }
    .row-divider { border-bottom: 1px solid #f0f2f6; padding: 10px 0; }
    code { font-size: 14px !important; color: #007bff !important; background-color: #f8f9fa; border: 1px solid #ddd; }
    
    /* CSS cho khu vực User ở góc phải */
    .user-box {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 15px;
        padding: 10px;
        background-color: #f0f2f6;
        border-radius: 8px;
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

# --- 2. LOGIC ĐĂNG NHẬP ---
if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập hệ thống")
    col_l, col_r = st.columns([1, 2])
    with col_l:
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
            except Exception as e:
                st.error(f"Lỗi: {e}")
else:
    # --- 3. THANH NGANG USER (GÓC PHẢI) ---
    u_col1, u_col2 = st.columns([8, 2])
    with u_col2:
        st.markdown(f"👤 Chào: **{st.session_state['user_name']}**")
        if st.button("Đăng xuất", key="logout_btn"):
            st.session_state.clear()
            st.rerun()

    # --- 4. TẢI DỮ LIỆU ---
    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_vals = sh_data.get_all_values()
        h_names = raw_vals[0]
        df_main = pd.DataFrame(raw_vals[1:], columns=h_names)
        
        # Chuẩn hóa
        df_main = df_main.applymap(lambda x: str(x).strip() if x is not None else "")
        df_main['Tòa_Clean'] = df_main['Tòa'].apply(lambda x: x.replace(".", ""))
        df_main['Trục_Clean'] = df_main['Trục'].apply(lambda x: x.replace(".0", "").zfill(2) if x else "")

        # --- 5. CHIA TABS BỘ LỌC ---
        tab_code, tab_filter = st.tabs(["🔍 Tìm theo Mã Căn", "📊 Lọc theo Tiêu chí"])

        with tab_code:
            c_m1, c_m2 = st.columns([3, 1])
            with c_m1:
                search_ma = st.text_input("Nhập mã căn đầy đủ (Ví dụ: S1010506)", key="search_ma_input")
            with c_m2:
                st.write("##")
                btn_ma = st.button("Tìm kiếm mã này", use_container_width=True)
            
            if btn_ma:
                st.session_state['res_df'] = df_main[df_main['Mã đầy đủ'].str.contains(search_ma.strip(), case=False)]

        with tab_filter:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            with c1: 
                toas_raw = sorted([t for t in df_main['Tòa'].unique() if t])
                sel_t = st.multiselect("Chọn Tòa", toas_raw)
            with c2: f_s = st.selectbox("Từ tầng", LIST_TANG_PHYSICAL, index=4)
            with c3: f_e = st.selectbox("Đến tầng", LIST_TANG_PHYSICAL, index=15)
            with c4: sel_tr = st.multiselect("Chọn Trục", LIST_TRUC)
            
            btn_filter = st.button("🚀 Thực hiện lọc theo tiêu chí", use_container_width=True)
            
            if btn_filter:
                t_df = df_main.copy()
                if len(sel_t) > 0:
                    sel_t_clean = [x.replace(".", "") for x in sel_t]
                    t_df = t_df[t_df['Tòa_Clean'].isin(sel_t_clean)]
                if len(sel_tr) > 0:
                    t_df = t_df[t_df['Trục_Clean'].isin(sel_tr)]
                
                idx_s, idx_e = LIST_TANG_PHYSICAL.index(f_s), LIST_TANG_PHYSICAL.index(f_e)
                allowed = LIST_TANG_PHYSICAL[idx_s : idx_e + 1]
                t_df = t_df[t_df['Tầng'].isin(allowed)]
                st.session_state['res_df'] = t_df

        # --- 6. HIỂN THỊ KẾT QUẢ ---
        res_display = st.session_state['res_df']
        
        if not res_display.empty:
            st.divider()
            st.info(f"Đang hiển thị {len(res_display)} kết quả.")
            
            # Header
            h_cols = st.columns([1.2, 1.2, 0.6, 1.5, 2.5, 0.6])
            labels = ["Mã Căn", "Chủ Nhà", "DT", "SĐT (Bấm 📞)", "Ghi chú", "Lưu"]
            for ui, lb in zip(h_cols, labels):
                ui.markdown(f"<div class='header-text'>{lb}</div>", unsafe_allow_html=True)

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
                    pre = r['Số điện thoại'][:4] + "..." if len(r['Số điện thoại']) > 4 else "Xem"
                    if row[3].button(f"📞 {pre}", key=f"btn_{i}"):
                        st.session_state[s_key] = True
                        st.rerun()
                
                note_val = row[4].text_input("N", value=r.get('Ghi chú', ''), key=f"in_{i}", label_visibility="collapsed")
                if row[5].button("💾", key=f"sv_{i}"):
                    try:
                        cell = sh_data.find(r['Mã đầy đủ'])
                        g_col = h_names.index('Ghi chú') + 1
                        sh_data.update_cell(cell.row, g_col, note_val)
                        st.toast(f"Đã lưu căn {r['Mã đầy đủ']}!", icon="✅")
                    except: st.error("Lỗi lưu")
                st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)
        else:
            if 'res_df' in st.session_state:
                st.write("Hãy chọn bộ lọc hoặc nhập mã căn để xem dữ liệu.")

    except Exception as e:
        st.error(f"Lỗi: {e}")
