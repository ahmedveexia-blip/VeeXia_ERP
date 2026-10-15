import pandas as pd
import streamlit as st
import gspread

# إعدادات صفحة التطبيق
st.set_page_config(
    page_title="VeeXia ERP - النظام الشامل المتكامل",
    page_icon="🏭",
    layout="wide",
)

st.title("🏭 نظام VeeXia ERP - لوحة التحكم والتحكامل الشامل في قواعد البيانات")
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

if db is not None:
  try:
    # جلب جميع التبويبات والبيانات المتاحة تلقائياً من جوجل شيت
    worksheets = db.worksheets()
    ws_titles = [ws.title for ws in worksheets]

    # القائمة الجانبية للتنقل الشامل
    st.sidebar.markdown("### 🗂️ لوحة التنقل الرئيسية")
    app_mode = st.sidebar.selectbox(
        "اختر القسم:",
        [
            "استعراض كافة الجداول والشيتات",
            "إدارة الألبومات ووصفات الإنتاج (BOM)",
            "حساب أوزان أوامر الإنتاج",
        ],
    )

    if app_mode == "استعراض كافة الجداول والشيتات":
      st.markdown("### 📋 استعراض الجداول وقاعدة البيانات (Google Sheets)")
      selected_sheet = st.selectbox("اختر الجدول أو التبويب:", ws_titles)

      if selected_sheet:
        ws = db.worksheet(selected_sheet)
        data = ws.get_all_values()

        if len(data) > 0:
          headers = data[0]
          rows = data[1:] if len(data) > 1 else []
          df = pd.DataFrame(rows, columns=headers if rows else None)
          df = df.dropna(how="all")

          st.info(
              f"📊 إجمالي عدد السجلات في جدول `{selected_sheet}`: **{len(df)}**"
          )
          st.dataframe(df, use_container_width=True)
        else:
          st.warning("هذا الجدول فارغ حالياً.")

    elif app_mode == "إدارة الألبومات ووصفات الإنتاج (BOM)":
      st.markdown(
          "### 💊 إدارة مكونات وألبومات المواد (BOM) والأصناف المرتبطة"
      )

      with st.form("bom_integration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
          parent_item = st.text_input("اسم المنتج التام (Parent Item)")
          component_item = st.text_input("المادة الخام / التغليف (Component)")
        with col2:
          unit_weight = st.number_input(
              "وزن الوحدة (جم)", min_value=0.0, step=0.001, format="%.3f"
          )
          wastage_pct = st.number_input(
              "نسبة الهالك (%)", min_value=0.0, value=1.0, step=0.1
          )

        submitted = st.form_submit_button("حفظ المكون وتحديث شيت BOM")
        if submitted:
          if parent_item and component_item:
            try:
              if "tbl_BOM" in ws_titles:
                bom_ws = db.worksheet("tbl_BOM")
              else:
                bom_ws = db.add_worksheet(title="tbl_BOM", rows=100, cols=10)
                bom_ws.update([[
                    "BOM_ID",
                    "Parent_Item_ID",
                    "Component_Item_ID",
                    "Required_Quantity",
                    "Unit_Weight_g",
                    "Wastage_Pct",
                ]])

              existing_bom = bom_ws.get_all_records()
              new_id = len(existing_bom) + 1

              bom_ws.append_row([
                  new_id,
                  parent_item,
                  component_item,
                  1,
                  unit_weight,
                  wastage_pct,
              ])
              st.success("تم حفظ المكون في جدول tbl_BOM على Google Sheets بنجاح!")
            except Exception as e:
              st.error(f"حدث خطأ أثناء الحفظ في جوجل شيت: {e}")
          else:
            st.warning("يرجى إدخال اسم المنتج والمكون.")

      # عرض محتويات tbl_BOM الحالي إن وجد
      if "tbl_BOM" in ws_titles:
        try:
          bom_ws = db.worksheet("tbl_BOM")
          bom_data = bom_ws.get_all_records()
          if bom_data:
            st.markdown("---")
            st.markdown("### 📋 جدول الألبومات الحالي (tbl_BOM)")
            st.dataframe(pd.DataFrame(bom_data), use_container_width=True)
        except Exception:
          pass

    elif app_mode == "حساب أوزان أوامر الإنتاج":
      st.markdown("### 🧮 حساب إجمالي الأوزان والتشغيل لأوامر الإنتاج")

      if "tbl_BOM" in ws_titles:
        try:
          bom_ws = db.worksheet("tbl_BOM")
          bom_data = bom_ws.get_all_records()
          if bom_data:
            bom_df = pd.DataFrame(bom_data)
            if "Parent_Item_ID" in bom_df.columns:
              products = bom_df["Parent_Item_ID"].unique()
              selected_prod = st.selectbox("اختر المنتج التام:", products)
              batch_qty = st.number_input(
                  "الكمية المراد إنتاجها (وحدة):",
                  min_value=1,
                  value=5000,
                  step=500,
              )

              if selected_prod:
                prod_bom = bom_df[
                    bom_df["Parent_Item_ID"] == selected_prod
                ].copy()

                if "Unit_Weight_g" not in prod_bom.columns:
                  prod_bom["Unit_Weight_g"] = 1.0
                if "Wastage_Pct" not in prod_bom.columns:
                  prod_bom["Wastage_Pct"] = 1.0

                prod_bom["Unit_Weight_g"] = pd.to_numeric(
                    prod_bom["Unit_Weight_g"], errors="coerce"
                ).fillna(0)
                prod_bom["Wastage_Pct"] = pd.to_numeric(
                    prod_bom["Wastage_Pct"], errors="coerce"
                ).fillna(0)

                prod_bom["وزن الوحدة بعد الهالك (جم)"] = prod_bom[
                    "Unit_Weight_g"
                ] * (1 + prod_bom["Wastage_Pct"] / 100)
                prod_bom["إجمالي الوزن المطلوب (كجم)"] = (
                    prod_bom["وزن الوحدة بعد الهالك (جم)"] * batch_qty
                ) / 1000

                st.markdown(
                    f"#### 📊 تقرير تفصيلي لإنتاج **{batch_qty:,}** وحدة من:"
                    f" **{selected_prod}**"
                )
                display_df = prod_bom[[
                    "Component_Item_ID",
                    "Unit_Weight_g",
                    "Wastage_Pct",
                    "إجمالي الوزن المطلوب (كجم)",
                ]]
                st.dataframe(display_df, use_container_width=True)

                total_kg = display_df["إجمالي الوزن المطلوب (كجم)"].sum()
                st.success(
                    f"⚖️ إجمالي وزن الخامات بالكامل للتشكيلة ="
                    f" **{total_kg:.3f} كجم**"
                )
          else:
            st.info("لا توجد بيانات مسجلة في جدول tbl_BOM حالياً.")
        except Exception as e:
          st.error(f"حدث خطأ أثناء تحميل بيانات الألبومات: {e}")
      else:
        st.warning(
            "جدول tbl_BOM غير موجود حالياً في قاعدة البيانات. قم بإنشائه أو إضافته"
            " من قسم إدارة الألبومات."
        )

  except Exception as e:
    st.error(f"حدث خطأ عام في النظام: {e}")
else:
    st.warning("تعذر الاتصال بقاعدة البيانات.")
