"""
╔══════════════════════════════════════════════════════════╗
║   MediCore Hospital Management System — Streamlit v2.0  ║
╚══════════════════════════════════════════════════════════╝
"""
import streamlit as st
import database as db
import charts, pdf_gen
import pandas as pd
from datetime import date

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="MediCore Hospital",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"]{background:#0A0F1E;}
  [data-testid="stSidebar"]{background:#080D1A;border-right:1px solid #1E3050;}
  [data-testid="stSidebar"] *{color:#C5D0E6 !important;}
  .stButton>button{background:#00D4FF;color:#000;font-weight:bold;border:none;border-radius:8px;}
  .stButton>button:hover{background:#00b8d9;color:#000;}
  .stTextInput>div>div>input,.stSelectbox>div>div,.stNumberInput>div>div>input,
  .stDateInput>div>div>input{background:#0D1526;color:#fff;border:1px solid #1E3050;border-radius:6px;}
  .stDataFrame{border:1px solid #1E3050;border-radius:8px;}
  .stAlert{border-radius:8px;}
  div[data-testid="metric-container"]{background:#1A2235;border:1px solid #1E3050;
    border-radius:10px;padding:16px;}
  div[data-testid="metric-container"] label{color:#8B9EC7 !important;}
  div[data-testid="metric-container"] div{color:#00D4FF !important;}
  h1,h2,h3{color:#00D4FF !important;}
  .stSelectbox label,.stTextInput label,.stNumberInput label,.stDateInput label,
  .stTextArea label{color:#8B9EC7 !important;}
  .stTabs [data-baseweb="tab"]{background:#111827;color:#8B9EC7;border-radius:8px 8px 0 0;}
  .stTabs [aria-selected="true"]{background:#1A2235;color:#00D4FF !important;border-bottom:2px solid #00D4FF;}
  footer{display:none;}
  #MainMenu{display:none;}
</style>
""", unsafe_allow_html=True)

# ── Init DB ───────────────────────────────────────────────────
db.init_db()

# ── Session state ─────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# ══════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ══════════════════════════════════════════════════════════════
def login_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center;padding:30px;background:#111827;
             border-radius:16px;border:1px solid #1E3050;'>
          <div style='font-size:56px;margin-bottom:8px;'>🏥</div>
          <h1 style='color:#00D4FF;margin:0;font-size:28px;'>MediCore</h1>
          <p style='color:#8B9EC7;margin:4px 0 24px;'>Hospital Management System</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔒 Password", placeholder="Enter password", type="password")
            submitted = st.form_submit_button("🔐 LOGIN", use_container_width=True)

        if submitted:
            user = db.login(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("❌ Invalid username or password!")

        st.markdown("""
        <div style='background:#0D1526;border-radius:10px;padding:14px;
             border:1px solid #1E3050;margin-top:16px;'>
          <p style='color:#8B9EC7;font-size:12px;margin:0 0 8px;font-weight:bold;'>
            Default Accounts:</p>
          <code style='color:#00D4FF;'>admin</code>
          <span style='color:#8B9EC7;'> / </span>
          <code style='color:#00FF9F;'>admin123</code>
          <span style='color:#8B9EC7;'> [Admin]</span><br>
          <code style='color:#00D4FF;'>doctor1</code>
          <span style='color:#8B9EC7;'> / </span>
          <code style='color:#00FF9F;'>doc123</code>
          <span style='color:#8B9EC7;'> [Doctor]</span><br>
          <code style='color:#00D4FF;'>receptionist</code>
          <span style='color:#8B9EC7;'> / </span>
          <code style='color:#00FF9F;'>rec123</code>
          <span style='color:#8B9EC7;'> [Receptionist]</span>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  SIDEBAR NAV
# ══════════════════════════════════════════════════════════════
def sidebar_nav(user):
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:16px 8px;border-bottom:1px solid #1E3050;margin-bottom:12px;'>
          <div style='font-size:22px;font-weight:bold;color:#00D4FF;'>🏥 MediCore</div>
          <div style='font-size:11px;color:#8B9EC7;margin-top:4px;'>
            {user['full_name']}<br>
            <span style='background:#1A2235;padding:2px 8px;border-radius:10px;
            color:#00FF9F;font-size:10px;'>{user['role'].upper()}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        all_pages = [
            ("🏠", "Dashboard"),
            ("👥", "Patients"),
            ("👨‍⚕️", "Doctors"),
            ("📅", "Appointments"),
            ("💰", "Billing"),
            ("💊", "Inventory"),
            ("👷", "Staff"),
            ("📊", "Reports"),
            ("👤", "Users"),
        ]
        pages = [(i,l) for i,l in all_pages if db.can(user["role"], l.lower())]
        labels = [f"{i}  {l}" for i,l in pages]

        if "page" not in st.session_state:
            st.session_state.page = labels[0]

        for lbl in labels:
            active = st.session_state.page == lbl
            bg = "#0D1E3D" if active else "transparent"
            border = "2px solid #00D4FF" if active else "2px solid transparent"
            col_c = "#00D4FF" if active else "#C5D0E6"
            st.markdown(f"""
            <div style='background:{bg};border-left:{border};padding:9px 14px;
                 border-radius:0 8px 8px 0;margin:2px 0;cursor:pointer;color:{col_c};
                 font-size:13px;'>
              {lbl}
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        choice = st.radio("", labels, label_visibility="collapsed",
                          index=labels.index(st.session_state.page) if st.session_state.page in labels else 0,
                          key="nav_radio")
        st.session_state.page = choice

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    return choice.split("  ", 1)[1] if "  " in choice else choice.strip()

# ══════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════
def page_dashboard():
    st.title("📊 Dashboard Overview")
    s = db.stats()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("👥 Total Patients",     s["patients"])
    c2.metric("👨‍⚕️ Total Doctors",      s["doctors"])
    c3.metric("📅 Today's Appointments",s["today_apts"])
    c4.metric("🗓️ Total Appointments",  s["appointments"])
    c5,c6,c7,c8 = st.columns(4)
    c5.metric("💰 Revenue Collected",  f"Rs. {s['revenue']:.0f}")
    c6.metric("⚠️ Pending Bills",      s["pending"])
    c7.metric("💊 Low Stock Items",    s["low_stock"])
    c8.metric("👷 Total Staff",        s["staff"])

    st.markdown("---")
    st.subheader("📋 Recent Appointments")
    rows = db.fetch("""
        SELECT a.appointment_id id, p.name patient, d.name doctor,
               d.specialization spec, a.appointment_date date,
               a.appointment_time time, a.status
        FROM appointments a
        JOIN patients p ON a.patient_id=p.patient_id
        JOIN doctors  d ON a.doctor_id=d.doctor_id
        ORDER BY a.created_at DESC LIMIT 10""")
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No appointments yet.")

# ══════════════════════════════════════════════════════════════
#  PATIENTS
# ══════════════════════════════════════════════════════════════
def page_patients():
    st.title("👥 Patient Records")
    tab1, tab2 = st.tabs(["📋 View Records", "➕ Add / Edit Patient"])

    with tab1:
        search = st.text_input("🔍 Search by name / phone / ID")
        if search:
            rows = db.fetch(
                "SELECT * FROM patients WHERE name LIKE ? OR phone LIKE ? OR CAST(patient_id AS TEXT)=?",
                (f"%{search}%", f"%{search}%", search))
        else:
            rows = db.fetch("SELECT * FROM patients ORDER BY created_at DESC")
        if rows:
            df = pd.DataFrame(rows)[["patient_id","name","age","gender","blood_group","phone","email","address","medical_history","created_at"]]
            df.columns=["ID","Name","Age","Gender","Blood","Phone","Email","Address","History","Added"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total: {len(rows)} patients")
        else:
            st.info("No patients found.")

        if rows:
            st.markdown("**Delete Patient**")
            del_id = st.number_input("Enter Patient ID to delete", min_value=1, step=1, key="del_p")
            if st.button("🗑️ Delete Patient", key="del_p_btn"):
                db.run("DELETE FROM patients WHERE patient_id=?", (del_id,))
                st.success("Patient deleted!"); st.rerun()

    with tab2:
        with st.form("patient_form"):
            c1,c2,c3,c4 = st.columns(4)
            name   = c1.text_input("Name *")
            age    = c2.number_input("Age", 0, 150, 25)
            gender = c3.selectbox("Gender", ["Male","Female","Other"])
            blood  = c4.selectbox("Blood Group", ["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"])
            c5,c6 = st.columns(2)
            phone  = c5.text_input("Phone")
            email  = c6.text_input("Email")
            address = st.text_input("Address")
            history = st.text_area("Medical History", height=80)
            if st.form_submit_button("💾 Save Patient", use_container_width=True):
                if not name: st.error("Name is required!")
                else:
                    db.run("INSERT INTO patients(name,age,gender,blood_group,phone,email,address,medical_history) VALUES(?,?,?,?,?,?,?,?)",
                           (name,age,gender,blood,phone,email,address,history))
                    st.success(f"✅ Patient '{name}' added!"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  DOCTORS
# ══════════════════════════════════════════════════════════════
def page_doctors():
    st.title("👨‍⚕️ Doctor Management")
    tab1, tab2 = st.tabs(["📋 View Doctors", "➕ Add / Edit Doctor"])

    with tab1:
        search = st.text_input("🔍 Search by name / specialization")
        if search:
            rows = db.fetch("SELECT * FROM doctors WHERE name LIKE ? OR specialization LIKE ?",
                            (f"%{search}%", f"%{search}%"))
        else:
            rows = db.fetch("SELECT * FROM doctors ORDER BY name")
        if rows:
            df = pd.DataFrame(rows)[["doctor_id","name","specialization","phone","email","experience","fee","available","created_at"]]
            df.columns=["ID","Name","Specialization","Phone","Email","Exp (yrs)","Fee Rs.","Available","Added"]
            df["Available"] = df["Available"].map({1:"Yes",0:"No"})
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No doctors found.")

        if rows:
            del_id = st.number_input("Doctor ID to delete", min_value=1, step=1, key="del_d")
            if st.button("🗑️ Delete Doctor", key="del_d_btn"):
                db.run("DELETE FROM doctors WHERE doctor_id=?", (del_id,))
                st.success("Deleted!"); st.rerun()

    with tab2:
        specs = ["Cardiology","Neurology","Orthopedics","Pediatrics","Dermatology",
                 "Gynecology","General Medicine","Ophthalmology","Dentistry","Psychiatry"]
        with st.form("doctor_form"):
            c1,c2 = st.columns(2)
            name  = c1.text_input("Doctor Name *")
            spec  = c2.selectbox("Specialization", specs)
            c3,c4 = st.columns(2)
            phone = c3.text_input("Phone")
            email = c4.text_input("Email")
            c5,c6,c7 = st.columns(3)
            exp   = c5.number_input("Experience (years)", 0, 60, 5)
            fee   = c6.number_input("Consultation Fee Rs.", 0.0, 100000.0, 500.0)
            avail = c7.selectbox("Available", ["Yes","No"])
            if st.form_submit_button("💾 Save Doctor", use_container_width=True):
                if not name: st.error("Name required!")
                else:
                    db.run("INSERT INTO doctors(name,specialization,phone,email,experience,fee,available) VALUES(?,?,?,?,?,?,?)",
                           (name,spec,phone,email,exp,fee,1 if avail=="Yes" else 0))
                    st.success(f"✅ Dr. {name} added!"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  APPOINTMENTS
# ══════════════════════════════════════════════════════════════
def page_appointments():
    st.title("📅 Appointment Booking")
    tab1, tab2, tab3 = st.tabs(["📋 All Appointments", "➕ Book Appointment", "✏️ Update Status"])

    with tab1:
        rows = db.fetch("""
            SELECT a.appointment_id id, p.name patient, d.name doctor,
                   d.specialization spec, a.appointment_date date,
                   a.appointment_time time, a.reason, a.status, a.notes
            FROM appointments a
            JOIN patients p ON a.patient_id=p.patient_id
            JOIN doctors  d ON a.doctor_id=d.doctor_id
            ORDER BY a.appointment_date DESC""")
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total: {len(rows)} appointments")
        else:
            st.info("No appointments yet.")

    with tab2:
        patients = db.fetch("SELECT patient_id,name FROM patients ORDER BY name")
        doctors  = db.fetch("SELECT doctor_id,name,specialization FROM doctors ORDER BY name")
        if not patients: st.warning("Add patients first!"); return
        if not doctors:  st.warning("Add doctors first!");  return

        p_opts = {f"{r['patient_id']} – {r['name']}": r['patient_id'] for r in patients}
        d_opts = {f"{r['doctor_id']} – {r['name']} ({r['specialization']})": r['doctor_id'] for r in doctors}

        with st.form("apt_form"):
            c1,c2 = st.columns(2)
            p_sel = c1.selectbox("Patient *", list(p_opts.keys()))
            d_sel = c2.selectbox("Doctor *",  list(d_opts.keys()))
            c3,c4 = st.columns(2)
            apt_date = c3.date_input("Date *", value=date.today())
            apt_time = c4.text_input("Time * (HH:MM)", value="10:00")
            reason   = st.text_input("Reason / Symptoms")
            if st.form_submit_button("📅 Book Appointment", use_container_width=True):
                db.run("INSERT INTO appointments(patient_id,doctor_id,appointment_date,appointment_time,reason) VALUES(?,?,?,?,?)",
                       (p_opts[p_sel], d_opts[d_sel], str(apt_date), apt_time, reason))
                st.success("✅ Appointment booked!"); st.rerun()

    with tab3:
        apt_id   = st.number_input("Appointment ID", min_value=1, step=1)
        new_stat = st.selectbox("New Status", ["Scheduled","Completed","Cancelled","No Show"])
        notes    = st.text_input("Notes (optional)")
        c1,c2   = st.columns(2)
        if c1.button("✅ Update Status", use_container_width=True):
            db.run("UPDATE appointments SET status=?,notes=? WHERE appointment_id=?",
                   (new_stat, notes, apt_id))
            st.success("Updated!"); st.rerun()
        if c2.button("🗑️ Delete Appointment", use_container_width=True):
            if st.session_state.get("confirm_del_apt"):
                db.run("DELETE FROM appointments WHERE appointment_id=?", (apt_id,))
                st.success("Deleted!"); st.session_state.confirm_del_apt=False; st.rerun()
            else:
                st.session_state.confirm_del_apt=True
                st.warning("Click Delete again to confirm.")

# ══════════════════════════════════════════════════════════════
#  BILLING
# ══════════════════════════════════════════════════════════════
def page_billing():
    st.title("💰 Billing & Payments")
    tab1, tab2 = st.tabs(["📋 All Bills", "➕ Generate Bill"])

    with tab1:
        rows = db.fetch("""
            SELECT b.bill_id, p.name patient, b.amount, b.paid,
                   b.payment_status status, b.bill_date date, b.description
            FROM billing b JOIN patients p ON b.patient_id=p.patient_id
            ORDER BY b.bill_date DESC""")
        if rows:
            df = pd.DataFrame(rows)
            df["amount"] = df["amount"].apply(lambda x: f"Rs. {x:,.2f}")
            df["paid"]   = df["paid"].apply(lambda x: f"Rs. {x:,.2f}")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # PDF Download
            st.markdown("---")
            st.subheader("🖨️ Download PDF Bill")
            bill_id = st.number_input("Bill ID for PDF", min_value=1, step=1)
            if st.button("Generate PDF", key="pdf_btn"):
                raw = db.fetch("""
                    SELECT b.*,p.name pn,p.phone pp,p.address pa,p.email pe
                    FROM billing b JOIN patients p ON b.patient_id=p.patient_id
                    WHERE b.bill_id=?""", (bill_id,))
                if raw:
                    r = raw[0]
                    data = {"bill_id":r["bill_id"],"patient_name":r["pn"],"patient_phone":r["pp"],
                            "patient_address":r["pa"],"doctor_name":"—","appointment_date":"—",
                            "total":r["amount"],"paid":r["paid"],"payment_status":r["payment_status"],
                            "description":r["description"] or "Medical Services"}
                    pdf_bytes = pdf_gen.generate_pdf(data)
                    st.download_button("⬇️ Download PDF", pdf_bytes,
                                       file_name=f"Bill_{bill_id}.pdf",
                                       mime="application/pdf",
                                       use_container_width=True)
                else:
                    st.error("Bill not found!")
        else:
            st.info("No bills yet.")

    with tab2:
        patients = db.fetch("SELECT patient_id,name FROM patients ORDER BY name")
        apts     = db.fetch("""SELECT a.appointment_id,p.name,a.appointment_date
                               FROM appointments a JOIN patients p ON a.patient_id=p.patient_id
                               ORDER BY a.appointment_date DESC LIMIT 50""")
        if not patients: st.warning("Add patients first!"); return
        p_opts = {f"{r['patient_id']} – {r['name']}": r['patient_id'] for r in patients}
        a_opts = {"None": None}
        a_opts.update({f"{r['appointment_id']} – {r['name']} ({r['appointment_date']})": r['appointment_id'] for r in apts})

        with st.form("bill_form"):
            c1,c2 = st.columns(2)
            p_sel    = c1.selectbox("Patient *", list(p_opts.keys()))
            a_sel    = c2.selectbox("Appointment (optional)", list(a_opts.keys()))
            c3,c4   = st.columns(2)
            amount   = c3.number_input("Total Amount Rs. *", 0.0, 1000000.0, 500.0)
            paid_amt = c4.number_input("Amount Paid Rs.",    0.0, 1000000.0, 0.0)
            desc     = st.text_input("Description")
            if st.form_submit_button("🧾 Generate Bill", use_container_width=True):
                status = "Paid" if paid_amt>=amount else ("Partial" if paid_amt>0 else "Pending")
                db.run("INSERT INTO billing(patient_id,appointment_id,amount,paid,payment_status,description) VALUES(?,?,?,?,?,?)",
                       (p_opts[p_sel], a_opts[a_sel], amount, paid_amt, status, desc))
                st.success(f"✅ Bill generated — Status: {status}"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  INVENTORY
# ══════════════════════════════════════════════════════════════
def page_inventory():
    st.title("💊 Medicine & Inventory")
    tab1, tab2 = st.tabs(["📦 View Inventory", "➕ Add / Edit Item"])

    with tab1:
        rows = db.fetch("SELECT * FROM inventory ORDER BY item_name")
        if rows:
            df = pd.DataFrame(rows)[["item_id","item_name","category","quantity","unit_price","supplier","expiry_date"]]
            df.columns=["ID","Item Name","Category","Quantity","Unit Price Rs.","Supplier","Expiry"]
            # Highlight low stock
            def highlight_low(row):
                color = "background-color: #3D1010; color: #FF6B6B" if row["Quantity"] < 50 else ""
                return [color]*len(row)
            st.dataframe(df.style.apply(highlight_low, axis=1), use_container_width=True, hide_index=True)
            low = [r for r in rows if r["quantity"] < 50]
            if low:
                st.warning(f"⚠️ {len(low)} item(s) are low on stock (qty < 50)!")
        else:
            st.info("No inventory items.")

    with tab2:
        cats = ["Medicine","Equipment","Consumable","Surgical","Diagnostic"]
        with st.form("inv_form"):
            c1,c2 = st.columns(2)
            name  = c1.text_input("Item Name *")
            cat   = c2.selectbox("Category", cats)
            c3,c4,c5 = st.columns(3)
            qty    = c3.number_input("Quantity", 0, 100000, 100)
            price  = c4.number_input("Unit Price Rs.", 0.0, 100000.0, 10.0)
            supp   = c5.text_input("Supplier")
            expiry = st.text_input("Expiry Date (YYYY-MM-DD)")
            if st.form_submit_button("💾 Add Item", use_container_width=True):
                if not name: st.error("Name required!")
                else:
                    db.run("INSERT INTO inventory(item_name,category,quantity,unit_price,supplier,expiry_date) VALUES(?,?,?,?,?,?)",
                           (name,cat,qty,price,supp,expiry))
                    st.success("✅ Item added!"); st.rerun()

        st.markdown("---")
        st.subheader("✏️ Update Item Quantity")
        with st.form("upd_inv"):
            iid  = st.number_input("Item ID", min_value=1, step=1)
            nqty = st.number_input("New Quantity", 0, 100000, 100)
            if st.form_submit_button("Update Quantity", use_container_width=True):
                db.run("UPDATE inventory SET quantity=? WHERE item_id=?", (nqty,iid))
                st.success("Updated!"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  STAFF
# ══════════════════════════════════════════════════════════════
def page_staff():
    st.title("👷 Staff Management")
    tab1, tab2 = st.tabs(["📋 View Staff", "➕ Add Staff"])

    with tab1:
        rows = db.fetch("SELECT * FROM staff ORDER BY name")
        if rows:
            df = pd.DataFrame(rows)[["staff_id","name","role","phone","salary","shift","created_at"]]
            df.columns=["ID","Name","Role","Phone","Salary Rs.","Shift","Added"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No staff members.")

        del_id = st.number_input("Staff ID to delete", min_value=1, step=1, key="del_s")
        if st.button("🗑️ Delete Staff", key="del_s_btn"):
            db.run("DELETE FROM staff WHERE staff_id=?", (del_id,))
            st.success("Deleted!"); st.rerun()

    with tab2:
        roles  = ["Nurse","Receptionist","Pharmacist","Lab Technician","Security","Cleaner","Admin"]
        shifts = ["Morning","Evening","Night","Rotating"]
        with st.form("staff_form"):
            c1,c2 = st.columns(2)
            name   = c1.text_input("Full Name *")
            role   = c2.selectbox("Role", roles)
            c3,c4,c5 = st.columns(3)
            phone  = c3.text_input("Phone")
            salary = c4.number_input("Salary Rs.", 0.0, 1000000.0, 30000.0)
            shift  = c5.selectbox("Shift", shifts)
            if st.form_submit_button("💾 Add Staff", use_container_width=True):
                if not name: st.error("Name required!")
                else:
                    db.run("INSERT INTO staff(name,role,phone,salary,shift) VALUES(?,?,?,?,?)",
                           (name,role,phone,salary,shift))
                    st.success(f"✅ {name} added!"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  REPORTS
# ══════════════════════════════════════════════════════════════
def page_reports():
    st.title("📊 Reports & Analytics")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
        <div style='background:#1A2235;border:1px solid #1E3050;border-radius:10px;padding:16px;'>
          <h3 style='color:#00D4FF;'>📊 Full Dashboard Report</h3>
          <p style='color:#8B9EC7;font-size:13px;'>
            8 charts: appointments, revenue, doctors, blood groups,
            patient gender, age groups, top doctors, appointment status
          </p>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Generate Dashboard Report", key="dash_rep", use_container_width=True):
            with st.spinner("Generating report..."):
                buf = charts.dashboard_chart()
            st.image(buf, use_container_width=True)
            st.download_button("⬇️ Download PNG", buf.getvalue(),
                               "dashboard_report.png", "image/png",
                               use_container_width=True)

    with c2:
        st.markdown("""
        <div style='background:#1A2235;border:1px solid #1E3050;border-radius:10px;padding:16px;'>
          <h3 style='color:#7B61FF;'>👥 Patient Analytics</h3>
          <p style='color:#8B9EC7;font-size:13px;'>
            Monthly new patients trend (12 months) + age group distribution pie chart
          </p>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Generate Patient Report", key="pat_rep", use_container_width=True):
            with st.spinner("Generating report..."):
                buf = charts.patient_chart()
            st.image(buf, use_container_width=True)
            st.download_button("⬇️ Download PNG", buf.getvalue(),
                               "patient_report.png", "image/png",
                               use_container_width=True)

# ══════════════════════════════════════════════════════════════
#  USERS
# ══════════════════════════════════════════════════════════════
def page_users():
    st.title("👤 User Management")
    import hashlib
    rows = db.fetch("SELECT user_id,username,role,full_name,email,active,rowid FROM users")
    if rows:
        df = pd.DataFrame(rows)[["user_id","username","role","full_name","email","active"]]
        df.columns=["ID","Username","Role","Full Name","Email","Active"]
        df["Active"]=df["Active"].map({1:"Yes",0:"No"})
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("➕ Add New User")
    with st.form("user_form"):
        c1,c2,c3 = st.columns(3)
        uname  = c1.text_input("Username *")
        upass  = c2.text_input("Password *", type="password")
        urole  = c3.selectbox("Role", ["admin","doctor","receptionist"])
        c4,c5 = st.columns(2)
        fname  = c4.text_input("Full Name")
        email  = c5.text_input("Email")
        if st.form_submit_button("💾 Add User", use_container_width=True):
            if not (uname and upass): st.error("Username & password required!")
            else:
                h=hashlib.sha256(upass.encode()).hexdigest()
                try:
                    db.run("INSERT INTO users(username,password,role,full_name,email) VALUES(?,?,?,?,?)",
                           (uname,h,urole,fname,email))
                    st.success(f"✅ User '{uname}' added!"); st.rerun()
                except Exception as e:
                    st.error(f"Error: {e} (username may already exist)")

    st.markdown("---")
    del_id = st.number_input("User ID to delete", min_value=1, step=1)
    if st.button("🗑️ Delete User"):
        db.run("DELETE FROM users WHERE user_id=?", (del_id,))
        st.success("Deleted!"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  MAIN ROUTER
# ══════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    login_page()
else:
    user  = st.session_state.user
    page  = sidebar_nav(user)

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
        if db.can(user["role"], page.lower()):
            fn()
        else:
            st.error(f"🚫 Access Denied — Your role ({user['role']}) cannot access {page}.")
    else:
        page_dashboard()
