import streamlit as st
import pandas as pd
import gspread

st.set_page_config(
    page_title="VeeXia ERP System", page_icon="🏭", layout="wide"
)

# هيدر النظام
st.markdown(
    """
    <div style="background-color: #800020; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <h1 style="color: white; text-align: center; margin: 0; font-size: 24px;">VeeXia ERP System - إدارة المخزون والأصناف</h1>
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

if db is None:
  st.error("⚠️ تعذر الاتصال بقاعدة بيانات Google Sheets. تأكد من إعدادات الـ Secrets.")
else:
  try:
    # جلب التبويبات المتاحة
    worksheets = db.worksheets()
    ws_titles = [ws.title for ws in worksheets]

    if ws_titles:
      # اختيار الشيت من القائمة الجانبية
      st.sidebar.markdown("### 📂 الشيتات المتاحة")
      selected_sheet = st.sidebar.selectbox("اختر الشيت لعرضه:", ws_titles)

      st.markdown(f"### 📦 المخزون والأرصدة الحالية - جدول: `{selected_sheet}`")

      # جلب البيانات بدون كاش قديم لضمان ظهور التحديثات فوراً
      ws = db.worksheet(selected_sheet)
      data = ws.get_all_values()

      if len(data) > 0:
        headers = data[0]
        rows = data[1:] if len(data) > 1 else []
        df = pd.DataFrame(rows, columns=headers if rows else None)
        df = df.dropna(how="all")

        # عرض الجدول بوضوح تام على الشاشة
        st.dataframe(df, use_container_width=True, height=400)
        st.success(f"📊 إجمالي عدد السجلات والأصناف في هذا الجدول: **{len(df)}** صنف")
      else:
        st.warning("هذا الشيت فارغ حالياً.")

      st.markdown("---")
      st.markdown("### ➕ إضافة صنف أو كود جديد")

      with st.form("add_item_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
          item_code = st.text_input("كود الصنف (Item Code)")
        with col2:
          item_name = st.text_input("اسم الصنف (Item Name)")

        submitted = st.form_submit_button("حفظ وإضافة الصنف لجوجل شيت")
        if submitted:
          if item_code and item_name:
            try:
              # إضافة السطر الجديد مباشرة لجوجل شيت
              ws.append_row([str(item_code), str(item_name)])
              
              # مسح الذاكرة المؤقتة لتحديث الجدول فوراً
              st.cache_data.clear()
              
              st.success(
                  f"تم إضافة الصنف ({item_name}) بالكود ({item_code}) بنجاح وتم تحديث الشيت!"
              )
              st.rerun()
            except Exception as e:
              st.error(f"خطأ أثناء الحفظ: {e}")
          else:
            st.warning("يرجى إدخال كود الصنف واسم الصنف معاً.")
    else:
      st.warning("لا توجد تبويبات في ملف جوجل شيت.")

  except Exception as e:
    st.error(f"حدث خطأ في النظام: {e}")
