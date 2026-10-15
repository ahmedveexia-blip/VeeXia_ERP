import streamlit as st
import pandas as pd
import gspread

st.set_page_config(
    page_title="VeeXia ERP System", page_icon="🏭", layout="wide"
)

# الهيدر الموحد
st.markdown(
    """
    <div style="background-color: #800020; padding: 15px; border-radius: 5px; margin-bottom: 25px;">
        <h1 style="color: white; text-align: center; margin: 0; font-size: 26px;">VeeXia ERP System</h1>
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
  except Exception:
    return None


db = init_connection()

if "current_page" not in st.session_state:
  st.session_state.current_page = "الرئيسية"

if db is None:
  st.error(
      "⚠️ تعذر الاتصال بقاعدة بيانات Google Sheets. تأكد من إعدادات الـ"
      " Secrets."
  )
else:
  try:
    @st.cache_data(ttl=30)
    def get_worksheets_list():
      try:
        return [ws.title for ws in db.worksheets()]
      except Exception:
        return []

    ws_titles = get_worksheets_list()

    # الواجهة الرئيسية (الأزرار)
    if st.session_state.current_page == "الرئيسية":
      st.markdown(
          "<h3 style='text-align: center; color: #333;'>اختر التطبيق</h3>",
          unsafe_allow_html=True,
      )
      st.markdown("<br>", unsafe_allow_html=True)

      col1, col2, col3 = st.columns(3)
      with col1:
        if st.button(
            "📦 المخزون والأصناف", use_container_width=True, type="primary"
        ):
          st.session_state.current_page = "المخزون والأصناف"
          st.rerun()
        if st.button("🏭 إدارة المصانع", use_container_width=True):
          st.session_state.current_page = "إدارة المصانع"
          st.rerun()
      with col2:
        if st.button("⚙️ التصنيع والإنتاج (BOM)", use_container_width=True):
          st.session_state.current_page = "التصنيع والإنتاج (BOM)"
          st.rerun()
        if st.button("💰 المصروفات", use_container_width=True):
          st.session_state.current_page = "المصروفات"
          st.rerun()
      with col3:
        if st.button("🛒 الشراء والتوريد", use_container_width=True):
          st.session_state.current_page = "الشراء والتوريد"
          st.rerun()
        if st.button("🔐 إدارة المستخدمين", use_container_width=True):
          st.session_state.current_page = "إدارة المستخدمين"
          st.rerun()

    else:
      # زر العودة للوحة التحكم الرئيسية
      if st.button("⬅️ العودة للوحة التحكم"):
        st.session_state.current_page = "الرئيسية"
        st.rerun()

      st.markdown("---")

      # صفحة المخزون والأصناف (عرض الجدول مباشرة بوضوح تام)
      if st.session_state.current_page == "المخزون والأصناف":
        st.markdown("### 📦 المخزون والأرصدة الحالية - جدول المنتجات والأكواد")

        if ws_titles:
          # اختيار التبويب (مع اختيار افتراضي لتبويب pk أو أول تبويب تلقائياً)
          default_idx = (
              ws_titles.index("pk") if "pk" in ws_titles else 0
          )
          selected_sheet = st.selectbox(
              "اختر الشيت / التبويب:", ws_titles, index=default_idx
          )

          if selected_sheet:
            ws = db.worksheet(selected_sheet)
            data = ws.get_all_values()

            st.markdown("---")
            if len(data) > 0:
              headers = data[0]
              rows = data[1:] if len(data) > 1 else []
              df = pd.DataFrame(rows, columns=headers if rows else None)
              df = df.dropna(how="all")

              # عرض جدول المنتجات والأكواد بشكل ظاهر وبارز جداً
              st.markdown(
                  f"#### 📊 جدول الأكواد والأصناف النشط في (`{selected_sheet}`)"
              )
              st.dataframe(df, use_container_width=True, height=350)
              st.info(
                  f"إجمالي عدد الأصناف المسجلة في الجدول: **{len(df)}** صنف"
              )
            else:
              st.warning("هذا التبويب فارغ حالياً.")

            st.markdown("---")
            st.markdown("#### ➕ إضافة صنف أو كود جديد مباشرة إلى الجدول")

            with st.form("add_item_visible_form", clear_on_submit=True):
              c1, c2 = st.columns(2)
              with c1:
                new_code = st.text_input("كود الصنف (Item Code)")
              with c2:
                new_name = st.text_input("اسم الصنف (Item Name)")

              submitted = st.form_submit_button(
                  "حفظ وإضافة الصنف لجوجل شيت فوراً"
              )
              if submitted:
                if new_code and new_name:
                  try:
                    ws.append_row([new_code, new_name])
                    st.success(
                        f"تم إضافة الصنف ({new_name}) بالكود ({new_code}) بنجاح!"
                    )
                    st.rerun()
                  except Exception as e:
                    st.error(f"خطأ أثناء الحفظ: {e}")
                else:
                  st.warning("يرجى إدخال كود الصنف واسم الصنف.")
        else:
          st.warning("لا توجد تبويبات في جوجل شيت.")

      elif st.session_state.current_page == "التصنيع والإنتاج (BOM)":
        st.markdown("### ⚙️ التصنيع والإنتاج (BOM)")
        if "tbl_BOM" in ws_titles:
          bom_ws = db.worksheet("tbl_BOM")
          bom_data = bom_ws.get_all_values()
          if len(bom_data) > 0:
            st.dataframe(
                pd.DataFrame(bom_data[1:], columns=bom_data[0]),
                use_container_width=True,
            )
        else:
          st.info("جدول tbl_BOM غير موجود.")
      else:
        st.markdown(f"### قسم: {st.session_state.current_page}")
        st.info("هذا القسم قيد التجهيز.")

  except Exception as e:
    st.error(f"حدث خطأ في النظام: {e}")
