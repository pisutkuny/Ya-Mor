# Ya-Mor (ยาหมอ) - Application Walkthrough

## Overview
Ya-Mor is a single-file Streamlit application designed to help elderly users manage their medical appointments. It uses Google Gemini AI to extract details from appointment cards and saves them to a local database.

## 🚀 How to Run

### 1. Install Dependencies
Open your terminal and run:
```bash
pip install -r requirements.txt
```

### 2. Set up API Key
You need a Google Gemini API Key.
- Create a file named `.streamlit/secrets.toml` in the project folder.
- Add the following line:
```toml
GEMINI_API_KEY = "YOUR_API_KEY_HERE"
```
*(Alternatively, you can enter the key in the app's UI for temporary use)*

### 3. Run the App
```bash
python -m streamlit run app.py
```

### 4. Setup LINE Messaging API (Optional - for Alerts)
See the detailed guide here: [LINE_API_GUIDE.md](LINE_API_GUIDE.md).

1. Go to [LINE Developers Console](https://developers.line.biz/).
2. Create a Provider and a Channel (Messaging API).
3. Get **Channel Access Token** and **Your User ID**.
4. Put these 2 values in the App's "Settings" page.


## 📱 Features

### 1. Upload & AI Scan (เพิ่มนัดหมาย)
- **Action**: Click "Browse files" or use the camera to take a photo of your appointment card.
- **AI**: Click "🔍 อ่านข้อมูลอัตโนมัติ" to let Gemini extract the Hospital, Doctor, Date, and Time.
- **Benefit**: No need to type everything manually!

### 2. Verify & Save (ตรวจสอบและบันทึก)
- **Action**: Review the pre-filled data. Correct anything if needed.
- **Save**: Click the big green "✅ บันทึกนัดหมาย" button.
- **Storage**: Data is saved to `appointments.db` automatically.

### 3. View & Download (ดูรายการและดาวน์โหลด)
- **View**: Scroll down to see your appointment content cards.
- **Calendar**: Click "📥 ดาวน์โหลดปฏิทิน (.ics)" to get a file you can open add to your phone's calendar (Google Calendar, Apple Calendar).

## ☁️ Deployment (Online)
See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions on how to put this app online for free using Streamlit Cloud.

**Quick Summary:**
1. Upload code to GitHub.
2. Deploy on Streamlit Cloud.
3. Add `GEMINI_API_KEY` to App Secrets.
4. "Add to Home Screen" on mobile for app-like experience.

## 🛠️ Technical Details
- **File**: `app.py` (Single file architecture)
- **Database**: SQLite (`appointments.db`)
- **AI Model**: `gemini-2.0-flash` / `gemini-flash-latest` (Auto-fallback)
- **UI**: Streamlit with custom CSS for accessibility (Large fonts, high contrast).
