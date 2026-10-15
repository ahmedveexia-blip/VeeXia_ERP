import pandas as pd
import streamlit as st

# إعدادات صفحة التطبيق الأساسية
st.set_page_config(
    page_title="VeeXia ERP", page_icon="💊", layout="centered"
)

st.title("🏭 نظام VeeXia ERP لإدارة المخازن والإنتاج")
st.markdown("---")

# تهيئة جدول الألبومات في الذاكرة لتخزين المكونات
if "bom_data" not in st.session_state:
  st.session_state.bom_data = pd.DataFrame(
      [
          {
              "اسم المنتج": "أكياس فوار 5 جم",
              "المادة الخام / المكون": "حمض الستريك (Citric Acid)",
              "الوزن للوحدة الواحدة (جم)": 1.5,
              "النسبة / الهالك (%)": 2.0,
          },
          {
              "اسم المنتج": "أكياس فوار 5 جم",
              "المادة الخام / المكون": "بيكربونات الصوديوم",
              "الوزن للوحدة الواحدة (جم)": 2.5,
              "النسبة / الهالك (%)": 1.5,
          },
          {
              "اسم المنتج": "أكياس فوار 5 جم",
              "المادة الخام / المكون": "مادة مُحلاّة / منكهات",
              "الوزن للوحدة الواحدة (جم)": 0.5,
              "النسبة / الهالك (%)": 3.0,
          },
      ]
  )

# القائمة الجانبية للتنقل بين الأقسام
menu = st.sidebar.selectbox(
    "القائمة الرئيسية", ["إدارة ألبومات المواد (BOM)", "حساب أوزان أوامر الإنتاج"]
)

if menu == "إدارة ألبومات المواد (BOM)":
  st.markdown("### 💊 إدارة ألبومات الفوار والمستحضرات (BOM)")

  # نموذج إضافة مكون جديد للألبوم
  with st.form("bom_form_complete", clear_on_submit=True):
    st.markdown("#### ➕ إضافة مادة خام جديدة لألبوم المنتج")
    col1, col2 = st.columns(2)
    with col1:
      product_name = st.text_input(
          "اسم المنتج التام (مثال: أكياس فوار فيتامين سي)"
      )
      raw_material = st.text_input("اسم المادة الخام أو التغليف")
    with col2:
      unit_weight = st.number_input(
          "وزن المادة في الوحدة الواحدة (بالجرام)",
          min_value=0.0,
          step=0.001,
          format="%.3f",
      )
      wastage_pct = st.number_input(
          "نسبة الهالك / الفاقد (%)", min_value=0.0, value=1.0, step=0.1
      )

    submitted = st.form_submit_button("حفظ المكون في الألبوم")
    if submitted:
      if product_name and raw_material:
        new_row = pd.DataFrame(
            [{
                "اسم المنتج": product_name,
                "المادة الخام / المكون": raw_material,
                "الوزن للوحدة الواحدة (جم)": unit_weight,
                "النسبة / الهالك (%)": wastage_pct,
            }]
        )
        st.session_state.bom_data = pd.concat(
            [st.session_state.bom_data, new_row], ignore_index=True
        )
        st.success(
            f"تمت إضافة ({raw_material}) للمنتج ({product_name}) بنجاح!"
        )
      else:
        st.warning(
            "من فضلك أدخل اسم المنتج التام واسم المادة الخام على الأقل."
        )

  # عرض جدول الألبومات المسجلة بالكامل
  if not st.session_state.bom_data.empty:
    st.markdown("---")
    st.markdown("### 📋 قائمة الألبومات والمكونات المسجلة")
    st.dataframe(st.session_state.bom_data, use_container_width=True)

elif menu == "حساب أوزان أوامر الإنتاج":
  st.markdown("### 🧮 حساب إجمالي الخامات المطلوبة لأمر إنتاج (Batch Calculation)")

  if st.session_state.bom_data.empty:
    st.warning("لا توجد ألبومات مسجلة حالياً، الرجاء إضافتها من قسم إدارة الألبومات.")
  else:
    selected_product = st.selectbox(
        "اختر المنتج (الفوار أو الصنف) لحساب أوزان تشكيلته:",
        st.session_state.bom_data["اسم المنتج"].unique(),
    )

    production_qty = st.number_input(
        "الكمية المراد إنتاجها (عدد الوحدات التامة):",
        min_value=1,
        value=5000,
        step=500,
    )

    if selected_product:
      product_bom = st.session_state.bom_data[
          st.session_state.bom_data["اسم المنتج"] == selected_product
      ].copy()

      # العمليات الحسابية: حساب الوزن بعد الهالك + تحويل الإجمالي لكيلوجرام
      product_bom["الوزن الفعلي بعد الهالك للوحدة (جم)"] = product_bom[
          "الوزن للوحدة الواحدة (جم)"
      ] * (1 + product_bom["نسبة الهالك (%)"] / 100)

      product_bom["إجمالي الوزن المطلوب (كجم)"] = (
          product_bom["الوزن الفعلي بعد الهالك للوحدة (جم)"] * production_qty
      ) / 1000

      st.markdown(
          f"#### 📊 تفاصيل خامات أمر الإنتاج لـ: **{production_qty:,}** وحدة من **{selected_product}**"
      )

      display_df = product_bom[[
          "المادة الخام / المكون",
          "الوزن للوحدة الواحدة (جم)",
          "نسبة الهالك (%)",
          "إجمالي الوزن المطلوب (كجم)",
      ]]
      st.dataframe(display_df, use_container_width=True)

      total_weight_kg = display_df["إجمالي الوزن المطلوب (كجم)"].sum()
      st.success(
          f"⚖️ إجمالي وزن الخامات بالكامل للتشكيلة/الباكتة المطلوبة = **{total_weight_kg:.3f} كجم**"
      )
