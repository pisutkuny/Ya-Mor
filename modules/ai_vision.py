import google.generativeai as genai
import streamlit as st
import json
import time

def configure_genai():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        # Check system env var as fallback
        import os
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if api_key:
        genai.configure(api_key=api_key)
        return True
    return False

def extract_medicine_info(image):
    # Models to try (Newer models first)
    candidate_models = [
        'gemini-2.0-flash',
        'gemini-flash-latest',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
    ]

    prompt = """
    คุณคือเภสัชกรผู้เชี่ยวชาญ ช่วยดูรูปซองยาหรือขวดยานี้ แล้วดึงข้อมูลสำคัญออกมาเป็น JSON format ดังนี้:
    {
        "medicine_name": "ชื่อยา (ภาษาอังกฤษหรือไทย)",
        "dosage": "ปริมาณการทาน (เช่น 1 เม็ด, 2 ช้อนชา)",
        "frequency": ["morning", "noon", "evening", "bedtime"],  <-- เลือกเฉพาะช่วงเวลาที่ต้องทานจากฉลาก (ถ้ามี 'ก่อนอาหาร/หลังอาหาร' ไม่ต้องใส่ ให้ใส่แค่ช่วงเวลา)
        "indication": "สรรพคุณ (รักษาอะไร - สั้นๆ)",
        "warning": "คำเตือนสำคัญ (ถ้ามี)"
    }
    
    กฏการตอบ:
    1. ถ้าหาชื่อยาไม่เจอ ให้ใส่ "ไม่ระบุ"
    2. frequency ต้องเป็น Array ของ string: "morning" (เช้า), "noon" (กลางวัน), "evening" (เย็น), "bedtime" (ก่อนนอน) เท่านั้น
    3. ตอบกลับเฉพาะ JSON เท่านั้น ไม่ต้องมี markdown block
    """

    with st.spinner('🤖 AI กำลังอ่านฉลากยา... (เภสัชกรส่วนตัวกำลังทำงาน)'):
        errors = []
        for model_name in candidate_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content([prompt, image])
                text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(text)
                return data
            except Exception as e:
                errors.append(f"{model_name}: {str(e)}")
                continue

        # Fallback if all fail
        st.error(f"❌ ไม่สามารถอ่านฉลากยาได้\n{errors}")
        return None
