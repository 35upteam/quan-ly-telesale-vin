def init_connection():
    try:
        # 1. Lấy dữ liệu từ Secrets và tạo một bản sao (dict) để có thể chỉnh sửa
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # 2. Xử lý lỗi ký tự xuống dòng trên bản sao này
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # 3. Sử dụng bản sao đã sửa để kết nối
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        return client.open("Data Vin")
    except Exception as e:
        st.error(f"Lỗi kết nối Secrets: {e}")
        return None
