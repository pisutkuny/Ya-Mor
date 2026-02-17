import streamlit as st
import pandas as pd
import datetime
from PIL import Image

# Import Modules
from modules import database, ai_vision, ui_components, notifications

# --- Configuration & Setup ---
st.set_page_config(
    page_title="Ya-Mor (ยาหมอ) V2",
    page_icon="💊",
    layout="centered", # Mobile layout focus
    initial_sidebar_state="collapsed"
)

# Initialize DB
database.init_db()
ai_vision.configure_genai()

# --- Custom CSS for Senior UI ---
st.markdown("""
<style>
    /* Global Font Increase */
    html, body, [class*="css"] {
        font-family: 'Sarabun', sans-serif;
        font-size: 20px;
    }
    
    /* Big Headers */
    h1 { font-size: 2.5rem !important; color: #1B4F72; text-align: center; }
    h2 { font-size: 2rem !important; color: #154360; border-bottom: 2px solid #D4E6F1; }
    h3 { font-size: 1.6rem !important; color: #21618C; }
    
    /* Button overrides are in ui_components.py but global stButton needs size */
    .stButton > button {
        height: 70px;
        font-size: 1.5rem !important;
        border-radius: 15px;
        margin-bottom: 10px;
    }
    
    /* Input fields */
    div[data-baseweb="input"] > div {
        height: 50px;
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard' # dashboard, scan, settings

def navigate_to(page):
    st.session_state.page = page
    st.rerun()

# --- Pages ---

def render_dashboard():
    st.title("🏡 หน้าหลัก (ยาหมอ)")
    
    # 1. User Info / Settings Link
    user_settings = database.get_user_settings()
    if not user_settings or not user_settings['line_token']:
        st.warning("⚠️ ยังไม่ได้ตั้งค่าผู้ดูแล (Line)")
        if st.button("⚙️ ตั้งค่าระบบ", use_container_width=True):
            navigate_to('settings')
    else:
        if st.button(f"⚙️ ตั้งค่า (คุณ: {user_settings['name']})", use_container_width=True):
            navigate_to('settings')

    st.divider()

    # 2. Urgent / Current Dose (Logic: Morning, Noon, Evening, Bedtime)
    current_hour = datetime.datetime.now().hour
    period = "morning"
    if 11 <= current_hour < 16: period = "noon"
    elif 16 <= current_hour < 20: period = "evening"
    elif current_hour >= 20: period = "bedtime"
    
    period_map = {
        "morning": "☀️ เช้า",
        "noon": "☀️ เที่ยง",
        "evening": "🌆 เย็น",
        "bedtime": "🌙 ก่อนนอน"
    }
    
    st.header(f"💊 ยาที่ต้องทาน: {period_map[period]}")
    
    # Fetch meds
    meds_df = database.get_medications()
    
    has_meds_now = False
    if not meds_df.empty:
        for index, row in meds_df.iterrows():
            # Check frequency in JSON string
            if period in row['frequency']:
                has_meds_now = True
                def on_take(mid, mname):
                    success = database.log_activity(mid, 'taken', f"Taken at {period}")
                    if success:
                        st.success(f"เก่งมาก! ทาน {mname} แล้ว")
                        # Line Alert
                        if user_settings and user_settings.get('line_token') and user_settings.get('user_id'):
                            notifications.send_line_message(
                                user_settings['line_token'], 
                                user_settings['user_id'],
                                f"👵 {user_settings['name']} ทานยา '{mname}' รอบ {period_map[period]} แล้วค่ะ ✅"
                            )
                        st.rerun()
                
                ui_components.med_card(
                    (row['id'], row['name'], row['image_path'], row['dosage'], row['frequency'], row['stock'], row['created_at']),
                    on_click_action=on_take
                )

    if not has_meds_now:
        st.success("✅ ตอนนี้ยังไม่มียาที่ต้องทาน พักผ่อนได้เลย")

    st.divider()

    # 3. Add New Med Button
    if st.button("📸 เพิ่มยาใหม่ (ถ่ายรูป)", type="primary", use_container_width=True):
        navigate_to('scan')
    
    st.divider()
    
    # 4. SOS Button
    st.markdown("""
        <a href="tel:1669" style="text-decoration: none;">
            <button style="
                width: 100%; height: 80px; background-color: #C0392B; color: white; 
                font-size: 2rem; border-radius: 20px; border: none; font-weight: bold; cursor: pointer;">
                🚑 แจ้งฉุกเฉิน (โทรลูกหลาน)
            </button>
        </a>
    """, unsafe_allow_html=True)
    st.caption("*กดปุ่มแดงเพื่อโทรออกทันที")

def render_scan():
    st.title("📸 เพิ่มยาใหม่")
    if st.button("⬅️ กลับหน้าหลัก"):
        navigate_to('dashboard')
        
    uploaded_file = st.file_uploader("ถ่ายรูปซองยา/ขวดยา", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption='รูปยา', use_column_width=True)
        
        if st.button("🔍 ให้ AI อ่านฉลากยา", type="primary"):
            data = ai_vision.extract_medicine_info(image)
            if data:
                st.session_state.scanned_data = data
                st.success("อ่านฉลากเสร็จแล้ว! ตรวจสอบด้านล่าง")
            
    if 'scanned_data' in st.session_state:
        data = st.session_state.scanned_data
        
        with st.form("save_med_form"):
            name = st.text_input("ชื่อยา", value=data.get('medicine_name', ''))
            dosage = st.text_input("ปริมาณ (เช่น 1 เม็ด)", value=data.get('dosage', ''))
            
            st.subheader("ทานเวลาไหนบ้าง?")
            # Default Checks
            default_freq = data.get('frequency', [])
            c1, c2, c3, c4 = st.columns(4)
            morning = c1.checkbox("เช้า", "morning" in default_freq)
            noon = c2.checkbox("เที่ยง", "noon" in default_freq)
            evening = c3.checkbox("เย็น", "evening" in default_freq)
            bedtime = c4.checkbox("ก่อนนอน", "bedtime" in default_freq)
            
            stock = st.number_input("จำนวนยาที่มี (เม็ด)", min_value=0, value=10)
            
            if st.form_submit_button("💾 บันทึกข้อมูลยา"):
                freq_list = []
                if morning: freq_list.append("morning")
                if noon: freq_list.append("noon")
                if evening: freq_list.append("evening")
                if bedtime: freq_list.append("bedtime")
                
                success = database.add_medication(name, "path/to/img", dosage, freq_list, stock)
                if success:
                    st.success("บันทึกเรียบร้อย!")
                    del st.session_state.scanned_data
                    navigate_to('dashboard')

def render_settings():
    st.title("⚙️ ตั้งค่าระบบ")
    if st.button("⬅️ กลับหน้าหลัก"):
        navigate_to('dashboard')

    current = database.get_user_settings() or {}
    
    with st.form("settings_form"):
        name = st.text_input("ชื่อผู้สูงอายุ (เช่น คุณยาย)", value=current.get('name', ''))
        
        st.subheader("การแจ้งเตือน LINE (Messaging API)")
        st.info("เนื่องจาก LINE Notify ปิดให้บริการ เราจึงต้องใช้ Messaging API แทนครับ")
        line_token = st.text_input("Channel Access Token", value=current.get('line_token', ''), type="password")
        user_id = st.text_input("Your User ID (คนดูแล)", value=current.get('user_id', ''), type="password")
        st.caption("ไปที่ https://developers.line.biz/console/ เพื่อสร้าง Channel และเอาค่าเหล่านี้มาใส่")
        
        if st.form_submit_button("บันทึก"):
            database.save_user_settings(name, line_token, user_id)
            st.success("บันทึกค่าเรียบร้อย")
            st.rerun()

# --- Main Router ---
if st.session_state.page == 'dashboard':
    render_dashboard()
elif st.session_state.page == 'scan':
    render_scan()
elif st.session_state.page == 'settings':
    render_settings()
