import pandas as pd
import streamlit as st
import gspread

# إعدادات الصفحة
st.set_page_config(
    page_title="VeeXia ERP - إدارة الإنتاج والألبومات",
    page_icon="💊",
    layout="centered",
)

st.title("🏭 نظام VeeXia ERP - إدارة الألبومات (BOM) والإنتاج")
st.markdown("---")


# إعداد الاتصال بقاعدة بيانات Google Sheets
@st.cache_resource
def init_connection():
  try:
    creds_dict = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"][
            "auth_provider_x509_cert_url"
        ],
        "client_x509_cert_url": st.secrets["gcp_service_account"][
            "client_x509_cert_url"
        ],
        "universe_domain": st.secrets["gcp_service_account"]["universe_domain"],
    }
    client = gspread.service_account_from_dict(creds_dict)
    return client.open("VeeXia_ERP_DB")
  except Exception as e:
    st.error(f"خطأ في الاتصال بقاعدة بيانات Google Sheets: {e}")
    return None


db = init_connection()


# تحميل أو تهيئة بيانات الألبومات (BOM)
@st.cache_data(ttl=60)
def load_bom_data():
  if db is not None:
    try:
      worksheet = db.worksheet("BOM")
      data = worksheet.get_all_records()
      if data:
        return pd.DataFrame(data)
    except Exception:
      pass

  # بيانات افتراضية أولية (أكياس الفوار والمكونات)
  return pd.DataFrame(
      [
          {
              "اسم المنتج": "أكياس فوار 5 جم",
              "المادة الخام / المكون": "حمض الستريك (Citric Acid)",
              "وزن الوحدة (جم)": 1.5,
              "نسبة الهالك (%)": 2.0,
          },
          {
              "اسم المنتج": "أكياس فوار 5 جم",
              "المادة الخام / المكون": "بيكربونات الصوديوم",
              "وزن الوحدة (جم)": 2.5,
              "نسبة الهالك (%)": 1.5,
          },
          {
              "اسم المنتج": "أكياس فوار 5 جم",
              "المادة الخام / المكون": "مادة مُحلاّة / منكهات",
              "وزن الوحدة (جم)": 0.5,
              "نسبة الهالك (%)": 3.0,
          },
      ]
  )


if "bom_df" not in st.session_state:
  st.session_state.bom_df = load_bom_data()

# القائمة الجانبية للتنقل
menu = st.sidebar.selectbox(
    "القائمة الرئيسية", ["إدارة ألبومات المواد (BOM)", "حساب أوزان أوامر الإنتاج"]
)

if menu == "إدارة ألبومات المواد (BOM)":
  st.markdown("### 💊 إدارة ألبومات المواد الخام والتغليف (BOM)")

  # نموذج إضافة مكون جديد للألبوم
  with st.form("bom_form", clear_on_submit=True):
    st.markdown("#### ➕ إضافة مكون جديد لألبوم المنتج")
    col1, col2 = st.columns(2)
    with col1:
      product_name = st.text_input(
          "اسم المنتج التام (مثال: أكياس فوار فيتامين سي)"
      )
      raw_material = st.text_input("اسم المادة الخام / التغليف")
    with col2:
      unit_weight = st.number_input(
          "وزن المادة في الوحدة الواحدة (جم)",
          min_value=0.0,
          step=0.001,
          format="%.3f",
      )
      wastage_pct = st.number_input(
          "نسبة الهالك (%)", min_value=0.0, value=1.0, step=0.1
      )

    submitted = st.form_submit_button("حفظ المكون في الألبوم")
    if submitted:
      if product_name and raw_material:
        new_row = pd.DataFrame(
            [{
                "اسم المنتج": product_name,
                "المادة الخام / المكون": raw_material,
                "وزن الوحدة (جم)": unit_weight,
                "نسبة الهالك (%)": wastage_pct,
            }]
        )
        st.session_state.bom_df = pd.concat(
            [st.session_state.bom_df, new_row], ignore_index=True
        )

        # تحديث Google Sheets تلقائياً إذا كان متصلاً
        if db is not None:
          try:
            worksheet = (
                db.worksheet("BOM")
                if "BOM" in [ws.title for ws in db.worksheets()]
                else db.add_worksheet(title="BOM", rows=100, cols=10)
            )
            worksheet.clear()
            worksheet.update(
                [st.session_state.bom_df.columns.values.tolist()]
                + st.session_state.bom_df.values.tolist()
            )
          except Exception as e:
            st.warning(f"تم الحفظ محلياً ولكن تعذر التحديث المباشر للشيت: {e}")

        st.success(
            f"تمت إضافة ({raw_material}) للمنتج ({product_name}) بنجاح!"
        )
      else:
        st.warning("من فضلك أدخل اسم المنتج التام واسم المادة الخام.")

  # عرض الجدول الحالي
  if not st.session_state.bom_df.empty:
    st.markdown("---")
    st.markdown("### 📋 قائمة الألبومات والمكونات المسجلة")
    st.dataframe(st.session_state.bom_df, use_container_width=True)

elif menu == "حساب أوزان أوامر الإنتاج":
  st.markdown("### 🧮 حساب إجمالي الخامات المطلوبة لأمر إنتاج")

  if st.session_state.bom_df.empty:
    st.warning("لا توجد ألبومات مسجلة حالياً.")
  else:
    selected_product = st.selectbox(
        "اختر المنتج التام لحساب أوزان تشكيلته:",
        st.session_state.bom_df["اسم المنتج"].unique(),
    )

    production_qty = st.number_input(
        "الكمية المراد إنتاجها (عدد الوحدات):",
        min_value=1,
        value=5000,
        step=500,
    )

    if selected_product:
      product_bom = st.session_state.bom_df[
          st.session_state.bom_df["اسم المنتج"] == selected_product
      ].copy()

      # العمليات الحسابية للهالك والوزن الإجمالي
      product_bom["الوزن الفعلي بعد الهالك للوحدة (جم)"] = product_bom[
          "وزن الوحدة (جم)"
      ] * (1 + product_bom["نسبة الهالك (%)"] / 100)

      product_bom["إجمالي الوزن المطلوب (كجم)"] = (
          product_bom["الوزن الفعلي بعد الهالك للوحدة (جم)"] * production_qty
      ) / 1000

      st.markdown(
          f"#### 📊 تفاصيل الخامات لإنتاج **{production_qty:,}** وحدة من: **{selected_product}**"
      )

      display_df = product_bom[[
          "المادة الخام / المكون",
          "وزن الوحدة (جم)",
          "نسبة الهالك (%)",
          "إجمالي الوزن المطلوب (كجم)",
      ]]
      st.dataframe(display_df, use_container_width=True)

      total_weight_kg = display_df["إجمالي الوزن المطلوب (كجم)"].sum()
      st.success(
          f"⚖️ إجمالي وزن الخامات بالكامل للتشكيلة = **{total_weight_kg:.3f} كجم**"
      )
