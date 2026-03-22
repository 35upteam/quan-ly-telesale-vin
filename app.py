import streamlit as st
import pandas as pd
import gspread
import time 
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH & CSS (GIỮ NGUYÊN BẢN BẠN ƯNG Ý) ---
st.set_page_config(page_title="Quản lý Giỏ hàng Vin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap');
    [data-testid="stSidebar"] { display: none; }
    
    .brand-title { 
        font-family: 'Playfair Display', serif; 
        font-size: 32px; 
        font-weight: 800; color: #1a1a1a; 
        margin-bottom: 10px; 
        text-align: center;
        line-height: 1.2;
    }
    .brand-sub { 
        font-family: 'Playfair Display', serif; 
        font-size: 18px; color: #444; 
        margin-bottom: 30px; 
        text-align: center; 
    }

    @media (max-width: 768
