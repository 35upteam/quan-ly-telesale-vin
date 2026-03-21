import streamlit as st
import pandas as pd
import re

# --- 1. CẤU HÌNH TRANG (PHẢI ĐỂ ĐẦU TIÊN) ---
st.set_page_config(page_title="PhanMemNhaDat - Smart City", layout="wide")

# --- 2. KIỂM TRA ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def check_login():
    st.title("🔐 Đăng nhập hệ thống")
    user = st.text_input("Tài khoản (admin)")
    pwd = st.text_input("Mật khẩu (123)", type="password")
    
    if st.button("Đăng nhập", type="primary"):
        if user == "admin" and pwd == "123":
            st.session_state['logged_in'] = True
            st.rerun() # Lệnh này cực kỳ quan trọng để làm mới trang
        else:
            st.error("Sai tài khoản hoặc mật khẩu")

# Nếu chưa đăng nhập thì dừng tại đây và hiện form login
if not st.session_state['logged_in']:
    check_login()
    st.stop() 

# --- 3. NỘI DUNG CHÍNH (CHỈ CHẠY KHI ĐÃ ĐĂNG NHẬP) ---

# --- DANH SÁCH DỮ LIỆU CHUẨN ---
LIST_TOA = [
    "S1.01", "S1.02", "S1.03", "S1.05", "S1.06", "S2.01", "S2.02", "S2.03", "S2.05", 
    "S3.01", "S3.02", "S3.03", "S4.01", "S4.02", "S4.03", "GS1", "GS2", "GS3", "GS5", "GS6", 
    "SA1", "SA2", "SA3", "SA5", "V1", "V2", "V3", "TK1", "TK2", "TC1", "TC2", "TC3", 
    "West A", "West B", "West C", "West D", "The Aura (A3)", "The Atmos (A2)", "The Aqua (A1)", 
    "I1", "I2", "I3", "I4", "I5", "G1", "G2", "G3", "G5", "G6"
]

LIST_TANG_LABEL = [
    "1", "2", "3", "05A", "05", "06", "07", "08", "08A", "09", "10", "11", "12", "12A", 
    "15A", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", 
    "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"
]

def get_numeric_floor(label):
    mapping = {"05A": 4, "12A": 13, "15A": 14, "12B": 14, "08A": 8.5, "25A": 24}
    if label in mapping: return mapping[label]
    try:
        num_part = re.sub("[^0-9]", "", str(label))
        return int(num_part)
    except: return 0

# --- DATA --- (Thay phần này bằng kết nối Google Sheets của bạn)
@st.cache_data
def load_data():
    data = {
        'MaCan': ['S3.03-0305A', 'S3.03-1015A', 'S3.03-2515', 'GS1-0508', 'TK1-2010'],
        'Toa': ['S3.03', 'S3.03', 'S3.03', 'GS1', 'TK1'],
        'Tang': ['05A', '10', '25', '05', '20'],
        'Truc': ['05A', '15A', '15', '08', '10'],
        'Gia': [2800, 3200, 3100, 2700, 5200],
        'DienTich': [43, 54, 55, 43, 70]
    }
    return pd.DataFrame(data)

df = load_data()

# --- GIAO DIỆN ---
st.title("🏙️ Quản lý & Lọc Căn Hộ Vinhomes Smart City")

# Nút Đăng xuất cho chuyên nghiệp
if st.sidebar.button("Đăng xuất"):
    st.session_state['logged_in'] = False
    st.rerun()

tab1, tab2 = st.tabs(["🔍 Tìm theo Mã căn", "📂 Lọc nâng cao"])

with tab1:
    search_ma = st.text_input("Nhập mã căn cụ thể", placeholder="Ví dụ: S3.03-0305A")
    if search_ma:
        res_ma = df[df['MaCan'].str.contains(search_ma, case=False)]
        st.dataframe(res_ma, use_container_width=True)

with tab2:
    with st.expander("Mở bộ lọc chi tiết", expanded=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
        with c1:
            toa_sel = st.selectbox("🏢 Chọn Tòa", options=["Tất cả"] + LIST_TOA)
        with c2:
            t_tu = st.selectbox("🔽 Tầng từ", options=LIST_TANG_LABEL, index=0)
        with c3:
            t_den = st.selectbox("🔼 Đến tầng", options=LIST_TANG_LABEL, index=len(LIST_TANG_LABEL)-1)
        with c4:
            truc_options = sorted(df['Truc'].unique().tolist())
            truc_sel = st.multiselect("🎯 Chọn Trục (Căn số)", options=truc_options)

    if st.button("🚀 Bắt đầu lọc", type="primary"):
        df['Tang_Num'] = df['Tang'].apply(get_numeric_floor)
        val_tu = get_numeric_floor(t_tu)
        val_den = get_numeric_floor(t_den)
        
        mask = (df['Tang_Num'] >= val_tu) & (df['Tang_Num'] <= val_den)
        if toa_sel != "Tất cả":
            mask &= (df['Toa'] == toa_sel)
        if truc_sel:
            mask &= (df['Truc'].isin(truc_sel))
            
        df_res = df[mask].drop(columns=['Tang_Num'])
        
        if not df_res.empty:
            st.success(f"Tìm thấy {len(df_res)} kết quả!")
            st.dataframe(df_res, use_container_width=True)
        else:
            st.warning("Không tìm thấy kết quả nào khớp với dữ liệu hiện tại.")
