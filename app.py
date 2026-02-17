import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import sqlite3
import json
import datetime
from icalendar import Calendar, Event
import io
import time

# --- Configuration & Setup ---
st.set_page_config(
    page_title="Ya-Mor (ยาหมอ)",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for Elderly Friendly UI ---
st.markdown("""
<style>
    /* Increase base font size */
    html, body, [class*="css"] {
        font-family: 'Sarabun', sans-serif; /* A clear Thai font if available */
        font-size: 18px;
    }
    
    /* Header styling */
    h1 {
        font-size: 2.2rem !important;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    h2 {
        font-size: 1.8rem !important;
        color: #2874A6;
        border-bottom: 2px solid #AED6F1;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    h3 {
        font-size: 1.5rem !important;
        color: #1F618D;
    }

    /* Button styling - Big & Clickable */
    .stButton > button {
        width: 100%;
        height: 60px;
        font-size: 1.2rem !important;
        font-weight: bold;
        border-radius: 12px;
        background-color: #3498DB;
        color: white;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #2980B9;
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }
    
    /* Success/Primary Action Button override */
    div[data-testid="stVerticalBlock"] > div:nth-child(5) .stButton > button {
         background-color: #28B463; /* Green for confirm */
    }

    /* Input fields */
    .stTextInput > div > div > input {
        font-size: 1.1rem;
        padding: 10px;
    }
    
    /* Cards for appointments */
    .appointment-card {
        background-color: #F8F9F9;
        border: 1px solid #D6DBDF;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #3498DB;
    }
    .appointment-card strong {
        color: #2E86C1;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Database Management ---
DB_FILE = 'appointments.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital TEXT,
            doctor TEXT,
            date TEXT,
            time TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_appointment(hospital, doctor, date_str, time_str, note):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO appointments (hospital, doctor, date, time, note)
            VALUES (?, ?, ?, ?, ?)
        ''', (hospital, doctor, date_str, time_str, note))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการบันทึก: {e}")
        return False

def load_appointments():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM appointments ORDER BY date DESC, time ASC", conn)
    conn.close()
    return df

# Initialize DB on load
init_db()

# --- Gemini AI Integration ---
def configure_genai():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        # Check system env var as fallback or just prompt user
        import os
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        st.warning("⚠️ ไม่พบ API Key! กรุณาตั้งค่า `GEMINI_API_KEY` ใน `.streamlit/secrets.toml`")
        st.info("หรือใส่ key ชั่วคราวที่นี่ (ไม่แนะนำสำหรับการใช้งานจริง):")
        temp_key = st.text_input("Enter Gemini API Key", type="password")
        if temp_key:
            genai.configure(api_key=temp_key)
            return True
        return False
    else:
        genai.configure(api_key=api_key)
        return True

def extract_data_from_image(image):
    # List of models to try in order of preference
    candidate_models = [
        'gemini-2.0-flash',
        'gemini-flash-latest',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
    ]
    
    prompt = """
    คุณคือผู้ช่วยอัจฉริยะวิเคราะห์ใบนัดแพทย์ ดูรูปภาพนี้แล้วดึงข้อมูลออกมาเป็น JSON format ดังนี้:
    {
        "hospital_name": "ชื่อโรงพยาบาล (ถ้ามี)",
        "doctor_name": "ชื่อแพทย์ (ถ้ามี)",
        "appointment_date": "YYYY-MM-DD (แปลงจาก พ.ศ. เป็น ค.ศ. ให้ถูกต้อง - ลบ 543)",
        "appointment_time": "HH:MM (24-hour format)",
        "note": "หมายเหตุเพิ่มเติม หรือ สิ่งที่ต้องเตรียมตัว (ถ้ามี)"
    }
    ถ้าไม่เจอข้อมูล ให้ใส่ null หรือ "ไม่ระบุ".
    ตอบกลับเฉพาะ JSON เท่านั้น ไม่ต้องมี markdown block.
    """
    
    with st.spinner('🤖 กำลังอ่านข้อมูลจากรูปภาพ... (AI Scan)'):
        errors = []
        for model_name in candidate_models:
            try:
                # Create model instance
                model = genai.GenerativeModel(model_name)
                
                # Generate content
                response = model.generate_content([prompt, image])
                text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(text)
                return data
            except Exception as e:
                errors.append(f"{model_name}: {str(e)}")
                continue # Try next model
        
        # If all failed, try to list available models to help validation
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception as e:
            available_models = [f"Could not list models: {str(e)}"]

        error_msg = "\n".join(errors)
        st.error(f"❌ ไม่สามารถวิเคราะห์รูปภาพได้\n\n**Error Logs:**\n{error_msg}\n\n**Available Models for your Key:**\n{', '.join(available_models)}")
        return None

# --- Main App Interface ---

def main():
    st.title("🏥 Ya-Mor (ยาหมอ)")
    st.caption("ผู้ช่วยจำนัด สำหรับทุกวัย ใช้ง่าย สบายตา")

    # API Check
    api_ready = configure_genai()

    # --- Section 1: Upload ---
    st.header("1. 📸 เพิ่มนัดหมายใหม่")
    
    uploaded_file = st.file_uploader("ถ่ายรูปใบนัด หรือ อัปโหลดรูปภาพ", type=['jpg', 'jpeg', 'png'])
    
    # Session State for form data
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            'hospital': '', 'doctor': '', 'date': datetime.date.today(), 'time': datetime.time(9, 0), 'note': ''
        }
    
    # Logic to handle if file is uploaded
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='รูปภาพที่อัปโหลด', use_column_width=True)
        
        if api_ready:
            if st.button("🔍 อ่านข้อมูลอัตโนมัติ (AI Scan)", key="scan_btn"):
                result = extract_data_from_image(image)
                if result:
                    st.session_state.form_data['hospital'] = result.get('hospital_name') or ''
                    st.session_state.form_data['doctor'] = result.get('doctor_name') or ''
                    st.session_state.form_data['note'] = result.get('note') or ''
                    
                    # Parse Date
                    date_str = result.get('appointment_date')
                    if date_str:
                        try:
                            # Try multiple formats if needed, but ISO is requested
                            d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                            st.session_state.form_data['date'] = d
                        except:
                            pass # Keep default today
                    
                    # Parse Time
                    time_str = result.get('appointment_time')
                    if time_str:
                        try:
                            t = datetime.datetime.strptime(time_str, "%H:%M").time()
                            st.session_state.form_data['time'] = t
                        except:
                            pass # Keep default 9:00
                    st.success("อ่านข้อมูลสำเร็จ! โปรดตรวจสอบด้านล่าง")

    # --- Section 2: Verify & Edit ---
    # Show form if file uploaded OR manual entry requested
    if uploaded_file or st.session_state.get('manual_entry', False):
        st.header("2. 📝 ตรวจสอบและแก้ไข")
        
        with st.form("appointment_form"):
            col1, col2 = st.columns(2)
            with col1:
                hospital = st.text_input("ชื่อโรงพยาบาล", value=st.session_state.form_data['hospital'])
            with col2:
                doctor = st.text_input("ชื่อแพทย์", value=st.session_state.form_data['doctor'])
            
            col3, col4 = st.columns(2)
            with col3:
                appt_date = st.date_input("วันที่นัด", value=st.session_state.form_data['date'])
            with col4:
                appt_time = st.time_input("เวลานัด", value=st.session_state.form_data['time'])
            
            note = st.text_area("หมายเหตุ / สิ่งที่ต้องเตรียม", value=st.session_state.form_data['note'])
            
            submitted = st.form_submit_button("✅ บันทึกนัดหมาย (Save)")
            
            if submitted:
                # Basic validation
                if not hospital:
                    st.error("กรุณาระบุชื่อโรงพยาบาล")
                else:
                    success = save_appointment(
                        hospital, doctor, appt_date.strftime("%Y-%m-%d"), appt_time.strftime("%H:%M"), note
                    )
                    if success:
                        st.success("บันทึกข้อมูลเรียบร้อยแล้ว!")
                        time.sleep(1) # feedback delay
                        # Reset
                        st.session_state.form_data = {
                            'hospital': '', 'doctor': '', 'date': datetime.date.today(), 'time': datetime.time(9, 0), 'note': ''
                        }
                        st.session_state.manual_entry = False
                        st.rerun()

    # Toggle manual entry button (only show if no file uploaded and not already in manual mode)
    if not uploaded_file and not st.session_state.get('manual_entry', False):
        if st.button("✍️ กรอกข้อมูลเอง (ไม่ใช้รูปภาพ)"):
            st.session_state.manual_entry = True
            st.rerun()

    # --- Section 3: List ---
    st.header("3. 📅 รายการนัดหมายของคุณ")
    
    df = load_appointments()
    
    if not df.empty:
        # Create ICS Calendar object for bulk download
        cal = Calendar()
        cal.add('prodid', '-//Ya-Mor App//mxm.dk//')
        cal.add('version', '2.0')
        
        for index, row in df.iterrows():
            # Display Card
            with st.container():
                st.markdown(f"""
                <div class="appointment-card">
                    <h3>🏥 {row['hospital']}</h3>
                    <p><strong>👨‍⚕️ แพทย์:</strong> {row['doctor'] or '-'}</p>
                    <p><strong>📅 วันที่:</strong> {row['date']} <strong>เวลา:</strong> {row['time']} น.</p>
                    <p><strong>📝 โน้ต:</strong> {row['note'] or '-'}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Add to ICS
            event = Event()
            event.add('summary', f"นัดหมอ: {row['hospital']}")
            try:
                # Combine date and time for ICS start
                start_dt = datetime.datetime.strptime(f"{row['date']} {row['time']}", "%Y-%m-%d %H:%M")
                event.add('dtstart', start_dt)
                event.add('dtend', start_dt + datetime.timedelta(hours=1)) # Default duration 1 hour
                event.add('description', f"แพทย์: {row['doctor']}\nหมายเหตุ: {row['note']}")
                cal.add_component(event)
            except:
                pass # Skip if date format error

        # --- Section 4: Export (Bulk) ---
        st.divider()
        try:
            ics_data = cal.to_ical()
            st.download_button(
                label="📥 ดาวน์โหลดปฏิทิน (.ics) ทั้งหมด",
                data=ics_data,
                file_name="appointments.ics",
                mime="text/calendar",
                key="download-ics-all"
            )
        except Exception as e:
            st.error(f"Generate ICS Error: {e}")

    else:
        st.info("ยังไม่มีรายการนัดหมาย")

if __name__ == "__main__":
    main()
