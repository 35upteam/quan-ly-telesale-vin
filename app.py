import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap');
    [data-testid="stSidebar"] { display: none; }
    
    /* Căn chỉnh header để tên và nút X nằm ngang hàng tuyệt đối */
    .header-wrapper {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 10px;
        margin-bottom: 15px;
    }
    
    .logout-btn-style button {
        background-color: #ff4b4b !important;
        color: white !important;
        border: none !important;
        width: 32px !important;
        height: 32px !important;
        border-radius: 6px !important;
        padding: 0 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        line-height: 1 !important;
    }

    .stButton button { width: 100%; border-radius: 6px; height: 38px; font-weight: bold; }
    div[data-testid="column"]:nth-of-type(2) button[kind="secondary"] { background-color: #007bff; color: white; border: none; }
    .save-btn button { background-color: #28a745 !important; color: white !important; border: none !important; }
    div[data-testid="stTextInput"] input { height: 42px; border-radius: 6px; }
    .header-text { font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 14px; }
    .row-divider { border-bottom: 1px solid #ebedef; padding: 12px 0; }
    .brand-title { font-family: 'Playfair Display', serif; font-size: 32px; font-weight: 800; color: #1a1a1a; margin-bottom: 5px; text-align: center; }
    .brand-sub { font-family: 'Playfair Display', serif; font-size: 18px; color: #444; margin-bottom: 30px; text-align: center; }
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

if 'res_df' not in st.session_state: st.session_state['res_df'] = pd.DataFrame()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

# --- 2. GIAO DIỆN ĐĂNG NHẬP ---
if not st.session_state['logged_in']:
    _, mid_col, _ = st.columns([1, 1.2, 1])
    with mid_col:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-title'>Data Vinhomes Smart City</div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-sub'>Liên hệ Admin Ninh - 0912.791.925</div>", unsafe_allow_html=True)
        u_val = st.text_input("Tài khoản").strip()
        p_val = st.text_input("Mật khẩu", type="password").strip()
        if st.button("Đăng nhập"):
            try:
                sh_u = doc.worksheet("QUAN_LY_USER")
                data = sh_u.get_all_values()
                users_df = pd.DataFrame(data[1:], columns=data[0])
                auth = users_df[(users_df['Username'].astype(str) == u_val) & (users_df['Password'].astype(str) == p_val)]
                if not auth.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = auth.iloc[0]['Tên nhân viên']
                    st.rerun()
                else: st.error("Tài khoản hoặc mật khẩu không đúng!")
            except Exception as e: st.error(f"Lỗi: {e}")
else:
    # --- 3. HEADER (XỬ LÝ THẲNG HÀNG) ---
    # Dùng markdown kết hợp columns để ép nút X nằm sát dòng chữ
    h_col1, h_col2 = st.columns([7, 3])
    with h_col2:
        st.markdown(f"""
            <div class="header-wrapper">
                <span style="font-size: 15px;">Xin chào <b>{st.session_state['user_name']}!</b></span>
                <div class="logout-btn-style">
        """, unsafe_allow_html=True)
        if st.button("❌", key="logout_btn"):
            st.session_state.clear()
            st.rerun()
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- 4. TẢI DỮ LIỆU ---
    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_vals = sh_data.get_all_values()
        h_names = raw_vals[0]
        df_main = pd.DataFrame(raw_vals[1:], columns=h_names)
        df_main = df_main.applymap(lambda x: str(x).strip() if x is not None else "")

        # --- 5. BỘ LỌC TABS ---
        tab_ma, tab_tieuchi = st.tabs(["🔍 Tìm nhanh", "📊 Lọc chi tiết"])

        with tab_ma:
            c_in, c_btn, _ = st.columns([2, 0.8, 3])
            with c_in:
                search_ma = st.text_input("Mã căn", key="input_ma", label_visibility="collapsed", placeholder="Nhập mã căn (VD: S1.01.10.20)...")
            with c_btn:
                if st.button("Tìm kiếm", key="btn_find_ma") or (search_ma and st.session_state.get('last_ma') != search_ma):
                    if search_ma:
                        st.session_state['last_ma'] = search_ma
                        res = df_main[df_main['Mã đầy đủ'].str.contains(search_ma.strip(), case=False)]
                        # THÔNG BÁO KHI KHÔNG TÌM THẤY
                        if res.empty:
                            st.toast(f"Không tìm thấy mã căn: {search_ma}", icon="⚠️")
                        st.session_state['res_df'] = res

        with tab_tieuchi:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            with c1: 
                ds_toa = sorted([t for t in df_main['Tòa'].unique() if t])
                sel_t = st.multiselect("Chọn Tòa", ds_toa)
            with c2: f_s = st.selectbox("Từ tầng", LIST_TANG_PHYSICAL, index=4)
            with c3: f_e = st.selectbox("Đến tầng", LIST_TANG_PHYSICAL, index=15)
            with c4: sel_tr = st.multiselect("Chọn Trục", LIST_TRUC)
            
            if st.button("🚀 Thực hiện lọc", key="btn_filter"):
                t_df = df_main.copy()
                if sel_t: t_df = t_df[t_df['Tòa'].isin(sel_t)]
                if sel_tr:
                    t_df['Trục_Clean'] = t_df['Trục'].apply(lambda x: x.replace(".0", "").zfill(2) if x else "")
                    t_df = t_df[t_df['Trục_Clean'].isin(sel_tr)]
                idx_s, idx_e = LIST_TANG_PHYSICAL.index(f_s), LIST_TANG_PHYSICAL.index(f_e)
                allowed = LIST_TANG_PHYSICAL[idx_s : idx_e + 1]
                t_df = t_df[t_df['Tầng'].isin(allowed)]
                if t_df.empty:
                    st.toast("Không tìm thấy căn hộ nào khớp với tiêu chí!", icon="ℹ️")
                st.session_state['res_df'] = t_df

        # --- 6. HIỂN THỊ DANH SÁCH ---
        res_display = st.session_state['res_df']
        if not res_display.empty:
            st.divider()
            st.success(f"Tìm thấy {len(res_display)} căn hộ.")
            cols_ui = st.columns([1, 1, 0.8, 0.6, 1.4, 2.2, 0.5])
            titles = ["Mã Căn", "Chủ Nhà", "Loại hình", "DT", "SĐT (Bấm xem)", "Ghi chú", "Lưu"]
            for ui, txt in zip(cols_ui, titles): ui.markdown(f"<div class='header-text'>{txt}</div>", unsafe_allow_html=True)

            for i, r in res_display.iterrows():
                row = st.columns([1, 1, 0.8, 0.6, 1.4, 2.2, 0.5])
                row[0].write(f"**{r['Mã đầy đủ']}**")
                row[1].write(r['Chủ nhà'])
                row[2].write(r.get('Loại hình', '-'))
                row[3].write(f"{r['Diện tích']}m²")
                
                s_key = f"v_{r['Mã đầy đủ']}"
                if s_key in st.session_state and st.session_state[s_key]:
                    row[4].code(r['Số điện thoại'], language="text")
                else:
                    sdt_raw = r['Số điện thoại']
                    prefix = sdt_raw[:-3] + "***" if len(sdt_raw) > 3 else "***"
                    if row[4].button(f"📞 {prefix}", key=f"btn_{i}"):
                        st.session_state[s_key] = True
                        st.rerun()
                
                n_val = row[5].text_input("G", value=r.get('Ghi chú', ''), key=f"in_{i}", label_visibility="collapsed")
                st.markdown('<div class="save-btn">', unsafe_allow_html=True)
                if row[6].button("💾", key=f"sv_{i}"):
                    try:
                        cell = sh_data.find(r['Mã đầy đủ'])
                        g_col = h_names.index('Ghi chú') + 1
                        sh_data.update_cell(cell.row, g_col, n_val)
                        st.toast(f"Đã lưu!", icon="✅")
                    except: st.error("Lỗi!")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)
        elif 'last_ma' in st.session_state and not res_display.empty:
             st.info("Nhập thông tin để xem kết quả.")

    except Exception as e: st.error(f"Lỗi: {e}")
