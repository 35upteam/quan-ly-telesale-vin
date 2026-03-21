import streamlit as st
import pandas as pd
import re

# --- 1. CẤU HÌNH DANH SÁCH DỮ LIỆU CHUẨN VINHOMES SMART CITY ---
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

# --- 2. HÀM LOGIC ÁNH XẠ TẦNG (MAPPING) ---
def get_numeric_floor(label):
    """
    Chuyển ký hiệu tầng sang số nguyên để máy tính so sánh được lớn/nhỏ.
    Ví dụ: 05A -> 4, 12A -> 13, 15A -> 14.
    """
    mapping = {
        "05A": 4,
        "12A": 13,
        "15A": 14,
        "12B": 14,
        "08A": 8.5, # Để 8A nằm giữa 8 và 9 nếu cần
        "25A": 24
    }
    if label in mapping:
        return mapping[label]
    try:
        # Tách phần số từ chuỗi (loại bỏ chữ A, B nếu có mà không nằm trong mapping)
        num_part = re.sub("[^0-9]", "", str(label))
        return int(num_part)
    except:
        return 0

# --- 3. GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="PhanMemNhaDat - Vinhomes Smart City", layout="wide")

# Tiêu đề ứng dụng
st.title("🏙️ Quản lý & Lọc Căn Hộ Vinhomes Smart City")

# --- PHẦN BỘ LỌC NÂNG CAO ---
st.subheader("🔍 Lọc nâng cao")
with st.expander("Mở bộ lọc chi tiết", expanded=True):
    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
    
    with col1:
        toa_selection = st.selectbox("🏢 Chọn Tòa", options=["Tất cả"] + LIST_TOA)
        
    with col2:
        tang_tu_label = st.selectbox("🔽 Tầng từ", options=LIST_TANG_LABEL, index=0)
        
    with col3:
        tang_den_label = st.selectbox("🔼 Đến tầng", options=LIST_TANG_LABEL, index=len(LIST_TANG_LABEL)-1)
        
    with col4:
        # Danh sách trục căn mẫu (Bạn có thể lấy từ dữ liệu thực tế)
        truc_options = ["01", "02", "03", "05A", "05", "06", "08", "08A", "09", "10", "11", "12", "12A", "15", "15A", "16"]
        truc_selection = st.multiselect("🎯 Chọn Trục (Căn số)", options=truc_options)

# Nút bấm bắt đầu lọc
btn_loc = st.button("🚀 Bắt đầu lọc", type="primary")

# --- 4. XỬ LÝ DỮ LIỆU ---
# Giả sử bạn đọc dữ liệu từ Google Sheets:
# df = conn.read(spreadsheet="URL_OR_ID", worksheet="Sheet1")
# Dưới đây là dữ liệu mẫu để bạn test:
data_sample = {
    'Toa': ['S1.01', 'S1.01', 'GS1', 'GS1', 'S2.02', 'S4.01', 'TK1'],
    'Tang': ['05A', '12A', '20', '30', '15A', '08', '25'],
    'Truc': ['08A', '02', '10', '08', '05', '12', '15A'],
    'Gia': [2500, 3100, 2800, 4500, 3200, 2900, 5000],
    'DienTich': [43, 55, 43, 75, 54, 48, 65]
}
df = pd.DataFrame(data_sample)

if btn_loc:
    # Bước 1: Tạo cột số tạm thời từ cột Tang (dạng 12A, 05A) trong database
    df['Tang_Numeric'] = df['Tang'].apply(get_numeric_floor)
    
    # Bước 2: Lấy giá trị số của lựa chọn người dùng
    val_tu = get_numeric_floor(tang_tu_label)
    val_den = get_numeric_floor(tang_den_label)
    
    # Bước 3: Áp dụng các điều kiện lọc
    # Lọc theo tầng (So sánh số)
    mask = (df['Tang_Numeric'] >= val_tu) & (df['Tang_Numeric'] <= val_den)
    
    # Lọc theo tòa
    if toa_selection != "Tất cả":
        mask &= (df['Toa'] == toa_selection)
        
    # Lọc theo trục
    if truc_selection:
        mask &= (df['Truc'].isin(truc_selection))
        
    df_filtered = df[mask].copy()

    # --- 5. HIỂN THỊ KẾT QUẢ ---
    if not df_filtered.empty:
        st.success(f"✅ Tìm thấy {len(df_filtered)} căn hộ phù hợp!")
        
        # Xóa cột số tạm thời trước khi hiển thị cho người dùng
        display_df = df_filtered.drop(columns=['Tang_Numeric'])
        
        # Định dạng hiển thị giá và diện tích cho đẹp
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("⚠️ Không tìm thấy kết quả nào. Vui lòng điều chỉnh lại bộ lọc.")

# --- PHẦN THỐNG KÊ NHANH (Tùy chọn) ---
if not btn_loc:
    st.info("💡 Mẹo: Bạn có thể lọc nhanh theo tầng từ 05A đến 12A để tìm các căn tầng thấp và trung bình.")
