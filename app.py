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
    .row-divider { border-bottom: 1px solid #f0f2f6; padding: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# Danh sách chuẩn
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
if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập hệ thống")
    u = st.text_input("Tài khoản").strip()
    p = st.text_input("Mật khẩu", type="password").strip()
    if st.button("Đăng nhập"):
        try:
            sh_u = doc.worksheet("QUAN_LY_USER")
            users = pd.DataFrame(sh_u.get_all_records())
            # FIX LỖI: Sử dụng .empty thay vì so sánh trực tiếp dataframe
            auth_check = users[(users['Username'].astype(str) == u) & (users['Password'].astype(str) == p)]
            if not auth_check.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = u
                st.rerun()
            else:
                st.error("Sai tài khoản hoặc mật khẩu!")
        except:
            st.error("Lỗi truy cập dữ liệu User!")
else:
    # --- 3. BỘ LỌC DỮ LIỆU ---
    st.sidebar.write(f"👤 Chào: **{st.session_state['user_name']}**")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.clear()
        st.rerun()

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_data = sh_data.get_all_values()
        header_names = raw_data[0]
        df_full = pd.DataFrame(raw_data[1:], columns=header_names)
        
        for col in df_full.columns:
            df_full[col] = df_full[col].apply(lambda x: str(x).strip() if x else "")

        c1, c2, c3, c4 = st.columns([1, 1, 1, 1.5])
        with c1: 
            ds_toa = sorted([t for t in df_full['Tòa'].unique() if t])
            sel_toa = st.multiselect("Chọn Tòa", ds_toa)
        with c2: f_s = st.selectbox("Từ tầng", LIST_TANG_PHYSICAL, index=4)
        with c3: f_e = st.selectbox("Đến tầng", LIST_TANG_PHYSICAL, index=15)
        with c4: sel_tr = st.multiselect("Chọn Trục", LIST_TRUC)

        if st.button("🚀 Thực hiện lọc"):
            temp_df = df_full.copy()
            # Sử dụng len() để tránh lỗi Ambiguous
            if len(sel_toa) > 0:
                temp_df = temp_df[temp_df['Tòa'].isin(sel_toa)]
            if len(sel_tr) > 0:
                temp_df = temp_df[temp_df['Trục'].isin(sel_tr)]
            
            idx_s = LIST_TANG_PHYSICAL.index(f_s)
            idx_e = LIST_TANG_PHYSICAL.index(f_e)
            allowed_floors = LIST_TANG_PHYSICAL[idx_s : idx_e + 1]
            temp_df = temp_df[temp_df['Tầng'].isin(allowed_floors)]
            st.session_state['res_df'] = temp_df

        # --- 4. HIỂN THỊ DANH SÁCH ---
        res_display = st.session_state['res_df']
        
        if not res_display.empty:
            st.divider()
            # Header hàng ngang
            h_cols = st.columns([1, 1, 0.6, 1.5, 2.5, 0.6])
            labels = ["Mã Căn", "Chủ Nhà", "DT", "SĐT (Bấm 👁️)", "Ghi chú", "Lưu"]
            for ui_col, lb in zip(h_cols, labels):
                ui_col.markdown(f"<div class='header-text'>{lb}</div>", unsafe_allow_html=True)

            for i, r in res_display.iterrows():
                r_cols = st.columns([1, 1, 0.6, 1.5, 2.5, 0.6])
                r_cols[0].write(f"**{r['Mã đầy đủ']}**")
                r_cols[1].write(r['Chủ nhà'])
                r_cols[2].write(f"{r['Diện tích']}m²")
                
                # Cột SĐT & Copy
                sdt_view_key = f"v_{r['Mã đầy đủ']}"
                if sdt_view_key in st.session_state and st.session_state[sdt_view_key]:
                    # Sử dụng st.code để có sẵn nút Copy mặc định của Streamlit
                    r_cols[3].code(r['Số điện thoại'], language="text")
                else:
                    sdt_pre = r['Số điện thoại'][:4] if len(r['Số điện thoại']) > 4 else "0xxx"
                    if r_cols[3].button(f"👁️ {sdt_pre}...", key=f"btn_{i}"):
                        st.session_state[sdt_view_key] = True
                        st.rerun()
                
                # Ghi chú & Nút Lưu
                n_input = r_cols[4].text_input("Note", value=r.get('Ghi chú', ''), key=f"in_{i}", label_visibility="collapsed")
                if r_cols[5].button("💾", key=f"sv_{i}"):
                    try:
                        cell = sh_data.find(r['Mã đầy đủ'])
                        if 'Ghi chú' in header_names:
                            g_idx = header_names.index('Ghi chú') + 1
                            sh_data.update_cell(cell.row, g_idx, n_input)
                            st.toast(f"Đã cập nhật!", icon="✅")
                        else:
                            st.error("Sheet thiếu cột 'Ghi chú'")
                    except:
                        st.error("Lỗi lưu!")
                st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)
        
        elif len(st.session_state['res_df']) == 0 and 'res_df' in st.session_state:
            st.info("Sử dụng bộ lọc để xem danh sách căn hộ.")

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
