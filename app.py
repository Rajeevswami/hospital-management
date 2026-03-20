"""
MediCore Hospital Management System
Single-file Streamlit App — No external imports needed
"""
import sys, os, io, hashlib
from datetime import datetime, date, timedelta
import sqlite3

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# ══════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hospital.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
        role TEXT NOT NULL, full_name TEXT, email TEXT, active INTEGER DEFAULT 1)""")
    c.execute("""CREATE TABLE IF NOT EXISTS patients(
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, age INTEGER, gender TEXT, blood_group TEXT,
        phone TEXT, email TEXT, address TEXT, medical_history TEXT,
        created_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS doctors(
        doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, specialization TEXT, phone TEXT, email TEXT,
        experience INTEGER, fee REAL DEFAULT 0, available INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS appointments(
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
        doctor_id  INTEGER REFERENCES doctors(doctor_id)  ON DELETE CASCADE,
        appointment_date TEXT, appointment_time TEXT,
        reason TEXT, status TEXT DEFAULT 'Scheduled', notes TEXT,
        created_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS billing(
        bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
        appointment_id INTEGER, amount REAL, paid REAL DEFAULT 0,
        payment_status TEXT DEFAULT 'Pending', description TEXT,
        bill_date TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS inventory(
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT, category TEXT, quantity INTEGER DEFAULT 0,
        unit_price REAL DEFAULT 0, supplier TEXT, expiry_date TEXT,
        created_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS staff(
        staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, role TEXT, phone TEXT, salary REAL DEFAULT 0,
        shift TEXT, created_at TEXT DEFAULT (datetime('now')))""")
    conn.commit()

    def _h(p): return hashlib.sha256(p.encode()).hexdigest()
    if not c.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
        c.executemany("INSERT INTO users(username,password,role,full_name,email) VALUES(?,?,?,?,?)",[
            ("admin",        _h("admin123"), "admin",        "Administrator",   "admin@hospital.com"),
            ("doctor1",      _h("doc123"),   "doctor",       "Dr. Arjun Sharma","arjun@hospital.com"),
            ("receptionist", _h("rec123"),   "receptionist", "Sunita Devi",     "rec@hospital.com"),
        ])
    if not c.execute("SELECT 1 FROM doctors").fetchone():
        c.executemany("INSERT INTO doctors(name,specialization,phone,email,experience,fee) VALUES(?,?,?,?,?,?)",[
            ("Dr. Arjun Sharma","Cardiology","9876543210","arjun@h.com",15,1500),
            ("Dr. Priya Mehta","Neurology","9876543211","priya@h.com",12,1800),
            ("Dr. Ravi Kumar","Orthopedics","9876543212","ravi@h.com",10,1200),
            ("Dr. Sunita Verma","Pediatrics","9876543213","sunita@h.com",8,1000),
            ("Dr. Anil Patel","General Medicine","9876543214","anil@h.com",20,800),
        ])
    if not c.execute("SELECT 1 FROM patients").fetchone():
        c.executemany("INSERT INTO patients(name,age,gender,blood_group,phone,email,address,medical_history) VALUES(?,?,?,?,?,?,?,?)",[
            ("Rahul Verma",32,"Male","B+","9811234567","rahul@mail.com","Delhi","Hypertension"),
            ("Anjali Gupta",28,"Female","O+","9822345678","anjali@mail.com","Mumbai","Diabetes"),
            ("Suresh Patel",45,"Male","A+","9833456789","suresh@mail.com","Pune","Asthma"),
            ("Meena Sharma",35,"Female","AB-","9844567890","meena@mail.com","Jaipur","None"),
            ("Vikram Singh",52,"Male","O-","9855678901","vikram@mail.com","Lucknow","Heart Disease"),
        ])
    if not c.execute("SELECT 1 FROM inventory").fetchone():
        c.executemany("INSERT INTO inventory(item_name,category,quantity,unit_price,supplier,expiry_date) VALUES(?,?,?,?,?,?)",[
            ("Paracetamol 500mg","Medicine",500,2.5,"MedCorp","2026-12-31"),
            ("Amoxicillin 250mg","Medicine",30,5.0,"PharmaCo","2026-06-30"),
            ("Surgical Gloves","Equipment",200,15.0,"MediSupply","2027-01-01"),
            ("Syringes 5ml","Equipment",400,3.0,"HealthKit","2027-06-01"),
            ("Bandages","Consumable",25,8.0,"CareSupply","2026-09-30"),
        ])
    if not c.execute("SELECT 1 FROM staff").fetchone():
        c.executemany("INSERT INTO staff(name,role,phone,salary,shift) VALUES(?,?,?,?,?)",[
            ("Ramesh Yadav","Nurse","9900011111",35000,"Morning"),
            ("Sunita Devi","Receptionist","9900022222",28000,"Morning"),
            ("Mohan Lal","Pharmacist","9900033333",40000,"Evening"),
        ])
    conn.commit(); conn.close()

def db_login(username, password):
    h = hashlib.sha256(password.encode()).hexdigest()
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=? AND password=? AND active=1",(username,h)).fetchone()
    conn.close()
    return dict(row) if row else None

PERMISSIONS = {
    "admin":        {"dashboard","patients","doctors","appointments","billing","inventory","staff","reports","users"},
    "doctor":       {"dashboard","patients","appointments","reports"},
    "receptionist": {"dashboard","patients","appointments","billing","inventory"},
}
def can(role, mod): return mod in PERMISSIONS.get(role, set())

def fetch(sql, params=()):
    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def run(sql, params=()):
    conn = get_conn()
    conn.execute(sql, params)
    conn.commit(); conn.close()

def get_stats():
    conn = get_conn()
    today = datetime.now().strftime("%Y-%m-%d")
    s = {
        "patients":    conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
        "doctors":     conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
        "appointments":conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
        "today_apts":  conn.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date=?",(today,)).fetchone()[0],
        "revenue":     conn.execute("SELECT COALESCE(SUM(paid),0) FROM billing").fetchone()[0],
        "pending":     conn.execute("SELECT COUNT(*) FROM billing WHERE payment_status='Pending'").fetchone()[0],
        "low_stock":   conn.execute("SELECT COUNT(*) FROM inventory WHERE quantity<50").fetchone()[0],
        "staff":       conn.execute("SELECT COUNT(*) FROM staff").fetchone()[0],
    }
    conn.close(); return s

# ══════════════════════════════════════════════════════════════
#  CHARTS
# ══════════════════════════════════════════════════════════════
BG="#0A0F1E"; CARD="#1A2235"; BORDER="#1E3050"
PAL=["#00D4FF","#7B61FF","#00FF9F","#FF6B6B","#FFB347","#FF85C2","#85FFD4","#FFD485"]

def _ax(ax, title=""):
    ax.set_facecolor(CARD)
    ax.tick_params(colors="#8B9EC7", labelsize=8)
    for s in ax.spines.values(): s.set_edgecolor(BORDER)
    ax.xaxis.label.set_color("#8B9EC7"); ax.yaxis.label.set_color("#8B9EC7")
    if title: ax.set_title(title, color="#00D4FF", fontsize=10, fontweight="bold", pad=8)
    ax.grid(axis="y", color=BORDER, linewidth=0.5, linestyle="--", alpha=0.6)

def dashboard_chart():
    conn = get_conn()
    months=[]; apts=[]; revs=[]
    for i in range(5,-1,-1):
        d = datetime.now()-timedelta(days=30*i)
        m = d.strftime("%Y-%m")
        months.append(d.strftime("%b"))
        apts.append(conn.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date LIKE ?",(f"{m}%",)).fetchone()[0])
        revs.append(float(conn.execute("SELECT COALESCE(SUM(paid),0) FROM billing WHERE bill_date LIKE ?",(f"{m}%",)).fetchone()[0]))
    specs   = conn.execute("SELECT specialization,COUNT(*) c FROM doctors GROUP BY specialization ORDER BY c DESC LIMIT 6").fetchall()
    statuses= conn.execute("SELECT status,COUNT(*) FROM appointments GROUP BY status").fetchall()
    genders = conn.execute("SELECT gender,COUNT(*) FROM patients GROUP BY gender").fetchall()
    blood   = conn.execute("SELECT blood_group,COUNT(*) c FROM patients WHERE blood_group!='' GROUP BY blood_group ORDER BY c DESC").fetchall()
    conn.close()

    fig = plt.figure(figsize=(16,10), facecolor=BG)
    fig.suptitle("MediCore — Analytics Dashboard", color="#00D4FF", fontsize=14, fontweight="bold", y=0.98)
    gs  = GridSpec(3,3, figure=fig, hspace=0.55, wspace=0.38, left=0.06, right=0.97, top=0.93, bottom=0.05)

    ax1 = fig.add_subplot(gs[0,:2])
    bars = ax1.bar(months, apts, color="#00D4FF", width=0.5, zorder=3)
    for b,v in zip(bars,apts): ax1.text(b.get_x()+b.get_width()/2, b.get_height()+0.1, str(v), ha="center", color="white", fontsize=8)
    _ax(ax1, "Monthly Appointments (Last 6 Months)")

    ax2 = fig.add_subplot(gs[0,2])
    if statuses:
        sl=[r[0] or "Unknown" for r in statuses]; sv=[r[1] for r in statuses]
        w,_ = ax2.pie(sv, colors=PAL[:len(sl)], startangle=90, wedgeprops={"width":0.55,"edgecolor":BG,"linewidth":2})
        ax2.legend(w, sl, loc="lower center", ncol=2, fontsize=7, labelcolor="#8B9EC7", facecolor=CARD, edgecolor=BORDER)
    ax2.set_facecolor(BG); ax2.set_title("Appointment Status", color="#00D4FF", fontsize=10, fontweight="bold")

    ax3 = fig.add_subplot(gs[1,:2])
    ax3.plot(months, revs, color="#00FF9F", linewidth=2.5, marker="o", markersize=7, zorder=3)
    ax3.fill_between(range(len(revs)), revs, alpha=0.12, color="#00FF9F")
    for i,v in enumerate(revs): ax3.text(i, v+(max(revs)*0.03 if max(revs)>0 else 1), f"Rs{v:.0f}", ha="center", color="white", fontsize=7)
    _ax(ax3, "Monthly Revenue (Rs.)"); ax3.set_xticks(range(len(months))); ax3.set_xticklabels(months)

    ax4 = fig.add_subplot(gs[1,2])
    if specs:
        sl=[r[0][:12] for r in specs]; sv=[r[1] for r in specs]
        ax4.barh(sl, sv, color=PAL[:len(sl)], height=0.6, zorder=3)
        for i,v in enumerate(sv): ax4.text(v+0.05, i, str(v), va="center", color="white", fontsize=7)
    _ax(ax4, "Doctors by Specialization"); ax4.invert_yaxis()

    ax5 = fig.add_subplot(gs[2,0])
    if genders:
        gl=[r[0] or "Unknown" for r in genders]; gv=[r[1] for r in genders]
        ax5.pie(gv, labels=gl, colors=["#7B61FF","#FF6B6B","#FFB347"][:len(gl)],
                autopct="%1.0f%%", startangle=90,
                textprops={"color":"white","fontsize":9}, wedgeprops={"edgecolor":BG,"linewidth":2})
    ax5.set_facecolor(BG); ax5.set_title("Patient Gender", color="#00D4FF", fontsize=10, fontweight="bold")

    ax6 = fig.add_subplot(gs[2,1])
    if blood:
        bl=[r[0] for r in blood]; bv=[r[1] for r in blood]
        bars6 = ax6.bar(bl, bv, color="#FF6B6B", width=0.6, zorder=3)
        for b,v in zip(bars6,bv): ax6.text(b.get_x()+b.get_width()/2, b.get_height()+0.05, str(v), ha="center", color="white", fontsize=8)
    _ax(ax6, "Blood Group Distribution")

    ax7 = fig.add_subplot(gs[2,2])
    top = fetch("""SELECT d.name,COUNT(a.appointment_id) c FROM doctors d
        LEFT JOIN appointments a ON d.doctor_id=a.doctor_id GROUP BY d.doctor_id ORDER BY c DESC LIMIT 5""")
    if top:
        tl=[r["name"].replace("Dr.","")[:12] for r in top]; tv=[r["c"] for r in top]
        ax7.barh(tl, tv, color="#7B61FF", height=0.6, zorder=3)
        for i,v in enumerate(tv): ax7.text(v+0.05, i, str(v), va="center", color="white", fontsize=7)
    _ax(ax7, "Top Doctors by Appointments"); ax7.invert_yaxis()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor=BG)
    plt.close(fig); buf.seek(0); return buf

def patient_chart():
    conn = get_conn()
    months=[]; vals=[]
    for i in range(11,-1,-1):
        d = datetime.now()-timedelta(days=30*i)
        months.append(d.strftime("%b"))
        vals.append(conn.execute("SELECT COUNT(*) FROM patients WHERE created_at LIKE ?",(f"{d.strftime('%Y-%m')}%",)).fetchone()[0])
    ag = conn.execute("SELECT SUM(age<18),SUM(age BETWEEN 18 AND 40),SUM(age BETWEEN 41 AND 60),SUM(age>60) FROM patients").fetchone()
    conn.close()

    fig = plt.figure(figsize=(12,5), facecolor=BG)
    fig.suptitle("Patient Analytics", color="#00D4FF", fontsize=13, fontweight="bold")
    gs  = GridSpec(1,2, figure=fig, wspace=0.35, left=0.08, right=0.96, top=0.88, bottom=0.12)

    ax1 = fig.add_subplot(gs[0])
    ax1.fill_between(range(len(vals)), vals, alpha=0.2, color="#00D4FF")
    ax1.plot(range(len(vals)), vals, color="#00D4FF", linewidth=2, marker="o", markersize=5)
    ax1.set_xticks(range(len(months))); ax1.set_xticklabels(months, rotation=45, fontsize=7)
    _ax(ax1, "Monthly New Patients (12 months)")

    ax2 = fig.add_subplot(gs[1])
    agl=["<18","18-40","41-60",">60"]; agv=[int(x or 0) for x in ag]
    ax2.pie(agv, labels=agl, colors=["#00FF9F","#00D4FF","#7B61FF","#FFB347"],
            autopct="%1.0f%%", startangle=90,
            textprops={"color":"white","fontsize":9}, wedgeprops={"edgecolor":BG,"linewidth":2})
    ax2.set_facecolor(BG); ax2.set_title("Age Groups", color="#00D4FF", fontsize=10, fontweight="bold")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor=BG)
    plt.close(fig); buf.seek(0); return buf

# ══════════════════════════════════════════════════════════════
#  PDF GENERATOR
# ══════════════════════════════════════════════════════════════
def generate_pdf(data: dict) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors as rlcolors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                rightMargin=1.5*cm, leftMargin=1.5*cm,
                                topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet(); story = []
        NAVY = rlcolors.HexColor("#0A0F1E"); BORDER_C = rlcolors.HexColor("#1E3050")
        right  = ParagraphStyle("r", parent=styles["Normal"], alignment=TA_RIGHT)
        center = ParagraphStyle("c", parent=styles["Normal"], alignment=TA_CENTER)

        ht = Table([[
            Paragraph("<b><font size=18 color='#00D4FF'>MediCore Hospital</font></b><br/>"
                      "<font size=9 color='#8B9EC7'>Hospital Management System</font>", styles["Normal"]),
            Paragraph(f"<b><font size=13 color='#00D4FF'>INVOICE #{data.get('bill_id','—')}</font></b><br/>"
                      f"<font size=9 color='#8B9EC7'>Date: {datetime.now().strftime('%d %b %Y')}</font>", right),
        ]], colWidths=[10*cm, 8*cm])
        ht.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),NAVY),
                                 ("TOPPADDING",(0,0),(-1,-1),14),("BOTTOMPADDING",(0,0),(-1,-1),14),
                                 ("LEFTPADDING",(0,0),(-1,-1),14),("RIGHTPADDING",(0,0),(-1,-1),14)]))
        story += [ht, Spacer(1,12)]

        def infoblock(title, lines):
            t = f"<b><font color='#00D4FF' size=9>{title}</font></b><br/>"
            for l in lines: t += f"<font size=9 color='#C5D0E6'>{l}</font><br/>"
            return Paragraph(t, styles["Normal"])

        it = Table([[
            infoblock("PATIENT", [f"Name: {data.get('patient_name','—')}",
                                   f"Phone: {data.get('patient_phone','—')}",
                                   f"Address: {data.get('patient_address','—')}"]),
            infoblock("SERVICE", [f"Doctor: {data.get('doctor_name','—')}",
                                   f"Date: {data.get('appointment_date','—')}",
                                   f"Status: {data.get('payment_status','Pending')}"]),
        ]], colWidths=[9*cm, 9*cm])
        it.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),rlcolors.HexColor("#111827")),
            ("BOX",(0,0),(-1,-1),0.5,BORDER_C),("INNERGRID",(0,0),(-1,-1),0.5,BORDER_C),
            ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
            ("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
        ]))
        story += [it, Spacer(1,12)]

        total = float(data.get("total", 0)); paid = float(data.get("paid", 0)); bal = total - paid
        cs = ParagraphStyle("cs", parent=styles["Normal"], fontSize=9, textColor=rlcolors.white, alignment=TA_CENTER)
        ce = ParagraphStyle("ce", parent=styles["Normal"], fontSize=9, textColor=rlcolors.HexColor("#C5D0E6"))
        tdata = [[Paragraph(h,cs) for h in ["#","Description","Qty","Rate (Rs.)","Amount (Rs.)"]],
                 [Paragraph("1",ce), Paragraph(data.get("description","Medical Services"),ce),
                  Paragraph("1",ce), Paragraph(f"{total:,.2f}",ce), Paragraph(f"{total:,.2f}",ce)]]
        tbl = Table(tdata, colWidths=[1*cm,8.5*cm,2*cm,3.5*cm,3.5*cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),rlcolors.HexColor("#0D1526")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[rlcolors.HexColor("#131D30"),rlcolors.HexColor("#0F1825")]),
            ("BOX",(0,0),(-1,-1),0.5,BORDER_C),("INNERGRID",(0,0),(-1,-1),0.3,BORDER_C),
            ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
            ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),("ALIGN",(1,0),(1,-1),"LEFT"),
        ]))
        story += [tbl, Spacer(1,10)]

        tr = ParagraphStyle("tr", parent=styles["Normal"], fontSize=9, textColor=rlcolors.HexColor("#C5D0E6"), alignment=TA_RIGHT)
        totals = [["Subtotal",f"Rs. {total:,.2f}"],["TOTAL",f"Rs. {total:,.2f}"],
                  ["Paid",f"Rs. {paid:,.2f}"],["Balance Due",f"Rs. {bal:,.2f}"]]
        ttbl = Table([[Paragraph(r,tr),Paragraph(v,tr)] for r,v in totals], colWidths=[13.5*cm,5*cm])
        ttbl.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),rlcolors.HexColor("#111827")),
            ("BACKGROUND",(0,1),(-1,1),rlcolors.HexColor("#0D1E3D")),
            ("BACKGROUND",(0,3),(-1,3),rlcolors.HexColor("#1A3010") if bal==0 else rlcolors.HexColor("#3D1010")),
            ("BOX",(0,0),(-1,-1),0.5,BORDER_C),("INNERGRID",(0,0),(-1,-1),0.3,BORDER_C),
            ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
            ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
        ]))
        story += [ttbl, Spacer(1,16),
                  HRFlowable(width="100%",thickness=0.5,color=BORDER_C), Spacer(1,6),
                  Paragraph("<font size=8 color='#8B9EC7'>Thank you for choosing MediCore. "
                             "Contact: support@medicore.com | +91-9999999999</font>", center)]
        doc.build(story)
        return buf.getvalue()
    except Exception as e:
        return f"PDF Error: {e}".encode()

# ══════════════════════════════════════════════════════════════
#  STREAMLIT CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(page_title="MediCore Hospital", page_icon="🏥",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0A0F1E;}
[data-testid="stSidebar"]{background:#080D1A;border-right:1px solid #1E3050;}
.stButton>button{background:#00D4FF;color:#000;font-weight:bold;border:none;border-radius:8px;}
.stButton>button:hover{background:#00b8d9;}
div[data-testid="metric-container"]{background:#1A2235;border:1px solid #1E3050;border-radius:10px;padding:16px;}
div[data-testid="metric-container"] label{color:#8B9EC7 !important;}
div[data-testid="metric-container"] div{color:#00D4FF !important;}
h1,h2,h3{color:#00D4FF !important;}
.stTabs [data-baseweb="tab"]{background:#111827;color:#8B9EC7;border-radius:8px 8px 0 0;}
.stTabs [aria-selected="true"]{background:#1A2235;color:#00D4FF !important;border-bottom:2px solid #00D4FF;}
footer{display:none;}#MainMenu{display:none;}
</style>""", unsafe_allow_html=True)

init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# ══════════════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════════════
def login_page():
    _, col, _ = st.columns([1,1.2,1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center;padding:30px;background:#111827;
             border-radius:16px;border:1px solid #1E3050;'>
          <div style='font-size:56px;'>🏥</div>
          <h1 style='color:#00D4FF;margin:0;font-size:28px;'>MediCore</h1>
          <p style='color:#8B9EC7;'>Hospital Management System</p>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("lf"):
            u = st.text_input("👤 Username", placeholder="Enter username")
            p = st.text_input("🔒 Password", placeholder="Enter password", type="password")
            if st.form_submit_button("🔐  LOGIN", use_container_width=True):
                user = db_login(u, p)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password!")

        st.markdown("""
        <div style='background:#0D1526;border-radius:10px;padding:14px;
             border:1px solid #1E3050;margin-top:12px;font-size:12px;'>
          <b style='color:#8B9EC7;'>Default Accounts:</b><br>
          <code style='color:#00D4FF;'>admin</code> / <code style='color:#00FF9F;'>admin123</code>
          <span style='color:#8B9EC7;'> [Admin]</span><br>
          <code style='color:#00D4FF;'>doctor1</code> / <code style='color:#00FF9F;'>doc123</code>
          <span style='color:#8B9EC7;'> [Doctor]</span><br>
          <code style='color:#00D4FF;'>receptionist</code> / <code style='color:#00FF9F;'>rec123</code>
          <span style='color:#8B9EC7;'> [Receptionist]</span>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════
def sidebar_nav(user):
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:14px 8px;border-bottom:1px solid #1E3050;margin-bottom:10px;'>
          <div style='font-size:20px;font-weight:bold;color:#00D4FF;'>🏥 MediCore</div>
          <div style='font-size:11px;color:#8B9EC7;margin-top:4px;'>
            {user['full_name']}<br>
            <span style='background:#1A2235;padding:2px 8px;border-radius:10px;
            color:#00FF9F;font-size:10px;'>{user['role'].upper()}</span>
          </div>
        </div>""", unsafe_allow_html=True)

        all_pages = [("🏠","Dashboard"),("👥","Patients"),("👨‍⚕️","Doctors"),
                     ("📅","Appointments"),("💰","Billing"),("💊","Inventory"),
                     ("👷","Staff"),("📊","Reports"),("👤","Users")]
        pages  = [(i,l) for i,l in all_pages if can(user["role"], l.lower())]
        labels = [f"{i}  {l}" for i,l in pages]

        if "page" not in st.session_state or st.session_state.page not in labels:
            st.session_state.page = labels[0]

        choice = st.radio("Navigate", labels, label_visibility="collapsed",
                          index=labels.index(st.session_state.page))
        st.session_state.page = choice
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
    return choice.split("  ", 1)[1].strip() if "  " in choice else choice.strip()

# ══════════════════════════════════════════════════════════════
#  PAGES
# ══════════════════════════════════════════════════════════════
def page_dashboard():
    st.title("📊 Dashboard Overview")
    s = get_stats()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("👥 Total Patients",      s["patients"])
    c2.metric("👨‍⚕️ Total Doctors",       s["doctors"])
    c3.metric("📅 Today Appointments",  s["today_apts"])
    c4.metric("🗓️ Total Appointments",   s["appointments"])
    c5,c6,c7,c8 = st.columns(4)
    c5.metric("💰 Revenue",  f"Rs.{s['revenue']:.0f}")
    c6.metric("⚠️ Pending Bills",       s["pending"])
    c7.metric("💊 Low Stock",           s["low_stock"])
    c8.metric("👷 Staff",               s["staff"])
    st.markdown("---")
    st.subheader("📋 Recent Appointments")
    rows = fetch("""SELECT a.appointment_id id, p.name patient, d.name doctor,
        d.specialization, a.appointment_date date, a.appointment_time time, a.status
        FROM appointments a JOIN patients p ON a.patient_id=p.patient_id
        JOIN doctors d ON a.doctor_id=d.doctor_id ORDER BY a.created_at DESC LIMIT 10""")
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: st.info("No appointments yet.")

def page_patients():
    st.title("👥 Patient Records")
    tab1, tab2 = st.tabs(["📋 View Records", "➕ Add Patient"])
    with tab1:
        search = st.text_input("🔍 Search name / phone / ID")
        rows = fetch("SELECT * FROM patients WHERE name LIKE ? OR phone LIKE ? OR CAST(patient_id AS TEXT)=?",
                     (f"%{search}%",f"%{search}%",search)) if search else fetch("SELECT * FROM patients ORDER BY created_at DESC")
        if rows:
            df = pd.DataFrame(rows)[["patient_id","name","age","gender","blood_group","phone","email","address","medical_history"]]
            df.columns=["ID","Name","Age","Gender","Blood","Phone","Email","Address","History"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total: {len(rows)}")
        else: st.info("No patients found.")
        del_id = st.number_input("Patient ID to delete", min_value=1, step=1, key="dp")
        if st.button("🗑️ Delete Patient"):
            run("DELETE FROM patients WHERE patient_id=?", (del_id,))
            st.success("Deleted!"); st.rerun()
    with tab2:
        with st.form("pf"):
            c1,c2,c3,c4 = st.columns(4)
            name  = c1.text_input("Name *")
            age   = c2.number_input("Age", 0, 150, 25)
            gender= c3.selectbox("Gender", ["Male","Female","Other"])
            blood = c4.selectbox("Blood Group", ["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"])
            c5,c6 = st.columns(2)
            phone = c5.text_input("Phone"); email = c6.text_input("Email")
            addr  = st.text_input("Address")
            hist  = st.text_area("Medical History", height=80)
            if st.form_submit_button("💾 Save Patient", use_container_width=True):
                if not name: st.error("Name required!")
                else:
                    run("INSERT INTO patients(name,age,gender,blood_group,phone,email,address,medical_history) VALUES(?,?,?,?,?,?,?,?)",
                        (name,age,gender,blood,phone,email,addr,hist))
                    st.success(f"✅ Patient '{name}' added!"); st.rerun()

def page_doctors():
    st.title("👨‍⚕️ Doctor Management")
    tab1, tab2 = st.tabs(["📋 View Doctors", "➕ Add Doctor"])
    with tab1:
        search = st.text_input("🔍 Search")
        rows = fetch("SELECT * FROM doctors WHERE name LIKE ? OR specialization LIKE ?",
                     (f"%{search}%",f"%{search}%")) if search else fetch("SELECT * FROM doctors ORDER BY name")
        if rows:
            df = pd.DataFrame(rows)[["doctor_id","name","specialization","phone","experience","fee","available"]]
            df.columns=["ID","Name","Specialization","Phone","Exp(yrs)","Fee Rs.","Available"]
            df["Available"]=df["Available"].map({1:"Yes",0:"No"})
            st.dataframe(df, use_container_width=True, hide_index=True)
        del_id = st.number_input("Doctor ID to delete", min_value=1, step=1, key="dd")
        if st.button("🗑️ Delete Doctor"):
            run("DELETE FROM doctors WHERE doctor_id=?", (del_id,))
            st.success("Deleted!"); st.rerun()
    with tab2:
        specs=["Cardiology","Neurology","Orthopedics","Pediatrics","Dermatology",
               "Gynecology","General Medicine","Ophthalmology","Dentistry","Psychiatry"]
        with st.form("df"):
            c1,c2=st.columns(2)
            name=c1.text_input("Name *"); spec=c2.selectbox("Specialization",specs)
            c3,c4=st.columns(2)
            phone=c3.text_input("Phone"); email=c4.text_input("Email")
            c5,c6,c7=st.columns(3)
            exp=c5.number_input("Experience(yrs)",0,60,5)
            fee=c6.number_input("Fee Rs.",0.0,100000.0,500.0)
            avail=c7.selectbox("Available",["Yes","No"])
            if st.form_submit_button("💾 Save Doctor", use_container_width=True):
                if not name: st.error("Name required!")
                else:
                    run("INSERT INTO doctors(name,specialization,phone,email,experience,fee,available) VALUES(?,?,?,?,?,?,?)",
                        (name,spec,phone,email,exp,fee,1 if avail=="Yes" else 0))
                    st.success(f"✅ Dr. {name} added!"); st.rerun()

def page_appointments():
    st.title("📅 Appointment Booking")
    tab1,tab2,tab3 = st.tabs(["📋 All","➕ Book","✏️ Update"])
    with tab1:
        rows=fetch("""SELECT a.appointment_id id, p.name patient, d.name doctor,
            d.specialization spec, a.appointment_date date, a.appointment_time time,
            a.reason, a.status FROM appointments a
            JOIN patients p ON a.patient_id=p.patient_id
            JOIN doctors  d ON a.doctor_id=d.doctor_id
            ORDER BY a.appointment_date DESC""")
        if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else: st.info("No appointments yet.")
    with tab2:
        patients=fetch("SELECT patient_id,name FROM patients ORDER BY name")
        doctors =fetch("SELECT doctor_id,name,specialization FROM doctors ORDER BY name")
        if not patients: st.warning("Add patients first!"); return
        if not doctors:  st.warning("Add doctors first!");  return
        p_opts={f"{r['patient_id']} – {r['name']}":r['patient_id'] for r in patients}
        d_opts={f"{r['doctor_id']} – {r['name']} ({r['specialization']})":r['doctor_id'] for r in doctors}
        with st.form("af"):
            c1,c2=st.columns(2)
            ps=c1.selectbox("Patient *",list(p_opts.keys()))
            ds=c2.selectbox("Doctor *",list(d_opts.keys()))
            c3,c4=st.columns(2)
            dt=c3.date_input("Date *",value=date.today())
            tm=c4.text_input("Time (HH:MM)","10:00")
            reason=st.text_input("Reason")
            if st.form_submit_button("📅 Book Appointment", use_container_width=True):
                run("INSERT INTO appointments(patient_id,doctor_id,appointment_date,appointment_time,reason) VALUES(?,?,?,?,?)",
                    (p_opts[ps],d_opts[ds],str(dt),tm,reason))
                st.success("✅ Booked!"); st.rerun()
    with tab3:
        aid=st.number_input("Appointment ID",min_value=1,step=1)
        ns=st.selectbox("New Status",["Scheduled","Completed","Cancelled","No Show"])
        notes=st.text_input("Notes")
        c1,c2=st.columns(2)
        if c1.button("✅ Update Status",use_container_width=True):
            run("UPDATE appointments SET status=?,notes=? WHERE appointment_id=?",(ns,notes,aid))
            st.success("Updated!"); st.rerun()
        if c2.button("🗑️ Delete",use_container_width=True):
            run("DELETE FROM appointments WHERE appointment_id=?",(aid,))
            st.success("Deleted!"); st.rerun()

def page_billing():
    st.title("💰 Billing & Payments")
    tab1,tab2=st.tabs(["📋 All Bills","➕ Generate Bill"])
    with tab1:
        rows=fetch("""SELECT b.bill_id, p.name patient, b.amount, b.paid,
            b.payment_status status, b.bill_date date, b.description
            FROM billing b JOIN patients p ON b.patient_id=p.patient_id
            ORDER BY b.bill_date DESC""")
        if rows:
            df=pd.DataFrame(rows)
            df["amount"]=df["amount"].apply(lambda x:f"Rs.{x:,.2f}")
            df["paid"]  =df["paid"].apply(lambda x:f"Rs.{x:,.2f}")
            st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("---")
        st.subheader("🖨️ Download PDF Bill")
        bid=st.number_input("Bill ID",min_value=1,step=1,key="pbid")
        if st.button("Generate PDF",key="pdfbtn"):
            raw=fetch("""SELECT b.*,p.name pn,p.phone pp,p.address pa
                FROM billing b JOIN patients p ON b.patient_id=p.patient_id
                WHERE b.bill_id=?""",(bid,))
            if raw:
                r=raw[0]
                pdf=generate_pdf({"bill_id":r["bill_id"],"patient_name":r["pn"],
                    "patient_phone":r["pp"],"patient_address":r["pa"],
                    "doctor_name":"—","appointment_date":"—",
                    "total":r["amount"],"paid":r["paid"],
                    "payment_status":r["payment_status"],
                    "description":r["description"] or "Medical Services"})
                st.download_button("⬇️ Download PDF",pdf,f"Bill_{bid}.pdf","application/pdf",use_container_width=True)
            else: st.error("Bill not found!")
    with tab2:
        patients=fetch("SELECT patient_id,name FROM patients ORDER BY name")
        if not patients: st.warning("Add patients first!"); return
        p_opts={f"{r['patient_id']} – {r['name']}":r['patient_id'] for r in patients}
        with st.form("bf"):
            c1,c2=st.columns(2)
            ps=c1.selectbox("Patient *",list(p_opts.keys()))
            c3,c4=st.columns(2)
            amount=c3.number_input("Total Amount Rs.*",0.0,1000000.0,500.0)
            paid_a=c4.number_input("Amount Paid Rs.",0.0,1000000.0,0.0)
            desc=st.text_input("Description")
            if st.form_submit_button("🧾 Generate Bill", use_container_width=True):
                status="Paid" if paid_a>=amount else ("Partial" if paid_a>0 else "Pending")
                run("INSERT INTO billing(patient_id,amount,paid,payment_status,description) VALUES(?,?,?,?,?)",
                    (p_opts[ps],amount,paid_a,status,desc))
                st.success(f"✅ Bill generated — {status}"); st.rerun()

def page_inventory():
    st.title("💊 Medicine & Inventory")
    tab1,tab2=st.tabs(["📦 View","➕ Add Item"])
    with tab1:
        rows=fetch("SELECT * FROM inventory ORDER BY item_name")
        if rows:
            df=pd.DataFrame(rows)[["item_id","item_name","category","quantity","unit_price","supplier","expiry_date"]]
            df.columns=["ID","Item","Category","Qty","Price Rs.","Supplier","Expiry"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            low=[r for r in rows if r["quantity"]<50]
            if low: st.warning(f"⚠️ {len(low)} item(s) low on stock!")
        iid=st.number_input("Item ID to delete",min_value=1,step=1,key="di")
        if st.button("🗑️ Delete Item"):
            run("DELETE FROM inventory WHERE item_id=?",(iid,)); st.success("Deleted!"); st.rerun()
    with tab2:
        cats=["Medicine","Equipment","Consumable","Surgical","Diagnostic"]
        with st.form("if"):
            c1,c2=st.columns(2)
            name=c1.text_input("Item Name *"); cat=c2.selectbox("Category",cats)
            c3,c4,c5=st.columns(3)
            qty=c3.number_input("Quantity",0,100000,100)
            price=c4.number_input("Unit Price Rs.",0.0,100000.0,10.0)
            supp=c5.text_input("Supplier")
            expiry=st.text_input("Expiry (YYYY-MM-DD)")
            if st.form_submit_button("💾 Add Item", use_container_width=True):
                if not name: st.error("Name required!")
                else:
                    run("INSERT INTO inventory(item_name,category,quantity,unit_price,supplier,expiry_date) VALUES(?,?,?,?,?,?)",
                        (name,cat,qty,price,supp,expiry))
                    st.success("✅ Added!"); st.rerun()

def page_staff():
    st.title("👷 Staff Management")
    tab1,tab2=st.tabs(["📋 View Staff","➕ Add Staff"])
    with tab1:
        rows=fetch("SELECT * FROM staff ORDER BY name")
        if rows:
            df=pd.DataFrame(rows)[["staff_id","name","role","phone","salary","shift"]]
            df.columns=["ID","Name","Role","Phone","Salary Rs.","Shift"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        sid=st.number_input("Staff ID to delete",min_value=1,step=1,key="ds")
        if st.button("🗑️ Delete Staff"):
            run("DELETE FROM staff WHERE staff_id=?",(sid,)); st.success("Deleted!"); st.rerun()
    with tab2:
        roles=["Nurse","Receptionist","Pharmacist","Lab Technician","Security","Cleaner","Admin"]
        shifts=["Morning","Evening","Night","Rotating"]
        with st.form("sf"):
            c1,c2=st.columns(2)
            name=c1.text_input("Full Name *"); role=c2.selectbox("Role",roles)
            c3,c4,c5=st.columns(3)
            phone=c3.text_input("Phone")
            salary=c4.number_input("Salary Rs.",0.0,1000000.0,30000.0)
            shift=c5.selectbox("Shift",shifts)
            if st.form_submit_button("💾 Add Staff", use_container_width=True):
                if not name: st.error("Name required!")
                else:
                    run("INSERT INTO staff(name,role,phone,salary,shift) VALUES(?,?,?,?,?)",(name,role,phone,salary,shift))
                    st.success(f"✅ {name} added!"); st.rerun()

def page_reports():
    st.title("📊 Reports & Analytics")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("""<div style='background:#1A2235;border:1px solid #1E3050;
            border-radius:10px;padding:16px;'>
            <h3 style='color:#00D4FF;'>📊 Dashboard Report</h3>
            <p style='color:#8B9EC7;font-size:13px;'>8 charts — appointments, revenue,
            doctors, blood groups, gender, age groups, top doctors</p></div>""",
            unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("Generate Dashboard Report", use_container_width=True, key="r1"):
            with st.spinner("Generating..."):
                buf=dashboard_chart()
            st.image(buf, use_container_width=True)
            st.download_button("⬇️ Download PNG",buf.getvalue(),"dashboard.png","image/png",use_container_width=True)
    with c2:
        st.markdown("""<div style='background:#1A2235;border:1px solid #1E3050;
            border-radius:10px;padding:16px;'>
            <h3 style='color:#7B61FF;'>👥 Patient Analytics</h3>
            <p style='color:#8B9EC7;font-size:13px;'>Monthly new patients (12 months)
            + age group distribution</p></div>""",
            unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("Generate Patient Report", use_container_width=True, key="r2"):
            with st.spinner("Generating..."):
                buf=patient_chart()
            st.image(buf, use_container_width=True)
            st.download_button("⬇️ Download PNG",buf.getvalue(),"patients.png","image/png",use_container_width=True)

def page_users():
    st.title("👤 User Management")
    rows=fetch("SELECT user_id,username,role,full_name,email,active FROM users")
    if rows:
        df=pd.DataFrame(rows)
        df["active"]=df["active"].map({1:"Yes",0:"No"})
        st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")
    st.subheader("➕ Add New User")
    with st.form("uf"):
        c1,c2,c3=st.columns(3)
        uname=c1.text_input("Username *")
        upass=c2.text_input("Password *",type="password")
        urole=c3.selectbox("Role",["admin","doctor","receptionist"])
        c4,c5=st.columns(2)
        fname=c4.text_input("Full Name"); email=c5.text_input("Email")
        if st.form_submit_button("💾 Add User", use_container_width=True):
            if not (uname and upass): st.error("Username & password required!")
            else:
                h=hashlib.sha256(upass.encode()).hexdigest()
                try:
                    run("INSERT INTO users(username,password,role,full_name,email) VALUES(?,?,?,?,?)",(uname,h,urole,fname,email))
                    st.success(f"✅ User '{uname}' added!"); st.rerun()
                except Exception as e: st.error(f"Error: {e}")
    st.markdown("---")
    uid=st.number_input("User ID to delete",min_value=1,step=1)
    if st.button("🗑️ Delete User"):
        run("DELETE FROM users WHERE user_id=?",(uid,)); st.success("Deleted!"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  MAIN ROUTER
# ══════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    login_page()
else:
    user = st.session_state.user
    page = sidebar_nav(user)
    router = {
        "Dashboard":    page_dashboard,
        "Patients":     page_patients,
        "Doctors":      page_doctors,
        "Appointments": page_appointments,
        "Billing":      page_billing,
        "Inventory":    page_inventory,
        "Staff":        page_staff,
        "Reports":      page_reports,
        "Users":        page_users,
    }
    fn = router.get(page)
    if fn:
        if can(user["role"], page.lower()): fn()
        else: st.error(f"🚫 Access Denied — {user['role']} cannot access {page}.")
    else:
        page_dashboard()
