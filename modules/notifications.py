import requests
import streamlit as st

def send_line_notify(token, message, image_file=None):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {token}'}
    data = {'message': message}
    files = None
    
    if image_file:
        files = {'imageFile': image_file}
        
    try:
        response = requests.post(url, headers=headers, data=data, files=files)
        if response.status_code == 200:
            return True, "แจ้งเตือน Line สำเร็จ"
        else:
            return False, f"Line Error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Exception: {e}"

def check_and_alert_missed_dose(users, logs):
    # This logic is tricky in Streamlit. 
    # V2 Implementation: We just provide the mechanism. 
    # Real-time alert needs external cron job.
    pass
