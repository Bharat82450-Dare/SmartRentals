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
- [ ] Tenant–property mapping display (show which property a tenant is currently assigned to).

---

## Phase 4: Lease Agreement & Expiry Reminders ✅
- [x] Create lease agreements: assign tenant → property, set start date, end date, monthly rent.
- [x] Mark property as Occupied when an agreement is created; Vacant when terminated.
- [x] Visual expiry badges on agreement cards: 🔴 ≤ 7 days, 🟡 ≤ 30 days, grey = expired.
- [x] Terminate an active agreement.
- [x] Dashboard alert banner: shows when any agreement expires within 30 days, links to Agreements page.

---

## Phase 5: Rent Payment Tracking ✅ (partial)
- [x] Record monthly rent payment: select agreement, payment month, amount, payment mode (UPI / Cash / Bank Transfer / Cheque).
- [x] Auto-fill rent amount when an agreement is selected.
- [x] Display full payment history in a table.
- [ ] Add explicit **rent due date** field per payment period.
- [ ] **Late fee** calculation — flag payments past the due date and apply a configurable late charge.

---

## Phase 6: Receipt / Invoice Module ✅ (partial)
- [x] Generate a printable HTML rent receipt per payment (opens in new tab, print button).
- [x] Receipt shows: tenant & property, month, amount, payment mode, date, reference ID.
- [ ] **PDF receipt generation** using WeasyPrint or ReportLab (downloadable `.pdf` file).
- [ ] Store receipt history per agreement for later re-download.

---

## Phase 7: Complaint & Maintenance Module ✅ (partial)
- [x] Log complaints: tenant name, property reference, category (Plumbing / Electrical / Pest Control etc.), description.
- [x] Status lifecycle: Open → In Progress → Resolved, with colour-coded cards.
- [x] Admin can update complaint status.
- [ ] **Assign complaints to a maintenance staff member** (dropdown of staff users).
- [ ] Maintenance staff role: dedicated view showing only their assigned complaints.

---

## Phase 8: Dashboard & UI Polish ✅
- [x] Summary stats: Total Properties, Occupied, Vacant, Total Tenants, Active Agreements, Expiring ≤ 30 days, Open Complaints, Total Income.
- [x] Animated stat cards with count-up effect.
- [x] Quick-access navigation cards for all modules.
- [x] Consistent navigation across all pages (Dashboard → Properties → Tenants → Agreements → Payments → Complaints).

---

## Phase 9: Rebranding ✅
- [x] Rebrand from "SmartPrice Insights" to **SmartRentals** across all pages.
- [x] Modern glassmorphism design: dark gradient background, floating white panels, vibrant stat cards.
- [x] Consistent typography (Poppins), orange accent (#FF5F38), smooth animations.
- [x] Updated landing page (`index.html`) with rental-focused content and branding.

---

## Phase 10: Tenant Portal — Role-Based Access (Optional)
- [ ] Separate **Tenant login** (email + password via Firebase Auth or local).
- [ ] Tenant dashboard: view own rent due dates and payment history.
- [ ] **Upload payment proof** (image or PDF) when making a payment.
- [ ] Tenant can download/view their own receipts.
- [ ] Tenant can raise a maintenance complaint directly from their portal.

---

## Phase 11: Maintenance Staff Module (Optional)
- [ ] Staff login with restricted access (complaints only).
- [ ] Staff sees only complaints assigned to them.
- [ ] Staff can update status (In Progress / Resolved) and add resolution notes.

---

## Phase 12: Testing & Deployment
- [ ] End-to-end testing of all Admin flows (property → tenant → agreement → payment → receipt).
- [ ] Test edge cases: duplicate payments, expired agreements, empty states.
- [ ] Deploy to a cloud platform (e.g. Google Cloud Run, Railway, or Render).
- [ ] Configure production Firebase credentials via environment variables.
