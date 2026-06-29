# Hospital Staff Handover Checklist

Hospital ko handover karte waqt ye sab dena/batana hai:

## 1. Login Credentials dena
- [ ] Admin login (username + password) — ye unka main account hai
- [ ] Doctor/Receptionist/Pharmacist accounts banao Admin panel se (Staff section)
- [ ] **Pehli baar login ke baad password change karne ko bolo**

## 2. Initial Setup (pehli baar karna hai)
- [ ] Django Admin (`/admin/`) se Wards aur Beds add karo (General Ward, ICU, etc + bed numbers)
- [ ] Doctors add karo "Doctors" section se (login + specialization + fee)
- [ ] Medicines add karo "Pharmacy" section se (stock quantity sahi se daalo)

## 3. Daily Use Training (staff ko ye dikhana hai)
- [ ] **Receptionist**: Naya patient register karna, appointment book karna, admit karna
- [ ] **Doctor**: Apne appointments dekhna, prescription banana
- [ ] **Pharmacist**: Medicine stock update karna, low-stock alerts dekhna
- [ ] **Admin/Receptionist**: Invoice banana, payment record karna, PDF bill download karna

## 4. Important Notes for Hospital
- Patient ID automatic generate hota hai (PAT-2026-0001 format) — manually mat banana
- Invoice number bhi automatic hai (INV-2026-0001 format)
- Ek baar discharge/complete kiya appointment dobara invoice mein nahi aayega (double-billing impossible hai)
- Bed automatically free ho jaata hai discharge karne par

## 5. Data Safety
- Database har raat 2 AM automatically backup hota hai (14 din tak)
- Backup files yahan milengi: `/var/backups/hospital_system/`
- Agar koi important data accidentally delete ho jaaye, backup se restore kiya ja sakta hai (developer se contact karo)

## 6. Support
- Koi bug ya issue aaye to error message ka screenshot le ke developer ko bhejo
- Server "down" lage to pehle check karo: domain khul raha hai ya nahi, dusre device se try karo

## 7. Future Scope (agar aage chahiye)
- SMS/WhatsApp appointment reminders
- Lab reports module
- Multi-branch support (agar hospital ki dusri branch ho)
