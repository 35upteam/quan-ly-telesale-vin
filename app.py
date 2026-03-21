import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Quản lý Giỏ hàng Smart City", layout="wide")

st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 8px; font-weight: 600; height: 38px; }
    .apartment-card {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        border-left: 5px solid #007bff; border-right: 1px solid #eee;
        border-top: 1px solid #eee; border-bottom: 1px solid #eee;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .label { color: #6c757d; font-size: 0.8rem; margin-bottom: 2px; }
    .value { font-weight: 700; color: #333; font-size: 1rem; }
    .title-card { font-size: 1.2rem; font-weight: 800; color: #007bff; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# Danh sách chuẩn
LIST_TRUC = [f"{i:02d}" for i in range(1, 31)]
LIST_TANG_PHYSICAL = ["1", "2", "3", "05A", "05", "06", "07", "08", "08A", "09", "10", "11", "12", "12A", "15A", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]

# --- 2. KẾT NỐI DỮ LIỆU ---
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
        st.error(f"Kết nối thất bại: {e}")
        return None

doc = init_connection()

if 'res_df' not in st.session_state: 
    st.session_state['res_df'] = pd.DataFrame()
if 'logged_in' not in st.session_state: 
    st.session_state['logged_in'] = False

# --- 3. LOGIC ĐĂNG NHẬP ---
if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập hệ thống")
    u_input = st.text_input("Tên đăng nhập")
    p_input = st.text_input("Mật khẩu", type="password")
    if st.button("Xác nhận"):
        try:
            sh_u = doc.worksheet("QUAN_LY_USER")
            users = pd.DataFrame(sh_u.get_all_records())
            # Chuyển về string để so sánh
            users['Username'] = users['Username'].astype(str).str.strip()
            users['Password'] = users['Password'].astype(str).str.strip()
            
            check = users[(users['Username']==u_input.strip()) & (users['Password']==p_input.strip())]
            if not check.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = u_input
                st.rerun()
            else:
                st.error("Sai tài khoản hoặc mật khẩu!")
        except Exception as e:
            st.error(f"Lỗi xác thực: {e}")
else:
    # --- 4. GIAO DIỆN CHÍNH ---
    st.sidebar.write(f"👤 Chào: **{st.session_state['user_name']}**")
    if st.sidebar.button("Thoát hệ thống"):
        st.session_state.clear()
        st.rerun()

    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw_values = sh_data.get_all_values()
        header = raw_values[0]
        df = pd.DataFrame(raw_values[1:], columns=header)
        
        # Làm sạch dữ liệu an toàn
        for col in df.columns:
            df[col] = df[col].apply(lambda x: str(x).strip() if x is not None else "")

        t1, t2 = st.tabs(["🔍 Tìm mã căn", "⚙️ Lọc thông minh"])
        
        with t1:
            m_find = st.text_input("Nhập mã căn (VD: S1.02-15-05)").strip()
            if st.button("Tìm ngay"):
                st.session_state['res_df'] = df[df['Mã đầy đủ'].str.contains(m_find, case=False, na=False)]

        with t2:
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])
            with c1: 
                ds_toa = sorted([t for t in df['Tòa'].unique() if t])
                sel_toa = st.multiselect("Chọn Tòa", ds_toa)
            with c2: 
                f_start = st.selectbox("Từ tầng", LIST_TANG_PHYSICAL, index=4)
            with c3: 
                f_end = st.selectbox("Đến tầng", LIST_TANG_PHYSICAL, index=15)
            with c4: 
                sel_tr = st.multiselect("Chọn Trục", LIST_TRUC)
            
            if st.button("🚀 Thực hiện lọc"):
                temp = df.copy()
                if sel_toa: temp = temp[temp['Tòa'].isin(sel_toa)]
                if sel_tr: temp = temp[temp['Trục'].isin(sel_tr)]
                
                # Logic lọc tầng
                try:
                    idx_s = LIST_TANG_PHYSICAL.index(f_start)
                    idx_e = LIST_TANG_PHYSICAL.index(f_end)
                    allowed_t = LIST_TANG_PHYSICAL[idx_s : idx_e + 1]
                    temp = temp[temp['Tầng'].isin(allowed_t)]
                except:
                    pass
                st.session_state['res_df'] = temp

        # --- 5. HIỂN THỊ KẾT QUẢ ---
        res = st.session_state['res_df']
        if not res.empty:
            st.write(f"Đã tìm thấy **{len(res)}** căn hộ phù hợp.")
            
            for i, r in res.iterrows():
                # Card HTML
                st.markdown(f'<div class="apartment-card"><div class="title-card">🏠 {r["Mã đầy đủ"]}</div>', unsafe_allow_html=True)
                
                col_left, col_right = st.columns([3, 2])
                
                with col_left:
                    # Thông tin
                    i1, i2, i3 = st.columns(3)
                    i1.markdown(f"<div class='label'>Chủ nhà</div><div class='value'>{r.get('Chủ nhà','-')}</div>", unsafe_allow_html=True)
                    i2.markdown(f"<div class='label'>Loại hình</div><div class='value'>{r.get('Loại hình','-')}</div>", unsafe_allow_html=True)
                    i3.markdown(f"<div class='label'>Diện tích</div><div class='value'>{r.get('Diện tích','-')} m²</div>", unsafe_allow_html=True)
                    
                    st.write("---")
                    # SĐT
                    p1, p2 = st.columns([2, 1])
                    key_show = f"view_{r['Mã đầy đủ']}"
                    
                    if key_show in st.session_state and st.session_state[key_show]:
                        p1.code(r.get('Số điện thoại','-'), language="text")
                        if p2.button("Ẩn số", key=f"hide_{i}"):
                            del st.session_state[key_show]
                            st.rerun()
                    else:
                        sdt_prefix = str(r.get('Số điện thoại',''))[:4]
                        if p1.button(f"📋 Hiện SĐT ({sdt_prefix}...)", key=f"show_{i}"):
                            st.session_state[key_show] = True
                            st.rerun()
                
                with col_right:
                    # Ghi chú
                    note_val = r.get('Ghi chú', '')
                    new_note = st.text_area("Ghi chú nội bộ", value=note_val, key=f"txt_{i}", height=80)
                    if st.button("💾 Lưu lại", key=f"save_{i}"):
                        try:
                            cell = sh_data.find(r['Mã đầy đủ'])
                            if 'Ghi chú' in header:
                                col_idx = header.index('Ghi chú') + 1
                                sh_data.update_cell(cell.row, col_idx, new_note)
                                st.toast("Đã cập nhật ghi chú!", icon="✅")
                            else:
                                st.error("Thiếu cột 'Ghi chú' trên Sheet!")
                        except Exception as e:
                            st.error(f"Lỗi lưu: {e}")
                
                st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Phát sinh lỗi hệ thống: {e}")
