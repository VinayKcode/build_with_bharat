# 🚨 Golden Hour — Automated Crash Detection & Real-Time Hospital Dispatch
> **Build with Bharat 4.0 National Level Hackathon**  
> *Team Dorara Coders (Rajkiya Engineering College, Kannauj)*

---

## 🌟 Overview
In India, over **1.77 lakh lives** are lost annually on roads, primarily due to delays during the critical **"Golden Hour"** (the first 60 minutes after a crash). 

**Golden Hour** is an end-to-end intelligent emergency coordination system:
1. **Detect:** Dual-Factor Sensor Verification (Heavy $g$-force crash spike + sudden vehicular speed drop).
2. **30-Second Cancel Window:** Audible alarm and countdown giving the driver time to cancel if unhurt.
3. **Decide:** Rejects non-trauma clinics; queries **OSRM (Open Source Routing Machine)** for real road network driving ETA, and ranks hospitals using:
   $$\text{Score} = (0.5 \times \text{Rating}) + (0.3 \times \text{Free ICU Beds}) - (0.2 \times \text{OSRM ETA})$$
4. **Respond:** Reserves an ICU bed in real-time, alerts 108 ambulance, requests a traffic green corridor, and auto-dispatches WhatsApp emergency alerts with live Google Maps routes.

---

## 📁 Project Structure
- `index.html`: Modern, simple frontend (Tab 1: Nurse Bed Portal + Tab 2: Live Control Room & Leaflet Map). Powered by **Supabase Realtime** & **OSRM**.
- `supabase_schema.sql`: 1-click database schema & realtime replication setup for Supabase.
- `main.py`: Optional Python FastAPI backend for Twilio WhatsApp dispatch and local hosting.
- `.env.example`: Configuration template for API keys.

---

## 🚀 Live Hosting on Netlify (100% Serverless)
`index.html` runs autonomously on **Netlify** without requiring a backend server:
1. Drag and drop `index.html` into your [Netlify Dashboard](https://app.netlify.com/drop).
2. Open your live Netlify URL on any phone or laptop.
3. Click the **"⚙️ API Keys"** button at the top right to link your Supabase URL & Key.

---

## ⚡ Supabase Setup (Real-Time Bed Sync)
1. Create a free project at [supabase.com](https://supabase.com).
2. Go to **SQL Editor** -> Paste and run the contents of `supabase_schema.sql`.
3. Go to **Project Settings** -> **API** -> Copy your `Project URL` and `anon public` key.
4. Paste them into the **"⚙️ API Keys"** dialog in the app.
Now, when a nurse changes bed counts on their phone, the control room map on your laptop updates in milliseconds!

---

## 💬 WhatsApp & Twilio Integration
- **Direct 1-Click WhatsApp:** Click **"📲 Open & Send on WhatsApp"** to launch WhatsApp Web/App with a pre-filled emergency alert and Google Maps navigation link.
- **Twilio Cloud SMS/WhatsApp:** Set your Twilio credentials in `main.py` or `.env` to automatically send background WhatsApp alerts.
