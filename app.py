import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide")

# CSS làm đẹp giao diện Card và Button
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 8px; height: 35px; }
    .apartment-card {
        background-color: #ffffff; padding: 20px; border-radius: 15px;
        border: 1px solid #eaeaea; shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-bottom: 15px;
    }
    .info-label { color: #888; font-size: 0.8rem; margin-bottom: 2px; }
    .info-value { font-weight: 700; color: #333; font-size: 1rem; }
    .card-header { font-size: 1.2rem; font-weight: 800; color: #007bff; margin-bottom: 10px; }
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
        
        # FIX LỖI: Xử lý strip() an toàn cho từng cột
        for col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()

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
                
                # Logic lọc tầng theo thứ tự vật lý
                try:
                    i_s, i_e = LIST_TANG_PHYSICAL.index(f_start), LIST_TANG_PHYSICAL.index(f_end)
                    allowed = LIST_TANG_PHYSICAL[i_s : i_e + 1]
                    t_df = t_df[t_df['Tầng'].isin(allowed)]
                except: pass
                st.session_state['search_results'] = t_df

        # --- HIỂN THỊ DANH SÁCH ---
        res = st.session_state['search_results']
        if not res.empty:
            st.write(f"Tìm thấy **{len(res)}** căn hộ")
            for idx, r in res.iterrows():
                with st.container():
                    # Card hiển thị đẹp hơn
                    st.markdown(f'<div class="apartment-card"><div class="card-header">🏠 {r["Mã đầy đủ"]}</div>', unsafe_allow_html=True)
                    
                    c_info, c_note = st.columns([3, 2])
                    
                    with c_info:
                        i1, i2, i3 = st.columns(3)
                        i1.markdown(f"<div class='info-label'>Chủ nhà</div><div class='info-value'>{r.get('Chủ nhà','-')}</div>", unsafe_allow_html=True)
                        i2.markdown(f"<div class='info-label'>Loại hình</div><div class='info-value'>{r.get('Loại hình','-')}</div>", unsafe_allow_html=True)
                        i3.markdown(f"<div class='info-label'>Diện tích</div><div class='info-value'>{r.get('Diện tích','-')} m²</div>", unsafe_allow_html=True)
                        
                        st.write("")
                        cp1, cp2 = st.columns([2, 1])
                        sdt_key = f"view_{r['Mã đầy đủ']}"
                        
                        if sdt_key in st.session_state and st.session_state[sdt_key]:
                            cp1.code(r.get('Số điện thoại','-'), language="text")
                            if cp2.button("Đóng", key=f"h_{idx}"):
                                del st.session_state[sdt_key]; st.rerun()
                        else:
                            # Nút mở số điện thoại gọn gàng hơn
                            sdt_prefix = str(r.get('Số điện thoại',''))[:4]
                            if cp1.button(f"📋 Hiện số ({sdt_prefix}...)", key=f"v_{idx}"):
                                st.session_state[sdt_key] = True; st.rerun()
                    
                    with c_note:
                        current_note = r.get('Ghi chú', '')
                        new_note = st.text_area("Ghi chú nội bộ", value=current_note, key=f"n_{idx}", height=85)
                        if st.button("💾 Lưu ghi chú", key=f"s_{idx}"):
                            try:
                                # Cập nhật trực tiếp lên Sheet
                                cell = sh_data.find(r['Mã đầy đủ'])
                                header = raw[0]
                                if 'Ghi chú' in header:
                                    col_idx = header.index('Ghi chú') + 1
                                    sh_data.update_cell(cell.row, col_idx, new_note)
                                    st.toast("Đã lưu thành công!", icon="✅")
                                else:
                                    st.error("Sheet thiếu cột 'Ghi chú'!")
                            except Exception as e:
                                st.error(f"Lỗi lưu: {e}")
                    st.markdown('</div>', unsafe_allow_html=True) # Kết thúc div card

    except Exception as e:
        st.error(f"Lỗi: {e}")
