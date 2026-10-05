from datetime import datetime
import io
import json
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
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&display=swap');
    * { font-family: 'Cairo', sans-serif !important; }
    .stApp { background-color: #f4f6f9; }
    .topbar { 
        background: linear-gradient(135deg, #7d2c42 0%, #5c2031 100%); 
        color: white; padding: 18px 25px; border-radius: 14px; 
        margin-bottom: 25px; display: flex; justify-content: space-between; 
        align-items: center; box-shadow: 0 4px 20px rgba(125, 44, 66, 0.15);
    }
    .topbar h3 { margin: 0; font-weight: 700; font-size: 1.4rem; }
    .topbar span { background: rgba(255, 255, 255, 0.15); padding: 6px 14px; border-radius: 20px; font-size: 0.9rem; font-weight: 600; }
    .stButton>button { 
        background: linear-gradient(135deg, #7d2c42 0%, #632235 100%); 
        color: white; border-radius: 10px; font-weight: 600; padding: 0.6rem 1rem;
        border: none; box-shadow: 0 3px 10px rgba(125, 44, 66, 0.2); width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        background: linear-gradient(135deg, #5c2031 100%, #421622 100%); 
        box-shadow: 0 5px 15px rgba(125, 44, 66, 0.35); transform: translateY(-1px);
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        border-radius: 10px; border: 1px solid #e0e0e0; background-color: #ffffff;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def init_connection():
  try:
    # استخدام st.secrets إذا كانت متوفرة، وإلا استخدام القاموس المباشر الآمن
    if "gcp_service_account" in st.secrets:
      creds_dict = dict(st.secrets["gcp_service_account"])
      return gspread.service_account_from_dict(creds_dict).open(
          "VeeXia_ERP_DB"
      )

    pk = (
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC8mSMVEEGRh+2r"
        "sONlScvExsK6Jn4WCuxz2F1pCBxEqr/DG8dYFtGn0CmI7SkwZwivs0RuegOp5Wd6"
        "zXFbg6fLsbvN44bfv2hiYJBeFd3/GKI60ZCw4kwQEk3OvZv9R2VwfcBvU6QCxl7v"
        "AI+8ilYXqfUorSWyZU0m+KFKGvqoZxRe21KaSpdIhGRdjE2CW8ad5Jth5i3ezikS"
        "p5oUngnAXNH2mTH9X5A9NV0y9eIi/ZlxfR5EVO1V6UYw6wiwbAj4Phna9IEkm51h"
        "nnAguacYHeTYngLC/OoxlcbsjK3YqSEYc73cwTzcEcg3dpDV+nNS0RLdZW1eeQQMS"
        "XtaiKFVJAgMBAAECggEAM9M9AbfC3NPmaqykABxkQ0F/FxomwbXkvfyxxn/1DKWD"
        "JoFGqR00JZIdJ8RL8kIN8AIqBtW+lfw1EFjOEqC+Bkpj2jLwyCFX9NimM0R9CXFi"
        "exlFUmYNEsmE2g/egp4Q8PWNYMoyIpUSV0jnNp8pAz2v4aqa1kfiCJh/8dYyFP4s"
        "npcOdQigPpNV3l7hdVmt7PZncpSD/cKEJADsTZg9lQnRBmBKRL/qtXO+xygVdpEl8"
        "rev+SON1fMPSsbhoXkQBoZqVJA9prisFG9HS2NWpHfG0syTxoYy4256xJvzBEMX0"
        "o+dSDhFzDRCtk+qVYbFE2Z55vwHgP7+5izZYHfmNdQKBgQD59OpDANdRnZgiM+dT"
        "nYAjhWY7QEttYy6nHFuK0Hqv98ypVDtjcL1S4cUjd6wdhH9JvTi/wsmjhfwqCZA+r"
        "gq5HzpK9+ev9J/D64pWt0zKE8es/OmvBlbnbFswZVL5HQyBS+5NYVAglvBLaJGzJ"
        "nqZWUyhcXqQpNNcbQ1A7M8FqptwKBgQDBKHLqanqfywE74H57UvhzGqtPDfh491Si"
        "VN5OU3+CqADOLsDma/IeNaQL8Y70amWeHPr7uCLMKqny/Jb87sqXnhaPB7Rojsm4"
        "IkWr+/7roOhn+yVFRTBQhp5JPI1k14FB5fSXq1BG90OogaW2SXgjbeQOLQucQrGl"
        "MA51eBD4/wKBgBQda4S82pcM0aNe/eytu8k2xdFk0xYQPbdx1gict0aWfP+fVEBT"
        "5sN5Cl4hfdSJFQw0BJOgJ+SNrrDTkJdCyveoXhK/vAgBYNkvxs/YQSaFuWK7NtS7"
        "UduZuA8JzM47Tqye5jqjeIxg2DuJ1t9bsFfq83TJ+7Q+8aL4jcBcT099AoGAQj5p"
        "CtPxshOhHLPlLM5Lvs4KqlYUPQg10mZgx2QDev+7JvsJ1Px4ULv8wsvZRyGmMA+o"
        "U+PWq0aGenr+HUiX2l+xRORTjvhJXgkC8/S8fHr2uZJ8OcF8zGEer+dAZrEx9zOy"
        "KsHqCiyK26N6/YU82om5iNMSBEkrO4e7rbW7vGkCgYAioIiYCb1zpl98oHMaW5tX"
        "njNzNCGWmXleotTFh7yl811gNSBz+U9Gww0dQxfH5GiYkGtWcVKKV1g7moQ7nM/Ec"
        "Hbu7HSupV3wnH0FoJUUiz3sk88nRVXEHduVKY04akPelhf23JI+ouHftn6dacmMw"
        "5jx+jUa+I9HSw3wVbGYLPA==\n"
        "-----END PRIVATE KEY-----\n"
    )

    creds = {
        "type": "service_account",
        "project_id": "veexia-erp",
        "private_key_id": "da558664cc7462ad484a66ca28d5663dfef96cc7",
        "private_key": pk,
        "client_email": "veexia-bot@veexia-erp.iam.gserviceaccount.com",
        "client_id": "115117847167928117949",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": (
            "https://www.googleapis.com/robot/v1/metadata/x509/veexia-bot%40veexia-erp.iam.gserviceaccount.com"
        ),
        "universe_domain": "googleapis.com",
    }
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

if not st.session_state.logged_in:
  st.markdown("<br><br>", unsafe_allow_html=True)
  _, col, _ = st.columns([1, 1.4, 1])
  with col:
    st.markdown(
        "<div style='background: white; padding: 30px; border-radius: 16px;"
        " box-shadow: 0 4px 25px rgba(0,0,0,0.06); border: 1px solid"
        " #eaeaea;'><h2 style='text-align:center; color:#7d2c42; font-weight:"
        " 800; margin-bottom: 25px;'>VeeXia ERP</h2>",
        unsafe_allow_html=True,
    )
    with st.form("login"):
      u = st.text_input("اسم المستخدم")
      p = st.text_input("كلمة المرور", type="password")
      st.markdown("<br>", unsafe_allow_html=True)
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
    st.markdown("</div>", unsafe_allow_html=True)
else:
  st.markdown(
      f"<div class='topbar'><h3>🏭 VeeXia ERP System</h3><span>👤"
      f" {st.session_state.user}</span></div>",
      unsafe_allow_html=True,
  )

  if st.session_state.app != "dashboard":
    if st.button("⬅ العودة لوحة التحكم الرئيسية"):
      st.session_state.app = "dashboard"
      st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

  if st.session_state.app == "dashboard":
    st.markdown(
        "<h4 style='color: #444; font-weight: 700; margin-bottom: 20px;'>لوحة"
        " التحكم الرئيسية</h4>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
      if st.button("🏭 إدارة المصانع"):
        st.session_state.app = "factories"
        st.rerun()
    with c2:
      if st.button("📦 المخزون والأصناف"):
        st.session_state.app = "inventory"
        st.rerun()
    with c3:
      if st.button("🛒 الشراء والتوريد"):
        st.session_state.app = "purchases"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    with c4:
      if st.button("⚙️ التصنيع والإنتاج (BOM)"):
        st.session_state.app = "mrp"
        st.rerun()
    with c5:
      if st.button("💰 المصروفات"):
        st.session_state.app = "expenses"
        st.rerun()
    with c6:
      if st.button("🔐 إدارة المستخدمين"):
        st.session_state.app = "admin"
        st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 تسجيل الخروج الآمن"):
      st.session_state.logged_in = False
      st.rerun()

  elif st.session_state.app == "factories":
    st.subheader("🏭 إدارة المصانع")
    df, s = get_data("tbl_Factories")
    with st.form("f_form"):
      name = st.text_input("اسم المصنع الجديد")
      if st.form_submit_button("حفظ المصنع") and name and s:
        s.append_row([len(df) + 1, name])
        st.success("تم الحفظ بنجاح!")
        st.rerun()
    st.markdown("---")
    if not df.empty:
      st.dataframe(df, use_container_width=True)

  elif st.session_state.app == "inventory":
    st.subheader("📦 المخزون والأرصدة")
    df_item, s_item = get_data("Items")
    with st.form("i_form"):
      c, n = st.columns(2)
      code = c.text_input("كود الصنف")
      name = n.text_input("اسم الصنف")
      if st.form_submit_button("إضافة صنف") and name and s_item:
        s_item.append_row([code, name])
        st.success("تمت الإضافة!")
        st.rerun()
    if not df_item.empty:
      st.dataframe(df_item, use_container_width=True)

  elif st.session_state.app == "purchases":
    st.subheader("🛒 الشراء والتوريد")
    df_h, _ = get_data("tbl_Doc_Header")
    if not df_h.empty:
      st.dataframe(df_h, use_container_width=True)

  elif st.session_state.app == "mrp":
    st.subheader("⚙️ التصنيع (BOM)")
    df_bom, _ = get_data("tbl_BOM")
    if not df_bom.empty:
      st.dataframe(df_bom, use_container_width=True)

  elif st.session_state.app == "expenses":
    st.subheader("💰 المصروفات")
    df_e, _ = get_data("tbl_Expenses")
    if not df_e.empty:
      st.dataframe(df_e, use_container_width=True)

  elif st.session_state.app == "admin":
    st.subheader("🔐 المستخدمين")
    df_u, _ = get_data("tbl_Users")
    if not df_u.empty:
      st.dataframe(df_u, use_container_width=True)
