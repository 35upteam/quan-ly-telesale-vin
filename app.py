def init_connection():
    creds_info = st.secrets["gcp_service_account"]
    
    # Dòng này cực kỳ quan trọng: Tự động sửa lỗi xuống dòng trong private_key
    creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    client = gspread.authorize(creds)
    return client.open("Data Vin")
