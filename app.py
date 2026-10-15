import pandas as pd
import streamlit as st
import gspread

# إعدادات صفحة التطبيق
st.set_page_config(
    page_title="VeeXia ERP - إدارة الألبومات والإنتاج",
    page_icon="💊",
    layout="centered",
)

st.title("🏭 نظام VeeXia ERP - إدارة ألبومات المواد (BOM)")
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


# تحميل بيانات الأصناف (tbl_Items) والألبومات (tbl_BOM)
@st.cache_data(ttl=30)
def load_database_tables():
  items_df = pd.DataFrame(columns=["Item_ID", "Item_Name", "Category"])
  bom_df = pd.DataFrame(
      columns=[
          "BOM_ID",
          "Parent_Item_ID",
          "Component_Item_ID",
          "Required_Quantity",
          "Unit_Weight_g",
          "Wastage_Pct",
      ]
  )

  if db is not None:
    try:
      # قراءة جدول الأصناف
      ws_items = db.worksheet("tbl_Items")
      items_data = ws_items.get_all_records()
      if items_data:
        items_df = pd.DataFrame(items_data)
    except Exception:
      pass

    try:
      # قراءة جدول الألبومات
      ws_bom = db.worksheet("tbl_BOM")
      bom_data = ws_bom.get_all_records()
      if bom_data:
        bom_df = pd.DataFrame(bom_data)
    except Exception:
      pass

  return items_df, bom_df


items_df, bom_df = load_database_tables()

# التنقل بين الأقسام
menu = st.sidebar.selectbox(
    "القائمة الرئيسية", ["إدارة جدول الألبومات (tbl_BOM)", "حساب أوزان أوامر الإنتاج"]
)

if menu == "إدارة جدول الألبومات (tbl_BOM)":
  st.markdown("### 📋 إدارة تفاصيل ألبومات المواد الخام والتغليف")

  if items_df.empty:
    st.warning(
        "تنبيه: تأكد من وجود جدول tbl_Items بداخل جوجل شيت لاختيار المنتجات"
        " منه."
    )

  with st.form("tbl_bom_form", clear_on_submit=True):
    st.markdown("#### ➕ إضافة مكون جديد للألبوم (BOM)")
    col1, col2 = st.columns(2)
    with col1:
      parent_item = st.text_input(
          "المنتج التام (Parent Item / مثال: أكياس فوار 5 جم)"
      )
      component_item = st.text_input(
          "المادة الخام / المكون (Component / مثال: حمض الستريك)"
      )
    with col2:
      unit_weight = st.number_input(
          "وزن الوحدة الواحدة (بالجرام)",
          min_value=0.0,
          step=0.001,
          format="%.3f",
      )
      wastage_pct = st.number_input(
          "نسبة الهالك (%)", min_value=0.0, value=1.0, step=0.1
      )

    submitted = st.form_submit_button("حفظ وحفظ التحديثات في جوجل شيت")
    if submitted:
      if parent_item and component_item:
        new_row = {
            "BOM_ID": len(bom_df) + 1,
            "Parent_Item_ID": parent_item,
            "Component_Item_ID": component_item,
            "Required_Quantity": 1,
            "Unit_Weight_g": unit_weight,
            "Wastage_Pct": wastage_pct,
        }
        bom_df = pd.concat([bom_df, pd.DataFrame([new_row])], ignore_index=True)

        # التحديث المباشر في جدول tbl_BOM على جوجل شيت
        if db is not None:
          try:
            ws_bom = db.worksheet("tbl_BOM")
            ws_bom.clear()
            ws_bom.update(
                [bom_df.columns.values.tolist()] + bom_df.values.tolist()
            )
            st.success("تم تحديث شيت tbl_BOM على Google Sheets بنجاح!")
          except Exception as e:
            st.warning(f"تمت الإضافة محلياً ولكن تعذر التحديث بالسحابة: {e}")
      else:
        st.warning("يرجى إدخال اسم المنتج والمكون على الأقل.")

  if not bom_df.empty:
    st.markdown("---")
    st.markdown("### 📊 محتويات جدول الألبومات الحالي (tbl_BOM)")
    st.dataframe(bom_df, use_container_width=True)

elif menu == "حساب أوزان أوامر الإنتاج":
  st.markdown("### 🧮 حساب إجمالي الأوزان لامر الإنتاج بناءً على الألبوم")

  if bom_df.empty:
    st.warning("لا توجد بيانات مسجلة في جدول الألبومات (tbl_BOM) حالياً.")
  else:
    # التأكد من توفر أعمدة الأوزان في الشيت أو تعويضها افتراضياً
    if "Unit_Weight_g" not in bom_df.columns:
      bom_df["Unit_Weight_g"] = 1.0
    if "Wastage_Pct" not in bom_df.columns:
      bom_df["Wastage_Pct"] = 1.0

    selected_product = st.selectbox(
        "اختر المنتج التام:", bom_df["Parent_Item_ID"].unique()
    )
    batch_qty = st.number_input(
        "الكمية المراد إنتاجها (عدد الوحدات):",
        min_value=1,
        value=5000,
        step=500,
    )

    if selected_product:
      prod_bom = bom_df[bom_df["Parent_Item_ID"] == selected_product].copy()

      # الحسابات الدقيقة للوزن والهالك
      prod_bom["الوزن بعد الهالك للوحدة (جم)"] = prod_bom[
          "Unit_Weight_g"
      ] * (1 + prod_bom["Wastage_Pct"] / 100)
      prod_bom["إجمالي الوزن المطلوب (كجم)"] = (
          prod_bom["الوزن بعد الهالك للوحدة (جم)"] * batch_qty
      ) / 1000

      st.markdown(
          f"#### 📈 تفاصيل خامات التشغيل لإنتاج **{batch_qty:,}** وحدة من: **{selected_product}**"
      )

      display_table = prod_bom[[
          "Component_Item_ID",
          "Unit_Weight_g",
          "Wastage_Pct",
          "إجمالي الوزن المطلوب (كجم)",
      ]]
      st.dataframe(display_table, use_container_width=True)

      total_order_kg = display_table["إجمالي الوزن المطلوب (كجم)"].sum()
      st.success(
          f"⚖️ إجمالي وزن التشكيلة/الباكتة بالكامل = **{total_order_kg:.3f} كجم**"
      )
