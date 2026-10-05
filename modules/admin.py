import streamlit as st
from database import read_data

def render_admin_panel():
    st.title("🛡️ لوحة تحكم الأدمن")
    st.divider()

    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if not st.session_state["admin_logged_in"]:
        st.subheader("🔐 تسجيل دخول الأدمن")
        with st.form("admin_login_form"):
            admin_user = st.text_input("اسم المستخدم")
            admin_pass = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                if admin_user == "admin" and admin_pass == "veexia2026":
                    st.session_state["admin_logged_in"] = True
                    st.success("تم الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة!")
        return

    st.success("مرحباً بك يا مدير النظام!")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state["admin_logged_in"] = False
        st.rerun()