import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide")

# CSS làm đẹp giao diện
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 8px; transition: 0.3s; }
    .apartment-card {
        background-color: white; padding: 15px; border-radius: 12px;
        border: 1px solid #e6e9ef; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .info-label { color: #6c757d; font-size: 0.85rem; }
    .info-value { font-weight: 600; color: #1f2d3d; }
    </style>
    """, unsafe_allow_html=True)

LIST_TRUC = [f"{i:02d}" for i in range(1, 31)]
LIST_TANG_PHYSICAL = ["1", "2", "3", "05A", "05", "06", "07", "08", "08A", "09", "10", "11", "12", "12A", "15A", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]

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
        st.error(f"Lỗi kết nối: {e}"); st.stop()

doc = init_connection()

if 'search_results' not in st.session_state: st.session_state['search_results'] = pd.DataFrame()

# --- ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Hệ thống Nội bộ")
    u = st.text_input("Tài khoản")
    p = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
        try:
            sh_u = doc.worksheet("QUAN_LY_USER")
            u_df = pd.DataFrame(sh_u.get_all_records())
            if not u_df[(u_df['Username'].astype(str)==u) & (u_df['Password'].astype(str)==p)].empty:
                st.session_state['logged_in'] = True; st.session_state['user_name'] = u; st.rerun()
            else: st.error("Sai thông tin!")
        except: st.error("Lỗi xác thực người dùng.")
else:
    st.sidebar.write(f"👤 Chào {st.session_state['user_name']}")
    if st.sidebar.button("Đăng xuất"): st.session_state.clear(); st.rerun()

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw = sh_data.get_all_values()
        df = pd.DataFrame(raw[1:], columns=raw[0])
        
        # SỬA LỖI TẠI ĐÂY: Ép kiểu string cho từng cột thay vì cả DataFrame
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()

        tab1, tab2 = st.tabs(["🔍 Tìm mã cụ thể", "🛠️ Bộ lọc chuyên sâu"])
        
        with tab1:
            m_in = st.text_input("Nhập mã (VD: S1.02-15-05)")
            if st.button("Tìm nhanh"):
                st.session_state['search_results'] = df[df['Mã đầy đủ'].str.contains(m_in, case=False, na=False)]

        with tab2:
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])
            with c1: 
                toas = sorted([x for x in df['Tòa'].unique() if x])
                sel_t = st.multiselect("Tòa", toas)
            with c2: f_start = st.selectbox("Từ tầng", LIST_TANG_PHYSICAL, index=0)
            with c3: f_end = st.selectbox("Đến tầng", LIST_TANG_PHYSICAL, index=len(LIST_TANG_PHYSICAL)-1)
            with c4: sel_tr = st.multiselect("Trục căn", LIST_TRUC)
            
            if st.button("⚡ Lọc danh sách"):
                t_df = df.copy()
                if sel_t: t_df = t_df[t_df['Tòa'].isin(sel_t)]
                if sel_tr: t_df = t_df[t_df['Trục'].isin(sel_tr)]
                
                i_s, i_e = LIST_TANG_PHYSICAL.index(f_start), LIST_TANG_PHYSICAL.index(f_end)
                allowed = LIST_TANG_PHYSICAL[i_s : i_e + 1]
                t_df = t_df[t_df['Tầng'].isin(allowed)]
                st.session_state['search_results'] = t_df

        # --- HIỂN THỊ DANH SÁCH ---
        res = st.session_state['search_results']
        if not res.empty:
            st.write(f"Tìm thấy **{len(res)}** kết quả")
            for idx, r in res.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="apartment-card">
                        <span style="font-size:1.1rem; font-weight:bold; color:#007bff;">🏠 {r['Mã đầy đủ']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_info, col_note = st.columns([3, 2])
                    with col_info:
                        i1, i2, i3 = st.columns(3)
                        i1.markdown(f"<div class='info-label'>Chủ nhà</div><div class='info-value'>{r.get('Chủ nhà','-')}</div>", unsafe_allow_html=True)
                        i2.markdown(f"<div class='info-label'>Loại hình</div><div class='info-value'>{r.get('Loại hình','-')}</div>", unsafe_allow_html=True)
                        i3.markdown(f"<div class='info-label'>Diện tích</div><div class='info-value'>{r.get('Diện tích','-')} m²</div>", unsafe_allow_html=True)
                        
                        st.write("")
                        c_p1, c_p2 = st.columns([2, 1])
                        sdt_key = f"view_{r['Mã đầy đủ']}"
                        if sdt_key in st.session_state and st.session_state[sdt_key]:
                            c_p1.code(r.get('Số điện thoại','-'), language="text")
                            if c_p2.button("Đóng", key=f"hide_{idx}"):
                                del st.session_state[sdt_key]; st.rerun()
                        else:
                            sdt_show = str(r.get('Số điện thoại',''))[:4] + "..."
                            if c_p1.button(f"🔓 Hiện số ({sdt_show})", key=f"btn_v_{idx}"):
                                st.session_state[sdt_key] = True; st.rerun()
                    
                    with col_note:
                        current_note = r.get('Ghi chú', '')
                        new_note = st.text_area("Ghi chú", value=current_note, key=f"note_{idx}", height=68)
                        if st.button("💾 Lưu", key=f"save_{idx}"):
                            try:
                                cell = sh_data.find(r['Mã đầy đủ'])
                                col_index = raw[0].index('Ghi chú') + 1
                                sh_data.update_cell(cell.row, col_index, new_note)
                                st.toast("Đã lưu ghi chú!", icon="✅")
                            except:
                                st.error("Không tìm thấy cột 'Ghi chú' trên Sheet!")

        elif 'search_results' in st.session_state and not st.session_state['search_results'].empty:
            pass # Tránh hiện lỗi khi mới khởi động

    except Exception as e:
        st.error(f"Lỗi: {e}")
