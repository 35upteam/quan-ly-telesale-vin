import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH ---
st.set_page_config(page_title="Hệ thống Telesale Vin", layout="wide")

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
        st.error(f"Lỗi hệ thống: {e}")
        st.stop()

doc = init_connection()

# --- ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập")
    u = st.text_input("Tên đăng nhập")
    p = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
        sh_user = doc.worksheet("QUAN_LY_USER")
        u_df = pd.DataFrame(sh_user.get_all_records())
        auth = u_df[(u_df['Username'] == u) & (u_df['Password'].astype(str) == p)]
        if not auth.empty:
            st.session_state['logged_in'] = True
            st.session_state['user_name'] = u
            st.rerun()
        else:
            st.error("Sai thông tin!")
else:
    # --- GIAO DIỆN CHÍNH ---
    st.sidebar.write(f"Chào {st.session_state['user_name']}")
    if st.sidebar.button("Thoát"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("🏘️ Tra cứu Căn hộ")
    
    try:
        sh_data = doc.worksheet("DATA_CAN_HO")
        data = sh_data.get_all_records()
        if not data:
            st.warning("Tab DATA_CAN_HO đang trống dữ liệu!")
            st.stop()
        df = pd.DataFrame(data)
        
        # Lọc đơn giản
        dstoa = ["Tất cả"] + sorted(list(df['Tòa'].unique()))
        toa_sel = st.selectbox("Chọn Tòa", dstoa)
        f_df = df if toa_sel == "Tất cả" else df[df['Tòa'] == toa_sel]

        for i, r in f_df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**Căn:** {r['Mã đầy đủ']} | **Chủ:** {r['Chủ nhà']}")
                    st.write(f"📞 SĐT: `{str(r['Số điện thoại'])[:4]}.xxx.xxx`")
                with c2:
                    if st.button(f"Xem số", key=f"btn_{r['Mã đầy đủ']}"):
                        st.success(f"SĐT: {r['Số điện thoại']}")
                        # Ghi Log
                        sh_log = doc.worksheet("LOG_TRUY_CAP")
                        now = datetime.now().strftime("%H:%M %d/%m")
                        sh_log.append_row([now, st.session_state['user_name'], r['Mã đầy đủ']])
                        st.toast("Đã lưu lịch sử!")
    except gspread.exceptions.WorksheetNotFound:
        st.error("Không tìm thấy tab 'DATA_CAN_HO'. Hãy kiểm tra lại tên tab trong Google Sheets!")
    except Exception as e:
        st.error(f"Lỗi đọc dữ liệu: {e}")
