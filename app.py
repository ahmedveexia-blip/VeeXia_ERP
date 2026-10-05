import json
from datetime import datetime
import io
import gspread
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="VeeXia ERP System",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; }
    .stApp { background-color: #f8f9fa; }
    .topbar { background-color: #7d2c42; color: white; padding: 10px 20px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; }
    .stButton>button { background-color: #7d2c42; color: white; border-radius: 8px; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #5c2031; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def init_connection():
  try:
    sec = st.secrets["gcp_service_account"]
    creds = json.loads(sec["text_json"]) if "text_json" in sec else dict(sec)
    return gspread.service_account_from_dict(creds).open("VeeXia_ERP_DB")
  except Exception as e:
    st.error(f"خطأ الاتصال: {e}")
    return None


db = init_connection()


def get_data(sheet_name):
  if not db:
    return pd.DataFrame(), None
  try:
    s = db.worksheet(sheet_name)
    return pd.DataFrame(s.get_all_records()), s
  except:
    return pd.DataFrame(), None


def export_to_excel(df):
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="Data")
  return output.getvalue()


if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "app" not in st.session_state:
  st.session_state.app = "dashboard"

# --- 1. شاشة تسجيل الدخول ---
if not st.session_state.logged_in:
  st.markdown("<br><br>", unsafe_allow_html=True)
  _, col, _ = st.columns([1, 1.5, 1])
  with col:
    st.markdown(
        "<h2 style='text-align:center; color:#7d2c42;'>VeeXia ERP</h2>",
        unsafe_allow_html=True,
    )
    with st.form("login"):
      u = st.text_input("اسم المستخدم")
      p = st.text_input("كلمة المرور", type="password")
      if st.form_submit_button("تسجيل الدخول 🔓"):
        if u == "admin" and p == "123456":
          st.session_state.logged_in = True
          st.session_state.user = "Ahmed Rbany"
          st.rerun()
        else:
          df_u, _ = get_data("tbl_Users")
          if (
              not df_u.empty
              and "Username" in df_u.columns
              and not df_u[
                  (df_u["Username"].astype(str) == u)
                  & (df_u["Password"].astype(str) == p)
              ].empty
          ):
            st.session_state.logged_in = True
            st.session_state.user = u
            st.rerun()
          else:
            st.error("بيانات الدخول غير صحيحة")

# --- 2. النظام الداخلي ---
else:
  st.markdown(
      f"<div class='topbar'><h3>⣿ VeeXia ERP System</h3><span>👤"
      f" {st.session_state.user}</span></div>",
      unsafe_allow_html=True,
  )

  if st.session_state.app != "dashboard":
    if st.button("⬅️ العودة للوحة التحكم"):
      st.session_state.app = "dashboard"
      st.rerun()

  # A. لوحة التحكم
  if st.session_state.app == "dashboard":
    st.subheader("اختر التطبيق")
    c1, c2, c3 = st.columns(3)
    if c1.button("🏭\n\nإدارة المصانع"):
      st.session_state.app = "factories"
      st.rerun()
    if c2.button("📦\n\nالمخزون والأصناف"):
      st.session_state.app = "inventory"
      st.rerun()
    if c3.button("🛒\n\nالشراء والتوريد"):
      st.session_state.app = "purchases"
      st.rerun()

    if c1.button("⚙️\n\nالتصنيع والإنتاج (BOM)"):
      st.session_state.app = "mrp"
      st.rerun()
    if c2.button("💰\n\nالمصروفات"):
      st.session_state.app = "expenses"
      st.rerun()
    if c3.button("🔐\n\nإدارة المستخدمين"):
      st.session_state.app = "admin"
      st.rerun()

    if st.button("🚪 تسجيل الخروج"):
      st.session_state.logged_in = False
      st.rerun()

  # B. المصانع
  elif st.session_state.app == "factories":
    st.subheader("🏭 إدارة المصانع")
    df, s = get_data("tbl_Factories")

    with st.form("f_form"):
      name = st.text_input("اسم المصنع")
      if st.form_submit_button("حفظ") and name and s:
        s.append_row([len(df) + 1, name])
        st.success("تم الحفظ!")
        st.rerun()

    st.markdown("---")
    st.subheader("📋 قائمة المصانع المسجلة")
    if not df.empty:
      search = st.text_input("🔍 بحث عن مصنع...")
      filtered_df = (
          df[df["Fact_Name"].astype(str).str.contains(search, case=False)]
          if search
          else df
      )

      st.dataframe(filtered_df, use_container_width=True)
      st.download_button(
          "📥 تصدير الجدول إلى Excel",
          data=export_to_excel(filtered_df),
          file_name="Factories.xlsx",
      )

  # C. المخزون والأرصدة
  elif st.session_state.app == "inventory":
    st.subheader("📦 المخزون والأرصدة الحالية")
    df_item, s_item = get_data("Items")
    df_doc, _ = get_data("tbl_Doc_Details")
    df_prod, _ = get_data("tbl_Production")

    with st.form("i_form"):
      c, n = st.columns(2)
      code = c.text_input("كود الصنف")
      name = n.text_input("اسم الصنف")
      if st.form_submit_button("إضافة صنف") and name and s_item:
        s_item.append_row([code, name])
        st.success("تمت الإضافة!")
        st.rerun()

    st.markdown("---")
    st.subheader("📊 كشف أرصدة المخزون")

    if not df_item.empty:
      res = []
      for _, r in df_item.iterrows():
        nm = r.get("Item_Name", "")
        i_qty = (
            pd.to_numeric(
                df_doc[df_doc["Item_Name"] == nm]["Quantity"], errors="coerce"
            ).sum()
            if not df_doc.empty and "Item_Name" in df_doc.columns
            else 0
        )
        i_qty += (
            pd.to_numeric(
                df_prod[df_prod["Finished_Product"] == nm]["Produced_Qty"],
                errors="coerce",
            ).sum()
            if not df_prod.empty and "Finished_Product" in df_prod.columns
            else 0
        )
        o_qty = (
            pd.to_numeric(
                df_prod[df_prod["Raw_Material"] == nm]["Used_Qty"],
                errors="coerce",
            ).sum()
            if not df_prod.empty and "Raw_Material" in df_prod.columns
            else 0
        )
        res.append({
            "الكود": r.get("Item_Code", ""),
            "الصنف": nm,
            "الوارد 📥": i_qty,
            "المنصرف 📤": o_qty,
            "الرصيد 📦": i_qty - o_qty,
        })

      df_res = pd.DataFrame(res)
      search = st.text_input("🔍 بحث باسم الصنف...")
      if search:
        df_res = df_res[
            df_res["الصنف"].astype(str).str.contains(search, case=False)
        ]

      st.dataframe(df_res, use_container_width=True)
      st.download_button(
          "📥 تصدير كشف المخزون إلى Excel",
          data=export_to_excel(df_res),
          file_name="Inventory_Balance.xlsx",
      )

  # D. الشراء والتوريد
  elif st.session_state.app == "purchases":
    st.subheader("🛒 حركة الشراء والتوريد")
    df_f, _ = get_data("tbl_Factories")
    df_i, _ = get_data("Items")
    df_h, s_h = get_data("tbl_Doc_Header")
    df_d, s_d = get_data("tbl_Doc_Details")

    f_list = df_f["Fact_Name"].tolist() if not df_f.empty else []
    i_list = df_i["Item_Name"].tolist() if not df_i.empty else []

    with st.form("p_form"):
      c1, c2, c3 = st.columns(3)
      doc = c1.text_input("رقم الإذن")
      date = c2.date_input("التاريخ", datetime.now())
      fact = c3.selectbox("المصنع", f_list or ["لا يوجد"])

      col1, col2, col3 = st.columns([2, 1, 1])
      item = col1.selectbox("الصنف", i_list or ["لا يوجد"])
      qty = col2.number_input("الكمية", min_value=1.0)
      price = col3.number_input("السعر", min_value=0.0)

      if st.form_submit_button("حفظ الفاتورة") and doc and item:
        if s_h:
          s_h.append_row([doc, str(date), fact])
        if s_d:
          s_d.append_row([doc, item, qty, price, qty * price])
        st.success("تم الحفظ وتحديث المخزون!")
        st.rerun()

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
      st.subheader("📄 سجل الفواتير (Header)")
      if not df_h.empty:
        st.dataframe(df_h, use_container_width=True)
        st.download_button(
            "📥 تصدير الفواتير Excel",
            data=export_to_excel(df_h),
            file_name="Doc_Header.xlsx",
        )
    with col_b:
      st.subheader("🔍 تفاصيل البنود (Details)")
      if not df_d.empty:
        st.dataframe(df_d, use_container_width=True)
        st.download_button(
            "📥 تصدير التفاصيل Excel",
            data=export_to_excel(df_d),
            file_name="Doc_Details.xlsx",
        )

  # E. التصنيع (BOM)
  elif st.session_state.app == "mrp":
    st.subheader("⚙️ التصنيع وقائمة المكونات (BOM)")
    df_i, _ = get_data("Items")
    df_bom, s_bom = get_data("tbl_BOM")
    _, s_prod = get_data("tbl_Production")

    i_list = df_i["Item_Name"].tolist() if not df_i.empty else []
    t1, t2 = st.tabs(["تنفيذ أمر إنتاج", "إضافة مكونات BOM"])

    with t1:
      if not df_bom.empty and "Parent_Item" in df_bom.columns:
        with st.form("prod_form"):
          p_item = st.selectbox(
              "المنتج التام", df_bom["Parent_Item"].unique().tolist()
          )
          p_qty = st.number_input("الكمية المنتجة", min_value=1.0)
          if st.form_submit_button("تشغيل الإنتاج وخصم الخامات"):
            matched = df_bom[df_bom["Parent_Item"] == p_item]
            for _, r in matched.iterrows():
              raw = r.get("Raw_Item")
              used = float(r.get("Required_Qty", 0)) * p_qty
              if s_prod:
                s_prod.append_row(
                    [str(datetime.now().date()), p_item, p_qty, raw, used]
                )
            st.success("تم تنفيذ أمر الإنتاج وخصم الخامات آلياً!")
            st.rerun()
      else:
        st.info("سجل مكونات المنتجات أولاً من التبويب الثاني.")

    with t2:
      with st.form("bom_form"):
        p = st.selectbox("المنتج التام", i_list or ["لا يوجد"])
        r = st.selectbox("المادة الخام", i_list or ["لا يوجد"])
        q = st.number_input("الكمية المطلوبة لكل وحدة", min_value=0.001)
        if st.form_submit_button("حفظ المكون") and s_bom:
          s_bom.append_row([p, r, q])
          st.success("تم الحفظ!")
          st.rerun()

      st.markdown("---")
      if not df_bom.empty:
        st.dataframe(df_bom, use_container_width=True)

  # F. المصروفات
  elif st.session_state.app == "expenses":
    st.subheader("💰 المصروفات")
    df_e, s_e = get_data("tbl_Expenses")

    with st.form("e_form"):
      c1, c2 = st.columns(2)
      amt = c1.number_input("المبلغ", min_value=1.0)
      cat = c2.text_input("نوع المصروف / البيان")
      if st.form_submit_button("حفظ") and s_e:
        s_e.append_row([str(datetime.now().date()), cat, amt])
        st.success("تم الحفظ!")
        st.rerun()

    st.markdown("---")
    if not df_e.empty:
      st.dataframe(df_e, use_container_width=True)
      st.download_button(
          "📥 تصدير المصروفات Excel",
          data=export_to_excel(df_e),
          file_name="Expenses.xlsx",
      )

  # G. إدارة المستخدمين
  elif st.session_state.app == "admin":
    st.subheader("🔐 إضافة مستخدم")
    df_u, s_u = get_data("tbl_Users")
    with st.form("u_form"):
      u = st.text_input("اسم المستخدم")
      p = st.text_input("كلمة المرور", type="password")
      if st.form_submit_button("إضافة") and u and p and s_u:
        s_u.append_row([u, p, u, "مستخدم"])
        st.success("تمت الإضافة!")
        st.rerun()

    st.markdown("---")
    if not df_u.empty:
      st.dataframe(df_u, use_container_width=True)