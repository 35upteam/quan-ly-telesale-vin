def init_connection():
    creds_info = st.secrets["gcp_service_account"]
    # Đảm bảo dòng này lùi vào đúng bằng các dòng khác
    creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    client = gspread.authorize(creds)
    return client.open("Data Vin")
