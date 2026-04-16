# SmartRentals — Rental / Tenant Management System

## Problem Statement
Property owners and rental companies struggle to track tenant details, rent due dates, late payments, security deposits, agreement expiry, and maintenance requests — often relying on notebooks, Excel, or WhatsApp. SmartRentals digitises this entirely.

---

## Phase 1: Core Setup & Infrastructure
- [x] Initialize Flask application with CSRF protection and session management.
- [x] Integrate Firebase Admin SDK (`firebase-admin`) for Firestore database.
- [x] Set up Admin login (username/password authentication).
- [x] Create base folder structure: `templates/`, `static/`, `server/`.
- [x] Remove legacy ML files (`util.py`, pickled models, CSV datasets) — not applicable to this PS.
- [x] Update `requirements.txt` to include only relevant packages.

---

## Phase 2: Property Module ✅
- [x] Add rental properties with details: address, flat number, type (1BHK / 2BHK etc.), rent amount, deposit amount, availability status.
- [x] List all properties with status badges (Vacant / Occupied).
- [x] Delete a property.

---

## Phase 3: Tenant Module ✅
- [x] Register tenant with: name, phone, email, ID proof (Aadhar/PAN/Passport), number of family members, emergency contact.
- [x] Add **occupation** field to tenant registration form and backend.
- [x] List all tenants with card view (shows occupation, family size, emergency contact).
- [x] Delete a tenant record.
- [x] Tenant–property mapping display (show which property a tenant is currently assigned to).
- [x] Portal password field — admin sets tenant's login password on registration.

---

## Phase 4: Lease Agreement & Expiry Reminders ✅
- [x] Create lease agreements: assign tenant → property, set start date, end date, monthly rent.
- [x] **Rent due day** (1–28 select, default 5th) and **late fee amount** fields on agreement creation.
- [x] Mark property as Occupied when an agreement is created; Vacant when terminated.
- [x] Visual expiry badges on agreement cards: 🔴 ≤ 7 days, 🟡 ≤ 30 days, grey = expired.
- [x] Terminate an active agreement.
- [x] Dashboard alert banner: shows when any agreement expires within 30 days, links to Agreements page.

---

## Phase 5: Rent Payment Tracking ✅
- [x] Record monthly rent payment: select agreement, payment month, amount, payment mode (UPI / Cash / Bank Transfer / Cheque).
- [x] Auto-fill rent amount when an agreement is selected.
- [x] Display full payment history in a table.
- [x] **Late fee** calculation — payment past `due_day` of that month flags `is_late=True` and records configured `late_fee_amount`.
- [x] Late fee column shown in payment history table (red amount or "—").

---

## Phase 6: Receipt / Invoice Module ✅
- [x] Generate a printable HTML rent receipt per payment (opens in new tab, print button).
- [x] Receipt shows: tenant & property, month, amount, payment mode, date, reference ID.
- [x] Late fee section on receipt if payment was late.
- [x] **PDF receipt generation** using fpdf2 (downloadable `.pdf` file).
- [x] PDF download button on HTML receipt and payment history table.

---

## Phase 7: Complaint & Maintenance Module ✅
- [x] Log complaints: tenant name, property reference, category (Plumbing / Electrical / Pest Control etc.), description.
- [x] Status lifecycle: Open → In Progress → Resolved, with colour-coded cards.
- [x] Admin can update complaint status.
- [x] **Assign complaints to a maintenance staff member** (dropdown of staff users).
- [x] Assigned staff name shown on complaint cards.

---

## Phase 8: Dashboard & UI Polish ✅
- [x] Summary stats: Total Properties, Occupied, Vacant, Total Tenants, Active Agreements, Expiring ≤ 30 days, Open Complaints, Total Income.
- [x] Animated stat cards with count-up effect.
- [x] Quick-access navigation cards for all modules.
- [x] Consistent navigation across all pages (Dashboard → Properties → Tenants → Agreements → Payments → Complaints → Staff).

---

## Phase 9: Rebranding ✅
- [x] Rebrand from "SmartPrice Insights" to **SmartRentals** across all pages.
- [x] Modern glassmorphism design: dark gradient background, floating white panels, vibrant stat cards.
- [x] Consistent typography (Poppins), orange accent (#FF5F38), smooth animations.
- [x] Updated landing page (`index.html`) with rental-focused content and branding.

---

## Phase 10: Tenant Portal ✅
- [x] Separate **Tenant login** (phone + portal password).
- [x] Tenant dashboard: view own active lease, rent due dates, payment history with receipts.
- [x] Late fee visibility in tenant payment history.
- [x] Tenant can raise a maintenance complaint directly from their portal.
- [x] Tenant can view own complaint history with status tracking.
- [x] Tenant can download/print their own receipts (HTML + PDF).

---

## Phase 11: Maintenance Staff Module ✅
- [x] Staff login with restricted access (username + password from `staff_users` collection).
- [x] Staff sees only complaints assigned to them.
- [x] Staff can update status (In Progress / Resolved) and add resolution notes.
- [x] Admin staff management page — add/delete staff members with specialisation field.

---

## Phase 12: Testing & Deployment
- [ ] End-to-end testing of all Admin flows (property → tenant → agreement → payment → receipt).
- [ ] Test edge cases: duplicate payments, expired agreements, empty states.
- [ ] Deploy to a cloud platform (e.g. Google Cloud Run, Railway, or Render).
- [ ] Configure production Firebase credentials via environment variables.
