# Hospital Management System — Deployment Guide

Ye guide step-by-step batati hai ki domain/hosting buy karne ke baad project ko live kaise karna hai.

## Prerequisites (buy karne ke baad)
- **Domain**: Namecheap / GoDaddy se khareedo
- **VPS Hosting**: Hostinger VPS, DigitalOcean, ya Railway (Ubuntu 24.04 recommend)
- VPS milne ke baad: IP address aur root/SSH access milega

---

## Step 1: Domain ko VPS se connect karo
Domain registrar (Namecheap/GoDaddy) ke DNS settings mein:
- A Record: `@` → tumhare VPS ka IP address
- A Record: `www` → tumhare VPS ka IP address

(DNS propagate hone mein 1-24 hours lag sakte hain)

## Step 2: VPS pe SSH se login karo
```bash
ssh root@your_server_ip
```

## Step 3: Server setup
```bash
apt update && apt upgrade -y
apt install -y python3-pip python3-venv nginx postgresql postgresql-contrib certbot python3-certbot-nginx git
```

## Step 4: PostgreSQL database banao
```bash
sudo -u postgres psql
```
Andar ye commands chalao:
```sql
CREATE DATABASE hospital_db;
CREATE USER hospital_user WITH PASSWORD 'STRONG_PASSWORD_YAHA_DAALO';
ALTER ROLE hospital_user SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE hospital_db TO hospital_user;
\q
```

## Step 5: Project upload karo
```bash
mkdir -p /var/www/hospital_system
cd /var/www/hospital_system
# Apna zip yahan upload/extract karo, ya git clone karo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 6: .env file production ke liye set karo
```bash
cp .env.example .env
nano .env
```
Ye fill karo:
```
SECRET_KEY=<naya secret generate karo neeche diye command se>
DEBUG=False
ALLOWED_HOSTS=yourhospital.com,www.yourhospital.com
DATABASE_URL=postgres://hospital_user:STRONG_PASSWORD_YAHA_DAALO@127.0.0.1:5432/hospital_db
```
Naya SECRET_KEY generate karne ke liye:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

## Step 7: Database migrate aur static files collect karo
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## Step 8: Gunicorn service start karo
```bash
mkdir -p /var/log/hospital_system
cp deploy/hospital_system.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now hospital_system
systemctl status hospital_system   # check ki "active (running)" dikh raha hai
```

## Step 9: Nginx setup karo
```bash
cp deploy/nginx.conf /etc/nginx/sites-available/hospital_system
# nginx.conf mein yourhospital.com ko apne actual domain se replace karo
ln -s /etc/nginx/sites-available/hospital_system /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

## Step 10: Free SSL certificate (HTTPS) laga do
```bash
certbot --nginx -d yourhospital.com -d www.yourhospital.com
```
Certbot automatically Nginx config update kar dega HTTPS ke liye. Free certificate hai, auto-renew hota rehta hai.

## Step 11: Daily backup setup karo
```bash
chmod +x deploy/backup_db.sh
crontab -e
```
Ye line add karo:
```
0 2 * * * /var/www/hospital_system/deploy/backup_db.sh >> /var/log/hospital_system/backup.log 2>&1
```
(Har raat 2 AM pe automatic backup hoga, 14 din tak rakhega)

---

## Verify everything is working
1. Browser mein `https://yourhospital.com` khol kar login page check karo
2. SSL lock icon dikhna chahiye (https, not http)
3. Login karke dashboard test karo
4. `systemctl status hospital_system` aur `systemctl status nginx` dono "active" hone chahiye

## Future code updates (jab bhi changes karne ho)
```bash
cd /var/www/hospital_system
git pull   # ya naya zip upload karo
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart hospital_system
```

## Agar kuch galat ho jaye
```bash
journalctl -u hospital_system -n 50   # last 50 error lines dekhne ke liye
tail -50 /var/log/hospital_system/error.log
```
