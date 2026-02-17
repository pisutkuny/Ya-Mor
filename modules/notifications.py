import requests
import streamlit as st
import json

def send_line_message(access_token, user_id, message, image_file=None):
    """
    Sends a push message using LINE Messaging API.
    Note: Free tier has a 200 message/month limit.
    """
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    
    # Image handling in Messaging API is harder (requires public URL). 
    # For now, we stick to text alerts to keep it simple without needing external storage.
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return True, "แจ้งเตือน LINE สำเร็จ"
        else:
            return False, f"LINE Error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Exception: {e}"
