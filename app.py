import streamlit as st
import pandas as pd
import gspread

st.set_page_config(
    page_title="VeeXia ERP System", page_icon="🏭", layout="wide"
)


# اتصال آمن ومخزن مؤقتاً
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

# إدارة التنقل بين صفحات النظام عبر الأزرار
if "current_page" not in st.session_state:
  st.session_state.current_page = "الرئيسية"

# الهيدر الموحد
st.markdown(
    """
    <div style="background-color: #800020; padding: 15px; border-radius: 5px; margin-bottom: 25px;">
        <h1 style="color: white; text-align: center; margin: 0; font-size: 26px;">VeeXia ERP System</h1>
    </div>
""",
    unsafe_allow_html=True,
)

if db is None:
  st.error(
      "⚠️ تعذر الاتصال بقاعدة بيانات Google Sheets. تأكد من إعدادات الـ"
      " Secrets."
  )
else:
  try:
    @st.cache_data(ttl=60)
    def get_worksheets_list():
      try:
        return [ws.title for ws in db.worksheets()]
      except Exception:
        return []

    ws_titles = get_worksheets_list()

    # لو في الصفحة الرئيسية (لوحة الأزرار)
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
      # زر العودة للقائمة الرئيسية
      if st.button("⬅️ العودة إلى القائمة الرئيسية"):
        st.session_state.current_page = "الرئيسية"
        st.rerun()

      st.markdown("---")

      # 1. قسم المخزون والأصناف
      if st.session_state.current_page == "المخزون والأصناف":
        st.markdown("### 📦 إدارة المخزون والأصناف والأكواد")

        if ws_titles:
          selected_sheet = st.selectbox(
              "اختر تبويب الأصناف / المخزون:", ws_titles
          )
          if selected_sheet:
            @st.cache_data(ttl=30)
            def load_sheet_data(sheet_name):
              try:
                ws = db.worksheet(sheet_name)
                return ws.get_all_values()
              except Exception as e:
                return str(e)

            with st.spinner("جاري جلب البيانات من جوجل شيت..."):
              result = load_sheet_data(selected_sheet)

            if isinstance(result, str):
              st.error(f"خطأ في قراءة الشيت: {result}")
            elif len(result) > 0:
              headers = result[0]
              rows = result[1:] if len(result) > 1 else []
              df = pd.DataFrame(rows, columns=headers if rows else None)
              df = df.dropna(how="all")
              st.success(
                  f"تم جلب جدول `{selected_sheet}` بنجاح (إجمالي السجلات:"
                  f" {len(df)})"
              )
              st.dataframe(df, use_container_width=True)
            else:
              st.info("هذا التبويب فارغ.")
        else:
          st.warning("لا توجد تبويبات متاحة في ملف Google Sheets.")

      # 2. قسم التصنيع والإنتاج (BOM)
      elif st.session_state.current_page == "التصنيع والإنتاج (BOM)":
        st.markdown("### ⚙️ إدارة ألبومات المواد (BOM) وحساب أوزان الإنتاج")

        tab1, tab2 = st.tabs(["📋 استعراض وعرض جدول BOM", "🧮 حساب أوامر الإنتاج"])

        with tab1:
          if "tbl_BOM" in ws_titles:
            try:
              bom_ws = db.worksheet("tbl_BOM")
              bom_data = bom_ws.get_all_values()
              if len(bom_data) > 0:
                bom_df = pd.DataFrame(
                    bom_data[1:], columns=bom_data[0]
                ).dropna(how="all")
                st.dataframe(bom_df, use_container_width=True)
              else:
                st.info("جدول tbl_BOM فارغ.")
            except Exception as e:
              st.error(f"خطأ: {e}")
          else:
            st.info("جدول tbl_BOM غير موجود حالياً في جوجل شيت.")

          st.markdown("---")
          st.markdown("#### ➕ إضافة مكون جديد إلى الألبوم (BOM)")
          with st.form("add_bom_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
              parent_item = st.text_input("اسم المنتج التام (Parent Item)")
              component_item = st.text_input("المكون / المادة الخام (Component)")
            with c2:
              unit_weight = st.number_input(
                  "وزن الوحدة (جم)", min_value=0.0, step=0.001, format="%.3f"
              )
              wastage_pct = st.number_input(
                  "نسبة الهالك (%)", min_value=0.0, value=1.0, step=0.1
              )

            submitted = st.form_submit_button("حفظ وحفظ التحديثات في جوجل شيت")
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
                  existing = bom_ws.get_all_records()
                  new_id = len(existing) + 1
                  bom_ws.append_row([
                      new_id,
                      parent_item,
                      component_item,
                      1,
                      unit_weight,
                      wastage_pct,
                  ])
                  st.success("تم الحفظ بنجاح في Google Sheets!")
                  st.rerun()
                except Exception as e:
                  st.error(f"خطأ أثناء الحفظ: {e}")
              else:
                st.warning("يرجى إدخال اسم المنتج والمكون على الأقل.")

        with tab2:
          if "tbl_BOM" in ws_titles:
            try:
              bom_ws = db.worksheet("tbl_BOM")
              bom_data = bom_ws.get_all_records()
              if bom_data:
                bom_df = pd.DataFrame(bom_data)
                if "Parent_Item_ID" in bom_df.columns:
                  products = bom_df["Parent_Item_ID"].unique()
                  selected_prod = st.selectbox(
                      "اختر المنتج التام للإنتاج:", list(products)
                  )
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
                    prod_bom["Unit_Weight_g"] = pd.to_numeric(
                        prod_bom.get("Unit_Weight_g", 0), errors="coerce"
                    ).fillna(0)
                    prod_bom["Wastage_Pct"] = pd.to_numeric(
                        prod_bom.get("Wastage_Pct", 0), errors="coerce"
                    ).fillna(0)

                    prod_bom["وزن الوحدة بعد الهالك (جم)"] = (
                        prod_bom["Unit_Weight_g"]
                        * (1 + prod_bom["Wastage_Pct"] / 100)
                    )
                    prod_bom["إجمالي الوزن المطلوب (كجم)"] = (
                        prod_bom["وزن الوحدة بعد الهالك (جم)"] * batch_qty
                    ) / 1000

                    st.markdown(
                        f"#### 📊 تقرير أوزان الخامات لإنتاج **{batch_qty:,}**"
                        f" وحدة من: **{selected_prod}**"
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
                st.info("لا توجد بيانات مسجلة في جدول BOM حالياً.")
            except Exception as e:
              st.error(f"خطأ أثناء حساب الأوزان: {e}")
          else:
            st.info("جدول tbl_BOM غير موجود حالياً.")

      else:
        st.markdown(f"### قسم: {st.session_state.current_page}")
        st.info("هذا القسم قيد التجهيز والربط مع قاعدة البيانات.")

  except Exception as e:
    st.error(f"حدث خطأ في النظام: {e}")
