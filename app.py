import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide")

st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 4px; height: 30px; font-size: 12px; }
    .header-text { font-weight: bold; color: #1f2d3d; border-bottom: 2px solid #dee2e6; padding-bottom: 5px; }
    .row-style { padding: 8px 0; border-bottom: 1px solid #eee; }
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

# --- 2. ĐĂNG NHẬP ---
if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập")
    u = st.text_input("Tài khoản").strip()
    p = st.text_input("Mật khẩu", type="password").strip()
    if st.button("Đăng nhập"):
        try:
            sh_u = doc.worksheet("QUAN_LY_USER")
            users = pd.DataFrame(sh_u.get_all_records())
            # FIX LỖI: Sử dụng .empty thay vì so sánh trực tiếp dataframe
            auth = users[(users['Username'].astype(str) == u) & (users['Password'].astype(str) == p)]
            if not auth.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = u
                st.rerun()
            else:
                st.error("Sai thông tin đăng nhập!")
        except:
            st.error("Lỗi truy cập dữ liệu người dùng!")
else:
    # --- 3. BỘ LỌC ---
    st.sidebar.write(f"👤 {st.session_state['user_name']}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.clear()
        st.rerun()

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw = sh_data.get_all_values()
        header = raw[0]
        df = pd.DataFrame(raw[1:], columns=header)
        
        for col in df.columns:
            df[col] = df[col].apply(lambda x: str(x).strip() if x else "")

        c1, c2, c3, c4 = st.columns([1, 1, 1, 1.5])
        with c1: 
            sel_toa = st.multiselect("Tòa", sorted([t for t in df['Tòa'].unique() if t]))
        with c2: f_s = st.selectbox("Từ tầng", LIST_TANG_PHYSICAL, index=4)
        with c3: f_e = st.selectbox("Đến tầng", LIST_TANG_PHYSICAL, index=15)
        with c4: sel_tr = st.multiselect("Trục", LIST_TRUC)

        if st.button("🚀 Lọc danh sách"):
            temp = df.copy()
            # Lọc an toàn
            if len(sel_toa) > 0:
                temp = temp[temp['Tòa'].isin(sel_toa)]
            if len(sel_tr) > 0:
                temp = temp[temp['Trục'].isin(sel_tr)]
            
            idx_s, idx_e = LIST_TANG_PHYSICAL.index(f_s), LIST_TANG_PHYSICAL.index(f_e)
            temp = temp[temp['Tầng'].isin(LIST_TANG_PHYSICAL[idx_s:idx_e+1])]
            st.session_state['res_df'] = temp

        # --- 4. DANH SÁCH BẢNG NGANG ---
        res = st.session_state['res_df']
        if not res.empty:
            st.divider()
            # Header
            h = st.columns([1, 1, 0.6, 1.3, 2.5, 0.6])
            cols = ["Mã Căn", "Chủ Nhà", "DT", "SĐT (Bấm mắt)", "Ghi chú nội bộ", "Lưu"]
            for ui, name in zip(h, cols):
                ui.markdown(f"<div class='header-text'>{name}</div>", unsafe_allow_html=True)

            for i, r in res.iterrows():
                row = st.columns([1, 1, 0.6, 1.3, 2.5, 0.6])
                row[0].write(r['Mã đầy đủ'])
                row[1].write(r['Chủ nhà'])
                row[2].write(f"{r['Diện tích']}m²")
                
                # SĐT & Copy
                sdt_key = f"v_{r['Mã đầy đủ']}"
                if sdt_key in st.session_state and st.session_state[sdt_key]:
                    row[3].code(r['Số điện thoại'], language="text")
                else:
                    sdt_prefix = r['Số điện thoại'][:4] if len(r['Số điện thoại']) > 4 else "0xxx"
                    if row[3].button(f"👁️ {sdt_prefix}...", key=f"btn_{i}"):
                        st.session_state[sdt_key] = True
                        st.rerun()
                
                # Ghi chú & Nút lưu
                n_input = row[4].text_input("Ghi chú", value=r.get('Ghi chú', ''), key=f"in_{i}", label_visibility="collapsed")
                if row[5].button("💾", key=f"sv_{i}"):
                    try:
                        cell = sh_data.find(r['Mã đầy đủ'])
                        if 'Ghi chú' in header:
                            col_idx = header.index('Ghi chú') + 1
                            sh_data.update_cell(cell.row, col_idx, n_input)
                            st.toast(f"Đã lưu!", icon="✅")
                        else:
                            st.error("Sheet thiếu cột 'Ghi chú'")
                    except:
                        st.error("Lỗi lưu!")
        
        elif len(st.session_state['res_df']) == 0 and 'res_df' in st.session_state:
            st.write("Chọn thông số và bấm Lọc để xem dữ liệu.")

    except Exception as e:
        st.error(f"Lỗi: {e}")
