# 🏥 MediCore — Hospital Management System

A full-featured Hospital Management System built with **Python + Streamlit + SQLite**.

## 🚀 Live Demo
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-name.streamlit.app)

## ✨ Features
- 🔐 **Login System** — Admin, Doctor, Receptionist roles with RBAC
- 📊 **Dashboard** — Live stats with 8 metric cards
- 👥 **Patients** — Full CRUD with search
- 👨‍⚕️ **Doctors** — Manage doctors, specializations, fees
- 📅 **Appointments** — Book, complete, cancel appointments
- 💰 **Billing** — Generate bills, track payments, download PDF invoices
- 💊 **Inventory** — Medicine & equipment with low-stock alerts
- 👷 **Staff** — Manage hospital staff & shifts
- 📊 **Reports** — Analytics charts (matplotlib), downloadable PNG
- 🖨️ **PDF Bills** — Professional invoices with reportlab

## 🛠️ Tech Stack
| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python 3 |
| Database | SQLite |
| Charts | Matplotlib |
| PDF | ReportLab |

## 📦 Installation
```bash
git clone https://github.com/YOUR_USERNAME/hospital-management.git
cd hospital-management
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Deploy on Streamlit Cloud
1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub → Select repo → Set `app.py` as main file
4. Click Deploy!

## 📁 Project Structure
```
hospital_streamlit/
├── app.py              ← Main Streamlit app (622 lines)
├── database.py         ← SQLite CRUD operations
├── charts.py           ← Matplotlib analytics charts
├── pdf_gen.py          ← ReportLab PDF bill generator
├── requirements.txt    ← Dependencies
└── .streamlit/
    └── config.toml     ← Dark theme config
```
