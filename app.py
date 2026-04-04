"""
╔══════════════════════════════════════════════════════════════╗
║  MediCore Hospital Management System — FINAL COMPLETE v3.0  ║
║  Database: Supabase PostgreSQL (Permanent)                   ║
║  All Features: Login, CRUD, Reports, PDF, Charts, RBAC      ║
╚══════════════════════════════════════════════════════════════╝
"""
import os, io, hashlib, socket
from datetime import datetime, date, timedelta
from urllib.parse import urlparse

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# ══════════════════════════════════════════════════════════════
#  SUPABASE DATABASE CONNECTION
# ══════════════════════════════════════════════════════════════
import psycopg2
from psycopg2.extras import RealDictCursor

def _ipv4_hostaddr_for_database_url(url: str):
    """
    Resolve DB host to IPv4 only. Streamlit Cloud and similar hosts often have no
    working IPv6 egress; Supabase may resolve to IPv6 first, causing
    'Cannot assign requested address'. libpq still uses the URL hostname for SSL.
    """
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        if not host or host in ("localhost", "127.0.0.1", "::1"):
            return None
        port = parsed.port or 5432
        infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        if not infos:
            return None
        return infos[0][4][0]
    except (socket.gaierror, OSError, ValueError):
        return None

def get_conn():
    """One PostgreSQL connection per browser session (not shared across users)."""
    url = st.secrets["DATABASE_URL"]
    conn = st.session_state.get("_pg_conn")
    if conn is not None and conn.closed:
        st.session_state.pop("_pg_conn", None)
        conn = None
    if conn is None:
        kw = dict(
            cursor_factory=RealDictCursor,
            connect_timeout=10,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
        )
        hostaddr = _ipv4_hostaddr_for_database_url(url)
        if hostaddr:
            kw["hostaddr"] = hostaddr
        conn = psycopg2.connect(url, **kw)
        conn.autocommit = False
        st.session_state["_pg_conn"] = conn
    return conn

def _drop_db_conn():
    old = st.session_state.pop("_pg_conn", None)
    if old is not None and not old.closed:
        try:
            old.close()
        except Exception:
            pass

def execute(sql, params=(), fetch_results=False):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch_results:
                rows = cur.fetchall()
                conn.commit()
                return [dict(r) for r in rows]
            conn.commit()
            return []
    except psycopg2.OperationalError:
        # Connection dropped — reconnect once for this session
        _drop_db_conn()
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch_results:
                rows = cur.fetchall()
                conn.commit()
                return [dict(r) for r in rows]
            conn.commit()
            return []
    except Exception as e:
        try: get_conn().rollback()
        except: pass
        st.error(f"❌ Database Error: {e}")
        return []

def fetch(sql, params=()):
    return execute(sql, params, fetch_results=True)

def run(sql, params=()):
    execute(sql, params, fetch_results=False)

# ── Database Initialization ──────────────────────────────────
def init_db():
    conn = get_conn()
    try:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id   SERIAL PRIMARY KEY,
                    username  TEXT UNIQUE NOT NULL,
                    password  TEXT NOT NULL,
                    role      TEXT NOT NULL CHECK(role IN ('admin','doctor','receptionist')),
                    full_name TEXT DEFAULT '',
                    email     TEXT DEFAULT '',
                    active    INTEGER DEFAULT 1,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id   SERIAL PRIMARY KEY,
                    name         TEXT NOT NULL,
                    age          INTEGER DEFAULT 0,
                    gender       TEXT DEFAULT 'Male',
                    blood_group  TEXT DEFAULT '',
                    phone        TEXT DEFAULT '',
                    email        TEXT DEFAULT '',
                    address      TEXT DEFAULT '',
                    medical_history TEXT DEFAULT '',
                    created_at   TIMESTAMPTZ DEFAULT NOW()
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS doctors (
                    doctor_id      SERIAL PRIMARY KEY,
                    name           TEXT NOT NULL,
                    specialization TEXT DEFAULT '',
                    phone          TEXT DEFAULT '',
                    email          TEXT DEFAULT '',
                    experience     INTEGER DEFAULT 0,
                    fee            REAL DEFAULT 0,
                    available      INTEGER DEFAULT 1,
                    created_at     TIMESTAMPTZ DEFAULT NOW()
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    appointment_id   SERIAL PRIMARY KEY,
                    patient_id       INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
                    doctor_id        INTEGER REFERENCES doctors(doctor_id) ON DELETE CASCADE,
                    appointment_date TEXT DEFAULT '',
                    appointment_time TEXT DEFAULT '',
                    reason           TEXT DEFAULT '',
                    status           TEXT DEFAULT 'Scheduled',
                    notes            TEXT DEFAULT '',
                    created_at       TIMESTAMPTZ DEFAULT NOW()
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS billing (
                    bill_id        SERIAL PRIMARY KEY,
                    patient_id     INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
                    appointment_id INTEGER DEFAULT NULL,
                    amount         REAL DEFAULT 0,
                    paid           REAL DEFAULT 0,
                    payment_status TEXT DEFAULT 'Pending',
                    description    TEXT DEFAULT '',
                    bill_date      TIMESTAMPTZ DEFAULT NOW()
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    item_id     SERIAL PRIMARY KEY,
                    item_name   TEXT NOT NULL,
                    category    TEXT DEFAULT 'Medicine',
                    quantity    INTEGER DEFAULT 0,
                    unit_price  REAL DEFAULT 0,
                    supplier    TEXT DEFAULT '',
                    expiry_date TEXT DEFAULT '',
                    created_at  TIMESTAMPTZ DEFAULT NOW()
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS staff (
                    staff_id   SERIAL PRIMARY KEY,
                    name       TEXT NOT NULL,
                    role       TEXT DEFAULT '',
                    phone      TEXT DEFAULT '',
                    salary     REAL DEFAULT 0,
                    shift      TEXT DEFAULT 'Morning',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )""")
        conn.commit()

        def _h(p): return hashlib.sha256(p.encode()).hexdigest()

        # Seed users
        r = fetch("SELECT COUNT(*) as cnt FROM users")
        if r and r[0]["cnt"] == 0:
            for u,p,role,fn,em in [
                ("admin",       _h("admin123"),"admin",        "Administrator",   "admin@hospital.com"),
                ("doctor1",     _h("doc123"),  "doctor",       "Dr. Arjun Sharma","arjun@hospital.com"),
                ("receptionist",_h("rec123"),  "receptionist", "Sunita Devi",     "rec@hospital.com"),
            ]:
                run("INSERT INTO users(username,password,role,full_name,email) VALUES(%s,%s,%s,%s,%s)",
                    (u,p,role,fn,em))

        # Seed doctors
        r = fetch("SELECT COUNT(*) as cnt FROM doctors")
        if r and r[0]["cnt"] == 0:
            for nm,sp,ph,em,exp,fee in [
                ("Dr. Arjun Sharma","Cardiology","9876543210","arjun@h.com",15,1500),
                ("Dr. Priya Mehta","Neurology","9876543211","priya@h.com",12,1800),
                ("Dr. Ravi Kumar","Orthopedics","9876543212","ravi@h.com",10,1200),
                ("Dr. Sunita Verma","Pediatrics","9876543213","sunita@h.com",8,1000),
                ("Dr. Anil Patel","General Medicine","9876543214","anil@h.com",20,800),
                ("Dr. Kavita Singh","Gynecology","9876543215","kavita@h.com",14,1600),
                ("Dr. Manish Gupta","Dermatology","9876543216","manish@h.com",6,900),
                ("Dr. Neha Joshi","Ophthalmology","9876543217","neha@h.com",9,1100),
            ]:
                run("INSERT INTO doctors(name,specialization,phone,email,experience,fee) VALUES(%s,%s,%s,%s,%s,%s)",
                    (nm,sp,ph,em,exp,fee))

        # Seed patients
        r = fetch("SELECT COUNT(*) as cnt FROM patients")
        if r and r[0]["cnt"] == 0:
            for nm,ag,gn,bg,ph,em,addr,hist in [
                ("Rahul Verma",32,"Male","B+","9811234567","rahul@mail.com","Delhi","Hypertension"),
                ("Anjali Gupta",28,"Female","O+","9822345678","anjali@mail.com","Mumbai","Diabetes"),
                ("Suresh Patel",45,"Male","A+","9833456789","suresh@mail.com","Pune","Asthma"),
                ("Meena Sharma",35,"Female","AB-","9844567890","meena@mail.com","Jaipur","None"),
                ("Vikram Singh",52,"Male","O-","9855678901","vikram@mail.com","Lucknow","Heart Disease"),
            ]:
                run("INSERT INTO patients(name,age,gender,blood_group,phone,email,address,medical_history) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                    (nm,ag,gn,bg,ph,em,addr,hist))

        # Seed inventory
        r = fetch("SELECT COUNT(*) as cnt FROM inventory")
        if r and r[0]["cnt"] == 0:
            for nm,cat,qty,pr,sup,exp in [
                ("Paracetamol 500mg","Medicine",500,2.5,"MedCorp","2026-12-31"),
                ("Amoxicillin 250mg","Medicine",30,5.0,"PharmaCo","2026-06-30"),
                ("Surgical Gloves","Equipment",200,15.0,"MediSupply","2027-01-01"),
                ("Syringes 5ml","Equipment",400,3.0,"HealthKit","2027-06-01"),
                ("Bandages","Consumable",25,8.0,"CareSupply","2026-09-30"),
            ]:
                run("INSERT INTO inventory(item_name,category,quantity,unit_price,supplier,expiry_date) VALUES(%s,%s,%s,%s,%s,%s)",
                    (nm,cat,qty,pr,sup,exp))

        # Seed staff
        r = fetch("SELECT COUNT(*) as cnt FROM staff")
        if r and r[0]["cnt"] == 0:
            for nm,role,ph,sal,sh in [
                ("Ramesh Yadav","Nurse","9900011111",35000,"Morning"),
                ("Sunita Devi","Receptionist","9900022222",28000,"Morning"),
                ("Mohan Lal","Pharmacist","9900033333",40000,"Evening"),
                ("Geeta Kumari","Lab Technician","9900044444",38000,"Night"),
            ]:
                run("INSERT INTO staff(name,role,phone,salary,shift) VALUES(%s,%s,%s,%s,%s)",
                    (nm,role,ph,sal,sh))

    except Exception as e:
        st.error(f"Init error: {e}")
        try: conn.rollback()
        except: pass

# ── Auth & RBAC ──────────────────────────────────────────────
def db_login(username, password):
    h = hashlib.sha256(password.encode()).hexdigest()
    rows = fetch("SELECT * FROM users WHERE username=%s AND password=%s AND active=1",(username,h))
    return rows[0] if rows else None

PERMISSIONS = {
    "admin":        {"dashboard","patients","doctors","appointments","billing","inventory","staff","reports","users"},
    "doctor":       {"dashboard","patients","appointments","reports"},
    "receptionist": {"dashboard","patients","appointments","billing","inventory"},
}
def can(role, mod): return mod in PERMISSIONS.get(role, set())

# ── Stats ────────────────────────────────────────────────────
def get_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    def val(sql, params=()):
        r = fetch(sql, params)
        if not r: return 0
        v = list(r[0].values())[0]
        return v if v else 0
    return {
        "patients":     val("SELECT COUNT(*) FROM patients"),
        "doctors":      val("SELECT COUNT(*) FROM doctors"),
        "appointments": val("SELECT COUNT(*) FROM appointments"),
        "today_apts":   val("SELECT COUNT(*) FROM appointments WHERE appointment_date=%s",(today,)),
        "revenue":      val("SELECT COALESCE(SUM(paid),0) FROM billing"),
        "pending":      val("SELECT COUNT(*) FROM billing WHERE payment_status='Pending'"),
        "low_stock":    val("SELECT COUNT(*) FROM inventory WHERE quantity<50"),
        "staff":        val("SELECT COUNT(*) FROM staff"),
    }

# ══════════════════════════════════════════════════════════════
#  CHARTS — Matplotlib Dark Theme
# ══════════════════════════════════════════════════════════════
BG="#0A0F1E"; CARD="#1A2235"; BORDER="#1E3050"
PAL=["#00D4FF","#7B61FF","#00FF9F","#FF6B6B","#FFB347","#FF85C2","#85FFD4","#FFD485"]

def _ax(ax, title=""):
    ax.set_facecolor(CARD)
    ax.tick_params(colors="#8B9EC7", labelsize=8)
    for s in ax.spines.values(): s.set_edgecolor(BORDER)
    if title: ax.set_title(title, color="#00D4FF", fontsize=10, fontweight="bold", pad=8)
    ax.grid(axis="y", color=BORDER, linewidth=0.5, linestyle="--", alpha=0.5)

def dashboard_chart():
    months=[]; apts=[]; revs=[]
    for i in range(5,-1,-1):
        d = datetime.now()-timedelta(days=30*i)
        m = d.strftime("%Y-%m")
        months.append(d.strftime("%b"))
        r1 = fetch("SELECT COUNT(*) as c FROM appointments WHERE appointment_date LIKE %s",(f"{m}%",))
        apts.append(r1[0]["c"] if r1 else 0)
        r2 = fetch("SELECT COALESCE(SUM(paid),0) as t FROM billing WHERE bill_date::text LIKE %s",(f"{m}%",))
        revs.append(float(r2[0]["t"]) if r2 else 0.0)

    specs    = fetch("SELECT specialization,COUNT(*) as c FROM doctors GROUP BY specialization ORDER BY c DESC LIMIT 6")
    statuses = fetch("SELECT status,COUNT(*) as c FROM appointments GROUP BY status")
    genders  = fetch("SELECT gender,COUNT(*) as c FROM patients GROUP BY gender")
    blood    = fetch("SELECT blood_group,COUNT(*) as c FROM patients WHERE blood_group!='' GROUP BY blood_group ORDER BY c DESC")
    top_docs = fetch("SELECT d.name,COUNT(a.appointment_id) as c FROM doctors d LEFT JOIN appointments a ON d.doctor_id=a.doctor_id GROUP BY d.doctor_id,d.name ORDER BY c DESC LIMIT 5")

    fig = plt.figure(figsize=(16,10), facecolor=BG)
    fig.suptitle("MediCore — Hospital Analytics Dashboard", color="#00D4FF", fontsize=14, fontweight="bold")
    gs = GridSpec(3,3, figure=fig, hspace=0.55, wspace=0.38, left=0.06, right=0.97, top=0.93, bottom=0.06)

    # Monthly appointments bar
    ax1 = fig.add_subplot(gs[0,:2])
    bars = ax1.bar(months, apts, color="#00D4FF", width=0.5, zorder=3)
    for b,v in zip(bars,apts): ax1.text(b.get_x()+b.get_width()/2, b.get_height()+0.1, str(v), ha="center", color="white", fontsize=9)
    _ax(ax1,"Monthly Appointments (Last 6 Months)")

    # Status donut
    ax2 = fig.add_subplot(gs[0,2])
    if statuses:
        sl=[r["status"] for r in statuses]; sv=[r["c"] for r in statuses]
        w,_ = ax2.pie(sv, colors=PAL[:len(sl)], startangle=90, wedgeprops={"width":0.55,"edgecolor":BG,"linewidth":2})
        ax2.legend(w, sl, loc="lower center", ncol=2, fontsize=7, labelcolor="#8B9EC7", facecolor=CARD, edgecolor=BORDER)
    ax2.set_facecolor(BG); ax2.set_title("Appointment Status", color="#00D4FF", fontsize=10, fontweight="bold")

    # Revenue line
    ax3 = fig.add_subplot(gs[1,:2])
    ax3.plot(months, revs, color="#00FF9F", linewidth=2.5, marker="o", markersize=7, zorder=3)
    ax3.fill_between(range(len(revs)), revs, alpha=0.12, color="#00FF9F")
    mx = max(revs) if revs and max(revs)>0 else 1
    for i,v in enumerate(revs): ax3.text(i, v+mx*0.04, f"Rs{v:.0f}", ha="center", color="white", fontsize=7)
    _ax(ax3,"Monthly Revenue (Rs.)")
    ax3.set_xticks(range(len(months))); ax3.set_xticklabels(months)

    # Doctors by spec
    ax4 = fig.add_subplot(gs[1,2])
    if specs:
        sl=[r["specialization"][:14] for r in specs]; sv=[r["c"] for r in specs]
        ax4.barh(sl, sv, color=PAL[:len(sl)], height=0.6, zorder=3)
        for i,v in enumerate(sv): ax4.text(v+0.05, i, str(v), va="center", color="white", fontsize=7)
    _ax(ax4,"Doctors by Specialization"); ax4.invert_yaxis()

    # Gender pie
    ax5 = fig.add_subplot(gs[2,0])
    if genders:
        gl=[r["gender"] for r in genders]; gv=[r["c"] for r in genders]
        ax5.pie(gv, labels=gl, colors=["#7B61FF","#FF6B6B","#FFB347"][:len(gl)],
                autopct="%1.0f%%", startangle=90,
                textprops={"color":"white","fontsize":9}, wedgeprops={"edgecolor":BG,"linewidth":2})
    ax5.set_facecolor(BG); ax5.set_title("Patient Gender", color="#00D4FF", fontsize=10, fontweight="bold")

    # Blood group
    ax6 = fig.add_subplot(gs[2,1])
    if blood:
        bl=[r["blood_group"] for r in blood]; bv=[r["c"] for r in blood]
        bars6 = ax6.bar(bl, bv, color="#FF6B6B", width=0.6, zorder=3)
        for b,v in zip(bars6,bv): ax6.text(b.get_x()+b.get_width()/2, b.get_height()+0.05, str(v), ha="center", color="white", fontsize=8)
    _ax(ax6,"Blood Group Distribution")

    # Top doctors
    ax7 = fig.add_subplot(gs[2,2])
    if top_docs:
        tl=[r["name"].replace("Dr.","").strip()[:14] for r in top_docs]; tv=[r["c"] for r in top_docs]
        ax7.barh(tl, tv, color="#7B61FF", height=0.6, zorder=3)
        for i,v in enumerate(tv): ax7.text(v+0.05, i, str(v), va="center", color="white", fontsize=7)
    _ax(ax7,"Top Doctors by Appointments"); ax7.invert_yaxis()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor=BG)
    plt.close(fig); buf.seek(0); return buf

def patient_chart():
    months=[]; vals=[]
    for i in range(11,-1,-1):
        d = datetime.now()-timedelta(days=30*i)
        months.append(d.strftime("%b"))
        r = fetch("SELECT COUNT(*) as c FROM patients WHERE created_at::text LIKE %s",(f"{d.strftime('%Y-%m')}%",))
        vals.append(r[0]["c"] if r else 0)
    ag = fetch("""SELECT
        COALESCE(SUM(CASE WHEN age<18 THEN 1 ELSE 0 END),0) as a,
        COALESCE(SUM(CASE WHEN age BETWEEN 18 AND 40 THEN 1 ELSE 0 END),0) as b,
        COALESCE(SUM(CASE WHEN age BETWEEN 41 AND 60 THEN 1 ELSE 0 END),0) as c,
        COALESCE(SUM(CASE WHEN age>60 THEN 1 ELSE 0 END),0) as d FROM patients""")
    agv = [int(ag[0]["a"]),int(ag[0]["b"]),int(ag[0]["c"]),int(ag[0]["d"])] if ag else [0,0,0,0]

    fig = plt.figure(figsize=(13,5), facecolor=BG)
    fig.suptitle("Patient Analytics Report", color="#00D4FF", fontsize=13, fontweight="bold")
    gs = GridSpec(1,2, figure=fig, wspace=0.35, left=0.07, right=0.97, top=0.88, bottom=0.12)

    ax1 = fig.add_subplot(gs[0])
    ax1.fill_between(range(len(vals)), vals, alpha=0.2, color="#00D4FF")
    ax1.plot(range(len(vals)), vals, color="#00D4FF", linewidth=2.5, marker="o", markersize=6)
    ax1.set_xticks(range(len(months))); ax1.set_xticklabels(months, rotation=45, fontsize=7)
    _ax(ax1,"Monthly New Patients (12 Months)")

    ax2 = fig.add_subplot(gs[1])
    agl=["Under 18","18-40 yrs","41-60 yrs","Above 60"]
    ax2.pie(agv, labels=agl, colors=["#00FF9F","#00D4FF","#7B61FF","#FFB347"],
            autopct="%1.0f%%", startangle=90,
            textprops={"color":"white","fontsize":9}, wedgeprops={"edgecolor":BG,"linewidth":2})
    ax2.set_facecolor(BG); ax2.set_title("Patient Age Groups", color="#00D4FF", fontsize=10, fontweight="bold")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor=BG)
    plt.close(fig); buf.seek(0); return buf

# ══════════════════════════════════════════════════════════════
#  PDF BILL GENERATOR
# ══════════════════════════════════════════════════════════════
def generate_pdf(data):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors as rlc
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm,
                                topMargin=1.5*cm, bottomMargin=1.5*cm)
        ss = getSampleStyleSheet(); story = []
        NAVY = rlc.HexColor("#0A0F1E"); BRD = rlc.HexColor("#1E3050")

        def P(txt, align=None, size=None, color=None, bold=False):
            s = ParagraphStyle("x", parent=ss["Normal"],
                               alignment={"c":1,"r":2}.get(align,0),
                               fontSize=size or 10,
                               textColor=rlc.HexColor(color) if color else rlc.black,
                               fontName="Helvetica-Bold" if bold else "Helvetica")
            return Paragraph(txt, s)

        # Header
        ht = Table([[
            P(f"<b><font size=20 color='#00D4FF'>MediCore Hospital</font></b><br/>"
              f"<font size=9 color='#8B9EC7'>Advanced Hospital Management System</font>"),
            P(f"<b><font size=14 color='#00D4FF'>INVOICE #{data.get('bill_id','')}</font></b><br/>"
              f"<font size=9 color='#8B9EC7'>Date: {datetime.now().strftime('%d %b %Y')}</font>","r"),
        ]], colWidths=[10*cm, 8*cm])
        ht.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),NAVY),
            ("TOPPADDING",(0,0),(-1,-1),16),("BOTTOMPADDING",(0,0),(-1,-1),16),
            ("LEFTPADDING",(0,0),(-1,-1),16),("RIGHTPADDING",(0,0),(-1,-1),16),
        ]))
        story += [ht, Spacer(1,14)]

        # Patient info
        def ib(title, lines):
            txt = f"<b><font color='#00D4FF' size=9>{title}</font></b><br/>"
            for l in lines: txt += f"<font size=9 color='#C5D0E6'>{l}</font><br/>"
            return Paragraph(txt, ss["Normal"])

        it = Table([[
            ib("PATIENT DETAILS",[
                f"Name   : {data.get('patient_name','—')}",
                f"Phone  : {data.get('patient_phone','—')}",
                f"Address: {data.get('patient_address','—')}",
            ]),
            ib("SERVICE DETAILS",[
                f"Doctor : {data.get('doctor_name','—')}",
                f"Date   : {data.get('appointment_date','—')}",
                f"Status : {data.get('payment_status','Pending')}",
            ]),
        ]], colWidths=[9*cm, 9*cm])
        it.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),rlc.HexColor("#111827")),
            ("BOX",(0,0),(-1,-1),0.5,BRD),("INNERGRID",(0,0),(-1,-1),0.5,BRD),
            ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
            ("LEFTPADDING",(0,0),(-1,-1),14),("RIGHTPADDING",(0,0),(-1,-1),14),
        ]))
        story += [it, Spacer(1,14)]

        # Items
        total = float(data.get("total",0)); paid = float(data.get("paid",0)); bal = total-paid
        th_s = ParagraphStyle("th",parent=ss["Normal"],fontSize=9,textColor=rlc.white,alignment=1,fontName="Helvetica-Bold")
        td_s = ParagraphStyle("td",parent=ss["Normal"],fontSize=9,textColor=rlc.HexColor("#C5D0E6"))
        tbl = Table([
            [Paragraph(h,th_s) for h in ["#","Description","Qty","Rate (Rs.)","Amount (Rs.)"]],
            [Paragraph("1",td_s),Paragraph(data.get("description","Medical Services"),td_s),
             Paragraph("1",td_s),Paragraph(f"{total:,.2f}",td_s),Paragraph(f"{total:,.2f}",td_s)],
        ], colWidths=[1*cm,8.5*cm,2*cm,3.5*cm,3.5*cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),rlc.HexColor("#0D1526")),
            ("BACKGROUND",(0,1),(-1,1),rlc.HexColor("#131D30")),
            ("BOX",(0,0),(-1,-1),0.5,BRD),("INNERGRID",(0,0),(-1,-1),0.3,BRD),
            ("TOPPADDING",(0,0),(-1,-1),9),("BOTTOMPADDING",(0,0),(-1,-1),9),
            ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),("ALIGN",(1,0),(1,-1),"LEFT"),
        ]))
        story += [tbl, Spacer(1,10)]

        # Totals
        tr_s = ParagraphStyle("tr",parent=ss["Normal"],fontSize=10,textColor=rlc.HexColor("#C5D0E6"),alignment=2)
        totals_data = [
            ["Subtotal",    f"Rs. {total:,.2f}"],
            ["Total Amount",f"Rs. {total:,.2f}"],
            ["Amount Paid", f"Rs. {paid:,.2f}"],
            ["Balance Due", f"Rs. {bal:,.2f}"],
        ]
        tt = Table([[Paragraph(r,tr_s), Paragraph(v,tr_s)] for r,v in totals_data],
                   colWidths=[13.5*cm, 5*cm])
        tt.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),rlc.HexColor("#111827")),
            ("BACKGROUND",(0,1),(-1,1),rlc.HexColor("#0D1E3D")),
            ("BACKGROUND",(0,3),(-1,3),
             rlc.HexColor("#1A3010") if bal<=0 else rlc.HexColor("#3D1010")),
            ("BOX",(0,0),(-1,-1),0.5,BRD),("INNERGRID",(0,0),(-1,-1),0.3,BRD),
            ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
            ("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
        ]))
        story += [tt, Spacer(1,20),
                  HRFlowable(width="100%",thickness=0.5,color=BRD), Spacer(1,8),
                  Paragraph("<font size=8 color='#8B9EC7'>Thank you for choosing MediCore Hospital. "
                            "For queries: support@medicore.com | +91-9999999999</font>",
                            ParagraphStyle("c",parent=ss["Normal"],alignment=1))]
        doc.build(story)
        return buf.getvalue()
    except Exception as e:
        return f"PDF Error: {e}".encode()

# ══════════════════════════════════════════════════════════════
#  STREAMLIT UI
# ══════════════════════════════════════════════════════════════
st.set_page_config(page_title="MediCore Hospital", page_icon="🏥",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
[data-testid="stAppViewContainer"]{background:#0A0F1E;}
[data-testid="stSidebar"]{background:#080D1A;border-right:1px solid #1E3050;}
.stButton>button{background:#00D4FF;color:#000;font-weight:700;border:none;
  border-radius:8px;padding:8px 20px;transition:all .2s;}
.stButton>button:hover{background:#00b8d9;transform:translateY(-1px);}
div[data-testid="metric-container"]{background:#1A2235;border:1px solid #1E3050;
  border-radius:12px;padding:18px;}
div[data-testid="metric-container"] label{color:#8B9EC7 !important;font-size:12px !important;}
div[data-testid="metric-container"] div{color:#00D4FF !important;font-size:28px !important;font-weight:700 !important;}
h1,h2,h3{color:#00D4FF !important;}
.stTabs [data-baseweb="tab"]{background:#111827;color:#8B9EC7;border-radius:8px 8px 0 0;padding:8px 20px;}
.stTabs [aria-selected="true"]{background:#1A2235;color:#00D4FF !important;border-bottom:2px solid #00D4FF;}
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stTextArea>div>div>textarea{
  background:#0D1526;color:#fff;border:1px solid #1E3050;border-radius:6px;}
.stSelectbox>div>div{background:#0D1526;color:#fff;border:1px solid #1E3050;}
.stDataFrame{border:1px solid #1E3050;border-radius:10px;}
footer{display:none;}#MainMenu{display:none;}
</style>""", unsafe_allow_html=True)

# Init
init_db()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# ── LOGIN PAGE ───────────────────────────────────────────────
def login_page():
    col1,col2,col3 = st.columns([1,1.3,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center;padding:32px 24px;background:#111827;
             border-radius:20px;border:1px solid #1E3050;box-shadow:0 8px 32px rgba(0,212,255,0.1);'>
          <div style='font-size:60px;margin-bottom:8px;'>🏥</div>
          <h1 style='color:#00D4FF;margin:0;font-size:30px;letter-spacing:2px;'>MediCore</h1>
          <p style='color:#8B9EC7;margin:6px 0 4px;font-size:14px;'>Hospital Management System</p>
          <span style='background:#1A2235;padding:3px 12px;border-radius:20px;
          color:#00FF9F;font-size:11px;'>● Powered by Supabase PostgreSQL</span>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", placeholder="Enter your password", type="password")
            submitted = st.form_submit_button("🔐  LOGIN", use_container_width=True)
        if submitted:
            if not username or not password:
                st.error("Please enter username and password!")
            else:
                user = db_login(username.strip(), password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password!")
        st.markdown("""
        <div style='background:#0D1526;border-radius:12px;padding:16px;
             border:1px solid #1E3050;margin-top:14px;'>
          <p style='color:#8B9EC7;font-size:12px;font-weight:bold;margin:0 0 8px;'>
            Default Login Accounts:</p>
          <code style='color:#00D4FF;'>admin</code>
          <span style='color:#8B9EC7;'> / </span>
          <code style='color:#00FF9F;'>admin123</code>
          <span style='color:#8B9EC7;font-size:11px;'> → Admin (full access)</span><br>
          <code style='color:#00D4FF;'>doctor1</code>
          <span style='color:#8B9EC7;'> / </span>
          <code style='color:#00FF9F;'>doc123</code>
          <span style='color:#8B9EC7;font-size:11px;'> → Doctor</span><br>
          <code style='color:#00D4FF;'>receptionist</code>
          <span style='color:#8B9EC7;'> / </span>
          <code style='color:#00FF9F;'>rec123</code>
          <span style='color:#8B9EC7;font-size:11px;'> → Receptionist</span>
        </div>""", unsafe_allow_html=True)

# ── SIDEBAR ──────────────────────────────────────────────────
def sidebar_nav(user):
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:16px 10px;border-bottom:1px solid #1E3050;margin-bottom:12px;'>
          <div style='font-size:20px;font-weight:bold;color:#00D4FF;'>🏥 MediCore</div>
          <div style='margin-top:8px;'>
            <div style='font-size:13px;color:#fff;font-weight:600;'>{user['full_name']}</div>
            <span style='background:#1A2235;padding:2px 10px;border-radius:20px;
            color:#00FF9F;font-size:10px;margin-top:4px;display:inline-block;'>
            {user['role'].upper()}</span>
          </div>
        </div>""", unsafe_allow_html=True)

        all_pages = [
            ("🏠","Dashboard"),("👥","Patients"),("👨‍⚕️","Doctors"),
            ("📅","Appointments"),("💰","Billing"),("💊","Inventory"),
            ("👷","Staff"),("📊","Reports"),("👤","Users"),
        ]
        pages  = [(ic,lb) for ic,lb in all_pages if can(user["role"], lb.lower())]
        labels = [f"{ic}  {lb}" for ic,lb in pages]

        if "page" not in st.session_state or st.session_state.page not in labels:
            st.session_state.page = labels[0]

        choice = st.radio("", labels, label_visibility="collapsed",
                          index=labels.index(st.session_state.page))
        st.session_state.page = choice
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪  Logout", use_container_width=True):
            _drop_db_conn()
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    return choice.split("  ",1)[1].strip() if "  " in choice else choice.strip()

# ══════════════════════════════════════════════════════════════
#  PAGE — DASHBOARD
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
    c5.metric("💰 Revenue Collected",   f"Rs. {s['revenue']:.0f}")
    c6.metric("⚠️ Pending Bills",       s["pending"])
    c7.metric("💊 Low Stock Items",     s["low_stock"])
    c8.metric("👷 Total Staff",         s["staff"])
    st.markdown("---")
    st.subheader("📋 Recent Appointments")
    rows = fetch("""SELECT a.appointment_id as "ID", p.name as "Patient", d.name as "Doctor",
        d.specialization as "Specialization", a.appointment_date as "Date",
        a.appointment_time as "Time", a.reason as "Reason", a.status as "Status"
        FROM appointments a
        JOIN patients p ON a.patient_id=p.patient_id
        JOIN doctors  d ON a.doctor_id=d.doctor_id
        ORDER BY a.created_at DESC LIMIT 10""")
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: st.info("No appointments yet. Book one from the Appointments page!")

# ══════════════════════════════════════════════════════════════
#  PAGE — PATIENTS
# ══════════════════════════════════════════════════════════════
def page_patients():
    st.title("👥 Patient Records")
    tab1,tab2,tab3 = st.tabs(["📋 View & Search","➕ Add Patient","✏️ Edit / Delete"])
    with tab1:
        search = st.text_input("🔍 Search by name, phone, or Patient ID")
        if search:
            rows = fetch("""SELECT patient_id,name,age,gender,blood_group,phone,email,address,medical_history,created_at::text
                FROM patients WHERE name ILIKE %s OR phone LIKE %s OR CAST(patient_id AS TEXT)=%s
                ORDER BY created_at DESC""",(f"%{search}%",f"%{search}%",search))
        else:
            rows = fetch("""SELECT patient_id,name,age,gender,blood_group,phone,email,address,medical_history,created_at::text
                FROM patients ORDER BY created_at DESC""")
        if rows:
            df = pd.DataFrame(rows)
            df.columns = ["ID","Name","Age","Gender","Blood","Phone","Email","Address","Medical History","Added"]
            df["Added"] = df["Added"].str[:10]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total records: **{len(rows)}**")
        else: st.info("No patients found.")

    with tab2:
        with st.form("add_patient_form", clear_on_submit=True):
            st.markdown("**Personal Information**")
            c1,c2,c3,c4 = st.columns(4)
            name   = c1.text_input("Full Name *")
            age    = c2.number_input("Age", 0, 150, 25)
            gender = c3.selectbox("Gender", ["Male","Female","Other"])
            blood  = c4.selectbox("Blood Group", ["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"])
            st.markdown("**Contact Information**")
            c5,c6 = st.columns(2)
            phone  = c5.text_input("Phone Number")
            email  = c6.text_input("Email Address")
            address = st.text_input("Home Address")
            history = st.text_area("Medical History / Existing Conditions", height=100,
                                   placeholder="e.g. Diabetes, Hypertension, None")
            if st.form_submit_button("💾 Save Patient", use_container_width=True):
                if not name.strip(): st.error("Patient name is required!")
                else:
                    run("""INSERT INTO patients(name,age,gender,blood_group,phone,email,address,medical_history)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (name.strip(),age,gender,blood,phone,email,address,history))
                    st.success(f"✅ Patient '{name}' added successfully!"); st.rerun()

    with tab3:
        rows2 = fetch("SELECT patient_id,name,age,gender,blood_group,phone,email,address,medical_history FROM patients ORDER BY name")
        if not rows2: st.info("No patients yet."); return
        opts = {f"{r['patient_id']} — {r['name']}": r for r in rows2}
        sel  = st.selectbox("Select Patient to Edit or Delete", list(opts.keys()))
        r    = opts[sel]
        with st.form("edit_patient_form"):
            c1,c2,c3,c4 = st.columns(4)
            name   = c1.text_input("Full Name", value=r["name"])
            age    = c2.number_input("Age", 0, 150, value=int(r["age"] or 25))
            gender = c3.selectbox("Gender",["Male","Female","Other"],
                                  index=["Male","Female","Other"].index(r["gender"]) if r["gender"] in ["Male","Female","Other"] else 0)
            blood  = c4.selectbox("Blood Group",["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"],
                                  index=["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"].index(r["blood_group"]) if r["blood_group"] in ["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"] else 8)
            c5,c6 = st.columns(2)
            phone   = c5.text_input("Phone", value=r["phone"] or "")
            email   = c6.text_input("Email", value=r["email"] or "")
            address = st.text_input("Address", value=r["address"] or "")
            history = st.text_area("Medical History", value=r["medical_history"] or "", height=80)
            cu,cd = st.columns(2)
            if cu.form_submit_button("✏️ Update Patient", use_container_width=True):
                run("""UPDATE patients SET name=%s,age=%s,gender=%s,blood_group=%s,
                    phone=%s,email=%s,address=%s,medical_history=%s WHERE patient_id=%s""",
                    (name,age,gender,blood,phone,email,address,history,r["patient_id"]))
                st.success("✅ Patient updated!"); st.rerun()
            if cd.form_submit_button("🗑️ Delete Patient", use_container_width=True):
                run("DELETE FROM patients WHERE patient_id=%s",(r["patient_id"],))
                st.success("Deleted!"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  PAGE — DOCTORS
# ══════════════════════════════════════════════════════════════
def page_doctors():
    st.title("👨‍⚕️ Doctor Management")
    tab1,tab2,tab3 = st.tabs(["📋 View Doctors","➕ Add Doctor","✏️ Edit / Delete"])
    SPECS = ["Cardiology","Neurology","Orthopedics","Pediatrics","Dermatology",
             "Gynecology","General Medicine","Ophthalmology","Dentistry","Psychiatry",
             "ENT","Urology","Oncology","Radiology","Anesthesiology"]

    with tab1:
        search = st.text_input("🔍 Search by name or specialization")
        if search:
            rows = fetch("SELECT * FROM doctors WHERE name ILIKE %s OR specialization ILIKE %s ORDER BY name",
                         (f"%{search}%",f"%{search}%"))
        else:
            rows = fetch("SELECT * FROM doctors ORDER BY name")
        if rows:
            df = pd.DataFrame(rows)[["doctor_id","name","specialization","phone","email","experience","fee","available"]]
            df.columns = ["ID","Name","Specialization","Phone","Email","Exp(yrs)","Fee Rs.","Available"]
            df["Available"] = df["Available"].map({1:"✅ Yes",0:"❌ No"})
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total doctors: **{len(rows)}**")
        else: st.info("No doctors found.")

    with tab2:
        with st.form("add_doctor_form", clear_on_submit=True):
            c1,c2 = st.columns(2)
            name  = c1.text_input("Doctor Full Name *")
            spec  = c2.selectbox("Specialization", SPECS)
            c3,c4 = st.columns(2)
            phone = c3.text_input("Phone Number")
            email = c4.text_input("Email Address")
            c5,c6,c7 = st.columns(3)
            exp   = c5.number_input("Experience (years)", 0, 60, 5)
            fee   = c6.number_input("Consultation Fee Rs.", 0.0, 100000.0, 500.0, step=50.0)
            avail = c7.selectbox("Availability", ["Available","Not Available"])
            if st.form_submit_button("💾 Save Doctor", use_container_width=True):
                if not name.strip(): st.error("Doctor name required!")
                else:
                    run("""INSERT INTO doctors(name,specialization,phone,email,experience,fee,available)
                        VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                        (name.strip(),spec,phone,email,exp,fee,1 if avail=="Available" else 0))
                    st.success(f"✅ Dr. {name} added!"); st.rerun()

    with tab3:
        rows2 = fetch("SELECT * FROM doctors ORDER BY name")
        if not rows2: st.info("No doctors yet."); return
        opts = {f"{r['doctor_id']} — {r['name']} ({r['specialization']})": r for r in rows2}
        sel  = st.selectbox("Select Doctor", list(opts.keys()))
        r    = opts[sel]
        with st.form("edit_doctor_form"):
            c1,c2 = st.columns(2)
            name  = c1.text_input("Name", value=r["name"])
            spec  = c2.selectbox("Specialization", SPECS,
                                 index=SPECS.index(r["specialization"]) if r["specialization"] in SPECS else 6)
            c3,c4 = st.columns(2)
            phone = c3.text_input("Phone", value=r["phone"] or "")
            email = c4.text_input("Email", value=r["email"] or "")
            c5,c6,c7 = st.columns(3)
            exp   = c5.number_input("Experience(yrs)",0,60,value=int(r["experience"] or 0))
            fee   = c6.number_input("Fee Rs.",0.0,100000.0,value=float(r["fee"] or 0))
            avail = c7.selectbox("Available",["Available","Not Available"],
                                 index=0 if r["available"]==1 else 1)
            cu,cd = st.columns(2)
            if cu.form_submit_button("✏️ Update", use_container_width=True):
                run("""UPDATE doctors SET name=%s,specialization=%s,phone=%s,email=%s,
                    experience=%s,fee=%s,available=%s WHERE doctor_id=%s""",
                    (name,spec,phone,email,exp,fee,1 if avail=="Available" else 0,r["doctor_id"]))
                st.success("✅ Updated!"); st.rerun()
            if cd.form_submit_button("🗑️ Delete", use_container_width=True):
                run("DELETE FROM doctors WHERE doctor_id=%s",(r["doctor_id"],))
                st.success("Deleted!"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  PAGE — APPOINTMENTS
# ══════════════════════════════════════════════════════════════
def page_appointments():
    st.title("📅 Appointment Booking")
    tab1,tab2,tab3 = st.tabs(["📋 All Appointments","➕ Book Appointment","✏️ Update Status"])

    with tab1:
        col1,col2 = st.columns(2)
        status_filter = col1.selectbox("Filter by Status",["All","Scheduled","Completed","Cancelled","No Show"])
        date_filter   = col2.date_input("Filter by Date (optional)", value=None)
        sql = """SELECT a.appointment_id as "ID", p.name as "Patient", d.name as "Doctor",
            d.specialization as "Spec", a.appointment_date as "Date",
            a.appointment_time as "Time", a.reason as "Reason",
            a.status as "Status", a.notes as "Notes"
            FROM appointments a
            JOIN patients p ON a.patient_id=p.patient_id
            JOIN doctors  d ON a.doctor_id=d.doctor_id"""
        conditions = []; params = []
        if status_filter != "All": conditions.append("a.status=%s"); params.append(status_filter)
        if date_filter: conditions.append("a.appointment_date=%s"); params.append(str(date_filter))
        if conditions: sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY a.appointment_date DESC, a.appointment_time DESC"
        rows = fetch(sql, tuple(params))
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption(f"Showing **{len(rows)}** appointments")
        else: st.info("No appointments found.")

    with tab2:
        patients = fetch("SELECT patient_id,name,phone FROM patients ORDER BY name")
        doctors  = fetch("SELECT doctor_id,name,specialization,fee FROM doctors WHERE available=1 ORDER BY name")
        if not patients: st.warning("⚠️ Add patients first!"); return
        if not doctors:  st.warning("⚠️ Add doctors first!");  return
        p_opts = {f"{r['patient_id']} — {r['name']} ({r['phone']})": r['patient_id'] for r in patients}
        d_opts = {f"{r['doctor_id']} — {r['name']} ({r['specialization']}) | Rs.{r['fee']:.0f}": r['doctor_id'] for r in doctors}
        with st.form("book_apt_form", clear_on_submit=True):
            c1,c2 = st.columns(2)
            ps = c1.selectbox("Select Patient *", list(p_opts.keys()))
            ds = c2.selectbox("Select Doctor *",  list(d_opts.keys()))
            c3,c4 = st.columns(2)
            apt_date = c3.date_input("Appointment Date *", value=date.today())
            apt_time = c4.selectbox("Appointment Time *",
                ["08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30",
                 "12:00","12:30","13:00","14:00","14:30","15:00","15:30",
                 "16:00","16:30","17:00","17:30","18:00"])
            reason = st.text_area("Reason / Symptoms *", height=80,
                                  placeholder="Describe the reason for visit...")
            if st.form_submit_button("📅 Book Appointment", use_container_width=True):
                if not reason.strip(): st.error("Please enter the reason for visit!")
                else:
                    run("""INSERT INTO appointments(patient_id,doctor_id,appointment_date,appointment_time,reason)
                        VALUES(%s,%s,%s,%s,%s)""",
                        (p_opts[ps],d_opts[ds],str(apt_date),apt_time,reason.strip()))
                    st.success("✅ Appointment booked successfully!"); st.rerun()

    with tab3:
        apts = fetch("""SELECT a.appointment_id,p.name as patient,d.name as doctor,
            a.appointment_date,a.status FROM appointments a
            JOIN patients p ON a.patient_id=p.patient_id
            JOIN doctors d ON a.doctor_id=d.doctor_id
            ORDER BY a.created_at DESC""")
        if not apts: st.info("No appointments yet."); return
        a_opts = {f"#{r['appointment_id']} — {r['patient']} with {r['doctor']} on {r['appointment_date']} [{r['status']}]":
                  r['appointment_id'] for r in apts}
        sel = st.selectbox("Select Appointment", list(a_opts.keys()))
        aid = a_opts[sel]
        c1,c2 = st.columns(2)
        new_status = c1.selectbox("New Status",["Scheduled","Completed","Cancelled","No Show"])
        notes      = c2.text_input("Doctor Notes (optional)")
        cu,cd = st.columns(2)
        if cu.button("✅ Update Status", use_container_width=True):
            run("UPDATE appointments SET status=%s,notes=%s WHERE appointment_id=%s",(new_status,notes,aid))
            st.success(f"✅ Status updated to '{new_status}'!"); st.rerun()
        if cd.button("🗑️ Delete Appointment", use_container_width=True):
            run("DELETE FROM appointments WHERE appointment_id=%s",(aid,))
            st.success("Appointment deleted!"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  PAGE — BILLING
# ══════════════════════════════════════════════════════════════
def page_billing():
    st.title("💰 Billing & Payments")
    tab1,tab2 = st.tabs(["📋 All Bills + PDF","➕ Generate Bill"])

    with tab1:
        rows = fetch("""SELECT b.bill_id as "Bill ID", p.name as "Patient",
            b.amount as "Total Rs.", b.paid as "Paid Rs.",
            b.payment_status as "Status", b.bill_date::text as "Date", b.description as "Description"
            FROM billing b JOIN patients p ON b.patient_id=p.patient_id
            ORDER BY b.bill_date DESC""")
        if rows:
            df = pd.DataFrame(rows)
            df["Date"] = df["Date"].str[:10]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.markdown("---")

        st.subheader("🖨️ Download PDF Invoice")
        bills = fetch("""SELECT b.bill_id,p.name,p.phone,p.address,b.amount,b.paid,b.payment_status,b.description
            FROM billing b JOIN patients p ON b.patient_id=p.patient_id ORDER BY b.bill_date DESC""")
        if bills:
            b_opts = {f"Bill #{r['bill_id']} — {r['name']} — Rs.{r['amount']} ({r['payment_status']})":
                      r for r in bills}
            sel = st.selectbox("Select Bill", list(b_opts.keys()), key="pdf_bill_select")
            r   = b_opts[sel]
            pdf_cache_key = f"bill_pdf_{r['bill_id']}"
            if st.button("🖨️ Generate PDF Invoice", use_container_width=True, key="gen_bill_pdf"):
                pdf = generate_pdf({
                    "bill_id":        r["bill_id"],
                    "patient_name":   r["name"],
                    "patient_phone":  r["phone"] or "—",
                    "patient_address":r["address"] or "—",
                    "doctor_name":    "—",
                    "appointment_date":"—",
                    "total":          r["amount"],
                    "paid":           r["paid"],
                    "payment_status": r["payment_status"],
                    "description":    r["description"] or "Medical Services",
                })
                if pdf.startswith(b"%PDF"):
                    st.session_state[pdf_cache_key] = pdf
                else:
                    st.error(pdf.decode(errors="replace") if isinstance(pdf, bytes) else str(pdf))
            if pdf_cache_key in st.session_state:
                st.download_button("⬇️ Download PDF Bill", st.session_state[pdf_cache_key],
                                   f"MediCore_Bill_{r['bill_id']}.pdf",
                                   "application/pdf", use_container_width=True,
                                   key=f"dl_bill_{r['bill_id']}")
        else: st.info("No bills yet.")

    with tab2:
        patients = fetch("SELECT patient_id,name,phone FROM patients ORDER BY name")
        apts     = fetch("""SELECT a.appointment_id,p.name,d.name as doc,a.appointment_date
            FROM appointments a JOIN patients p ON a.patient_id=p.patient_id
            JOIN doctors d ON a.doctor_id=d.doctor_id
            WHERE a.status='Completed' ORDER BY a.appointment_date DESC""")
        if not patients: st.warning("Add patients first!"); return
        p_opts = {f"{r['patient_id']} — {r['name']} ({r['phone']})": r['patient_id'] for r in patients}
        a_opts = {"None (Walk-in)": None}
        a_opts.update({f"#{r['appointment_id']} — {r['name']} with {r['doc']} on {r['appointment_date']}":
                       r['appointment_id'] for r in apts})
        with st.form("bill_form", clear_on_submit=True):
            c1,c2 = st.columns(2)
            ps    = c1.selectbox("Patient *", list(p_opts.keys()))
            apt_s = c2.selectbox("Appointment (optional)", list(a_opts.keys()))
            c3,c4 = st.columns(2)
            amount  = c3.number_input("Total Bill Amount Rs. *", 0.0, 5000000.0, 500.0, step=50.0)
            paid_am = c4.number_input("Amount Paid Rs.", 0.0, 5000000.0, 0.0, step=50.0)
            desc = st.text_input("Description", placeholder="e.g. Consultation + Blood Test")
            st.info(f"💡 Balance: **Rs. {max(0, amount-paid_am):.2f}** | Status will be: "
                    f"**{'Paid' if paid_am>=amount else 'Partial' if paid_am>0 else 'Pending'}**")
            if st.form_submit_button("🧾 Generate Bill", use_container_width=True):
                if amount <= 0: st.error("Amount must be greater than 0!")
                else:
                    status = "Paid" if paid_am>=amount else ("Partial" if paid_am>0 else "Pending")
                    run("""INSERT INTO billing(patient_id,appointment_id,amount,paid,payment_status,description)
                        VALUES(%s,%s,%s,%s,%s,%s)""",
                        (p_opts[ps],a_opts[apt_s],amount,paid_am,status,desc))
                    st.success(f"✅ Bill generated! Status: **{status}**"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  PAGE — INVENTORY
# ══════════════════════════════════════════════════════════════
def page_inventory():
    st.title("💊 Medicine & Inventory")
    tab1,tab2,tab3 = st.tabs(["📦 View Stock","➕ Add Item","✏️ Update Stock"])
    CATS = ["Medicine","Equipment","Consumable","Surgical","Diagnostic","Lab Supplies"]

    with tab1:
        rows = fetch("SELECT * FROM inventory ORDER BY item_name")
        if rows:
            df = pd.DataFrame(rows)[["item_id","item_name","category","quantity","unit_price","supplier","expiry_date"]]
            df.columns = ["ID","Item Name","Category","Qty","Unit Price Rs.","Supplier","Expiry Date"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            low = [r for r in rows if r["quantity"] < 50]
            if low:
                st.warning(f"⚠️ **{len(low)} item(s)** are low on stock (quantity < 50)!")
                ldf = pd.DataFrame(low)[["item_name","category","quantity","supplier"]]
                ldf.columns = ["Item","Category","Qty Left","Supplier"]
                st.dataframe(ldf, use_container_width=True, hide_index=True)
            else: st.success("✅ All items are well stocked!")
        else: st.info("No inventory items yet.")

    with tab2:
        with st.form("add_inv_form", clear_on_submit=True):
            c1,c2 = st.columns(2)
            name  = c1.text_input("Item Name *")
            cat   = c2.selectbox("Category", CATS)
            c3,c4,c5 = st.columns(3)
            qty   = c3.number_input("Quantity", 0, 100000, 100)
            price = c4.number_input("Unit Price Rs.", 0.0, 100000.0, 10.0)
            supp  = c5.text_input("Supplier Name")
            expiry = st.text_input("Expiry Date (YYYY-MM-DD)", placeholder="2027-12-31")
            if st.form_submit_button("💾 Add Item", use_container_width=True):
                if not name.strip(): st.error("Item name required!")
                else:
                    run("""INSERT INTO inventory(item_name,category,quantity,unit_price,supplier,expiry_date)
                        VALUES(%s,%s,%s,%s,%s,%s)""", (name.strip(),cat,qty,price,supp,expiry))
                    st.success(f"✅ '{name}' added to inventory!"); st.rerun()

    with tab3:
        rows2 = fetch("SELECT * FROM inventory ORDER BY item_name")
        if not rows2: st.info("No items yet."); return
        i_opts = {f"{r['item_id']} — {r['item_name']} (Qty: {r['quantity']})": r for r in rows2}
        sel = st.selectbox("Select Item", list(i_opts.keys()))
        r   = i_opts[sel]
        with st.form("edit_inv_form"):
            c1,c2,c3 = st.columns(3)
            new_qty   = c1.number_input("Update Quantity", 0, 100000, value=int(r["quantity"]))
            new_price = c2.number_input("Update Price Rs.", 0.0, 100000.0, value=float(r["unit_price"]))
            new_supp  = c3.text_input("Supplier", value=r["supplier"] or "")
            new_exp   = st.text_input("Expiry Date", value=r["expiry_date"] or "")
            cu,cd = st.columns(2)
            if cu.form_submit_button("✏️ Update Item", use_container_width=True):
                run("UPDATE inventory SET quantity=%s,unit_price=%s,supplier=%s,expiry_date=%s WHERE item_id=%s",
                    (new_qty,new_price,new_supp,new_exp,r["item_id"]))
                st.success("✅ Updated!"); st.rerun()
            if cd.form_submit_button("🗑️ Delete Item", use_container_width=True):
                run("DELETE FROM inventory WHERE item_id=%s",(r["item_id"],))
                st.success("Deleted!"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  PAGE — STAFF
# ══════════════════════════════════════════════════════════════
def page_staff():
    st.title("👷 Staff Management")
    tab1,tab2,tab3 = st.tabs(["📋 View Staff","➕ Add Staff","✏️ Edit / Delete"])
    ROLES  = ["Nurse","Receptionist","Pharmacist","Lab Technician","Security","Cleaner","Admin","Ward Boy","Accountant"]
    SHIFTS = ["Morning","Evening","Night","Rotating"]

    with tab1:
        rows = fetch("SELECT * FROM staff ORDER BY name")
        if rows:
            df = pd.DataFrame(rows)[["staff_id","name","role","phone","salary","shift","created_at"]]
            df.columns = ["ID","Name","Role","Phone","Salary Rs.","Shift","Joined"]
            df["Joined"] = df["Joined"].astype(str).str[:10]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total staff: **{len(rows)}**")
        else: st.info("No staff records yet.")

    with tab2:
        with st.form("add_staff_form", clear_on_submit=True):
            c1,c2 = st.columns(2)
            name  = c1.text_input("Full Name *")
            role  = c2.selectbox("Job Role", ROLES)
            c3,c4,c5 = st.columns(3)
            phone  = c3.text_input("Phone Number")
            salary = c4.number_input("Monthly Salary Rs.", 0.0, 1000000.0, 30000.0, step=1000.0)
            shift  = c5.selectbox("Shift", SHIFTS)
            if st.form_submit_button("💾 Add Staff Member", use_container_width=True):
                if not name.strip(): st.error("Name required!")
                else:
                    run("INSERT INTO staff(name,role,phone,salary,shift) VALUES(%s,%s,%s,%s,%s)",
                        (name.strip(),role,phone,salary,shift))
                    st.success(f"✅ {name} added!"); st.rerun()

    with tab3:
        rows2 = fetch("SELECT * FROM staff ORDER BY name")
        if not rows2: st.info("No staff yet."); return
        s_opts = {f"{r['staff_id']} — {r['name']} ({r['role']})": r for r in rows2}
        sel = st.selectbox("Select Staff", list(s_opts.keys()))
        r   = s_opts[sel]
        with st.form("edit_staff_form"):
            c1,c2 = st.columns(2)
            name   = c1.text_input("Name", value=r["name"])
            role   = c2.selectbox("Role", ROLES, index=ROLES.index(r["role"]) if r["role"] in ROLES else 0)
            c3,c4,c5 = st.columns(3)
            phone  = c3.text_input("Phone", value=r["phone"] or "")
            salary = c4.number_input("Salary Rs.", 0.0, 1000000.0, value=float(r["salary"] or 0))
            shift  = c5.selectbox("Shift", SHIFTS, index=SHIFTS.index(r["shift"]) if r["shift"] in SHIFTS else 0)
            cu,cd = st.columns(2)
            if cu.form_submit_button("✏️ Update", use_container_width=True):
                run("UPDATE staff SET name=%s,role=%s,phone=%s,salary=%s,shift=%s WHERE staff_id=%s",
                    (name,role,phone,salary,shift,r["staff_id"]))
                st.success("✅ Updated!"); st.rerun()
            if cd.form_submit_button("🗑️ Delete", use_container_width=True):
                run("DELETE FROM staff WHERE staff_id=%s",(r["staff_id"],))
                st.success("Deleted!"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  PAGE — REPORTS
# ══════════════════════════════════════════════════════════════
def page_reports():
    st.title("📊 Reports & Analytics")
    st.markdown("Generate visual analytics charts from live hospital data.")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("""<div style='background:#1A2235;border:1px solid #00D4FF;border-radius:12px;
            padding:20px;'>
            <h3 style='color:#00D4FF;margin:0;'>📊 Dashboard Report</h3>
            <p style='color:#8B9EC7;font-size:13px;margin:8px 0 0;'>
            8 charts: monthly appointments, revenue trend, doctor specializations,
            appointment status, patient gender, blood groups, age groups, top doctors</p>
            </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Generate Dashboard Report", use_container_width=True, key="gen_dash"):
            with st.spinner("⏳ Generating analytics chart..."):
                try:
                    buf = dashboard_chart()
                    st.session_state["report_dash_png"] = buf.getvalue()
                except Exception as e:
                    st.error(f"Chart error: {e}")
        if "report_dash_png" in st.session_state:
            st.image(io.BytesIO(st.session_state["report_dash_png"]), use_container_width=True)
            st.download_button("⬇️ Download PNG", st.session_state["report_dash_png"],
                               "MediCore_Dashboard.png", "image/png",
                               use_container_width=True, key="dl_dash_png")

    with c2:
        st.markdown("""<div style='background:#1A2235;border:1px solid #7B61FF;border-radius:12px;
            padding:20px;'>
            <h3 style='color:#7B61FF;margin:0;'>👥 Patient Analytics</h3>
            <p style='color:#8B9EC7;font-size:13px;margin:8px 0 0;'>
            Monthly new patient registration trend (12 months)
            + patient age group distribution pie chart</p>
            </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Generate Patient Report", use_container_width=True, key="gen_pat"):
            with st.spinner("⏳ Generating patient chart..."):
                try:
                    buf = patient_chart()
                    st.session_state["report_pat_png"] = buf.getvalue()
                except Exception as e:
                    st.error(f"Chart error: {e}")
        if "report_pat_png" in st.session_state:
            st.image(io.BytesIO(st.session_state["report_pat_png"]), use_container_width=True)
            st.download_button("⬇️ Download PNG", st.session_state["report_pat_png"],
                               "MediCore_Patients.png", "image/png",
                               use_container_width=True, key="dl_pat_png")

# ══════════════════════════════════════════════════════════════
#  PAGE — USERS
# ══════════════════════════════════════════════════════════════
def page_users():
    st.title("👤 User Management")
    st.info("ℹ️ Only Admin can access this page. Passwords are stored as SHA-256 hashes.")
    tab1,tab2 = st.tabs(["👥 All Users","➕ Add / Delete User"])

    with tab1:
        rows = fetch("SELECT user_id,username,role,full_name,email,active,created_at::text FROM users ORDER BY created_at")
        if rows:
            df = pd.DataFrame(rows)
            df.columns = ["ID","Username","Role","Full Name","Email","Active","Created"]
            df["Active"] = df["Active"].map({1:"✅ Active",0:"❌ Inactive"})
            df["Created"] = df["Created"].str[:10]
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        with st.form("add_user_form", clear_on_submit=True):
            st.subheader("➕ Add New User")
            c1,c2,c3 = st.columns(3)
            uname = c1.text_input("Username *")
            upass = c2.text_input("Password *", type="password")
            urole = c3.selectbox("Role", ["admin","doctor","receptionist"])
            c4,c5 = st.columns(2)
            fname = c4.text_input("Full Name")
            email = c5.text_input("Email")
            if st.form_submit_button("💾 Create User", use_container_width=True):
                if not uname.strip() or not upass:
                    st.error("Username and password are required!")
                elif fetch("SELECT 1 FROM users WHERE username=%s LIMIT 1", (uname.strip(),)):
                    st.error("❌ That username is already taken. Choose another.")
                else:
                    h = hashlib.sha256(upass.encode()).hexdigest()
                    run("INSERT INTO users(username,password,role,full_name,email) VALUES(%s,%s,%s,%s,%s)",
                        (uname.strip(),h,urole,fname,email))
                    st.success(f"✅ User '{uname}' created!"); st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Delete User")
        users = fetch("SELECT user_id,username,role,full_name FROM users ORDER BY username")
        if users:
            u_opts = {f"{r['user_id']} — {r['username']} ({r['role']}) — {r['full_name']}":
                      r['user_id'] for r in users}
            sel = st.selectbox("Select User to Delete", list(u_opts.keys()))
            if st.button("🗑️ Delete Selected User", use_container_width=True):
                uid = u_opts[sel]
                if uid == st.session_state.user.get("user_id"):
                    st.error("❌ You cannot delete your own account!")
                else:
                    run("DELETE FROM users WHERE user_id=%s",(uid,))
                    st.success("User deleted!"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  MAIN ROUTER
# ══════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    login_page()
else:
    user = st.session_state.user
    page = sidebar_nav(user)
    PAGES = {
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
    fn = PAGES.get(page)
    if fn:
        if can(user["role"], page.lower()):
            fn()
        else:
            st.error(f"🚫 Access Denied — Your role **({user['role']})** cannot access **{page}**.")
            st.info("Contact admin if you need access.")
    else:
        page_dashboard()
