import streamlit as st
import pandas as pd
import gspread

st.set_page_config(page_title="VeeXia ERP System", page_icon="🏭", layout="wide")

st.markdown(
    """
    <div style="background-color: #800020; padding: 15px; border-radius: 5px; margin-bottom: 25px;">
        <h1 style="color: white; text-align: center; margin: 0; font-size: 26px;">VeeXia ERP System - الأصناف والمخزون</h1>
    </div>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def init_connection():
  try:
    if "gcp_service_account" not in st.secrets:
      return None
    creds_dict = dict(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(creds_dict)
    return client.open("VeeXia_ERP_DB")
  except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    return None


db = init_connection()

if db is not None:
  try:
    worksheets = db.worksheets()
    ws_titles = [ws.title for ws in worksheets]

    if ws_titles:
      st.sidebar.markdown("### 📂 الشيتات المتاحة")
      selected_sheet = st.sidebar.selectbox(
          "اختر التبويب لعرض الأصناف:", ws_titles
      )

      if selected_sheet:
        ws = db.worksheet(selected_sheet)
        data = ws.get_all_values()

        st.markdown(f"### 📋 محتويات جدول: `{selected_sheet}`")

        if len(data) > 0:
          headers = data[0]
          rows = data[1:] if len(data) > 1 else []
          df = pd.DataFrame(rows, columns=headers if rows else None)
          df = df.dropna(how="all")

          st.success(
              f"تم بنجاح جلب عدد **{len(df)}** صنف/سجل من جدول `{selected_sheet}`"
          )
          st.dataframe(df, use_container_width=True)
        else:
          st.info("هذا التبويب فارغ حالياً.")
    else:
      st.warning("لا توجد تبويبات داخل ملف جوجل شيت.")
  except Exception as e:
    st.error(f"حدث خطأ أثناء جلب البيانات: {e}")
else:
    st.warning("تعذر الاتصال بقاعدة البيانات. تأكد من إعدادات الـ Secrets.")
