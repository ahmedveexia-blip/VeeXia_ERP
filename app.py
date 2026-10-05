from datetime import datetime
import io
import gspread
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="VeeXia ERP System",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# تصميم عصري واحترافي بالكامل (UI/UX Styling)
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&display=swap');
    
    * { font-family: 'Cairo', sans-serif !important; }
    
    .stApp { 
        background-color: #f4f6f9; 
    }
    
    /* الشريط العلوي */
    .topbar { 
        background: linear-gradient(135deg, #7d2c42 0%, #5c2031 100%); 
        color: white; 
        padding: 18px 25px; 
        border-radius: 14px; 
        margin-bottom: 25px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
        box-shadow: 0 4px 20px rgba(125, 44, 66, 0.15);
    }
    
    .topbar h3 {
        margin: 0;
        font-weight: 700;
        font-size: 1.4rem;
        letter-spacing: 0.5px;
    }
    
    .topbar span {
        background: rgba(255, 255, 255, 0.15);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
    }

    /* الأزرار العصرية */
    .stButton>button { 
        background: linear-gradient(135deg, #7d2c42 0%, #632235 100%); 
        color: white; 
        border-radius: 10px; 
        font-weight: 600; 
        padding: 0.6rem 1rem;
        border: none;
        box-shadow: 0 3px 10px rgba(125, 44, 66, 0.2);
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover { 
        background: linear-gradient(135deg, #5c2031 0%, #421622 100%); 
        box-shadow: 0 5px 15px rgba(125, 44, 66, 0.35);
        transform: translateY(-1px);
    }

    /* تنسيق الحقول والجداول */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        background-color: #ffffff;
    }

    /* كروت لوحة التحكم */
    .dashboard-card {
        background: white;
        padding: 20px;
        border-radius: 14px;
        box
