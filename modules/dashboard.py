import streamlit as st
import pandas as pd
from database import read_data

def render_dashboard():
    st.title("🔮 لوحة التحكم - VeeXia ERP")
    st.caption("مؤشرات الأداء الرئيسية والبيانات الحية")
    st.divider()

    df_products = read_data("Products")
    df_expenses = read_data("Expenses")

    total_items = len(df_products) if not df_products.empty else 0
    total_expenses = df_expenses["Amount"].sum() if not df_expenses.empty and "Amount" in df_expenses.columns else 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="📦 إجمالي الأصناف المسجلة", value=f"{total_items} صنف")
    with col2:
        st.metric(label="💰 إجمالي المصروفات", value=f"{total_expenses:,.2f} EGP")

    st.divider()
    st.subheader("📋 قائمة الأصناف الحالية")
    if not df_products.empty:
        st.dataframe(df_products, use_container_width=True)
    else:
        st.info("لا توجد بيانات أصناف لعرضها حالياً.")