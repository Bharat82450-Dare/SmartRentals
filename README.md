# 🏠 SmartRentals — Advanced Rental Management System

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **Digitizing the rental experience.** A comprehensive, browser-based ecosystem for property owners, tenants, and maintenance staff to manage the entire rental lifecycle seamlessly.

---

## 📖 Overview

**SmartRentals** was born out of a simple problem: property management is often a chaotic mess of WhatsApp messages, Excel sheets, and handwritten receipts. 

This platform centralizes everything. From property listing and tenant onboarding to automated rent tracking and maintenance management, SmartRentals provides a unified, glassmorphic interface that feels premium and functions powerfully.

---

## 🚀 Core Features

### 🏢 Multi-User Portals
- **Admin Dashboard**: Full control over properties, tenants, agreements, and staff assignments.
- **Tenant Portal**: Self-service access to lease details, payment history, and one-click maintenance requests.
- **Staff Portal**: Simplified interface for maintenance crews to track and resolve assigned tasks.

### 📋 Management Modules
- **Property Tracking**: Manage multiple units with automated availability status (Vacant/Occupied).
- **Tenant CRM**: Securely store tenant profiles, ID proofs, and emergency contacts.
- **Dynamic Lease Agreements**: Digital agreements with custom rent due days, late fee logic, and automated expiry alerts (🔴 ≤ 7 days, 🟡 ≤ 30 days).
- **Automated Billing**: Record payments via UPI/Cash/Bank, calculate late fees, and generate professional **PDF receipts**.
- **Maintenance Lifecycle**: Status tracking from *Open* to *Resolved* with photo descriptions and staff assignments.

---

## 🛠️ Use Cases

### 👨‍💼 Use Case 1: The Property Manager (Admin)
*   **Goal**: Ensure 100% occupancy and on-time payments.
*   **Activity**: Admin checks the dashboard for "Agreement Expiry Alerts" (Phase 4). They notice a tenant's lease ends in 15 days. They contact the tenant, renew the agreement in one click, and the dashboard stat updates automatically.

### 👤 Use Case 2: The Modern Tenant
*   **Goal**: Quick access to receipts and maintenance.
*   **Activity**: A tenant notices a leaking faucet. They log in to their portal, raise a "Plumbing" complaint with a description. They can check back anytime to see if a staff member has been assigned.

### 🔧 Use Case 3: The Maintenance Staff
*   **Goal**: Efficiently handle repairs.
*   **Activity**: The plumber logs into their dedicated portal, sees only the "Open" plumbing tickets assigned to them, updates the status to "In Progress," and finally "Resolved" once the work is done.

---

## 🔄 System Workflow

The following diagram illustrates the standard lifecycle of a rental unit within SmartRentals:

```mermaid
graph TD
    A[Property Created] --> B{Availability?}
    B -- Vacant --> C[Register New Tenant]
    C --> D[Create Lease Agreement]
    D --> E[Property Becomes Occupied]
    E --> F[Monthly Rent Cycle]
    F --> G[Record Payment]
    G --> H[Generate PDF Receipt]
    F --> I[Maintenance Request]
    I --> J[Admin Assigns Staff]
    J --> K[Staff Resolves Ticket]
    D -- Expiry Alert --> L{Renew or Terminate?}
    L -- Terminate --> M[Property Becomes Vacant]
    L -- Renew --> D
```

---

## 🎨 Design Philosophy: "Premium Utility"

SmartRentals isn't just a tool; it's an experience.
- **Glassmorphism**: Modern UI using translucent containers, blur effects, and vibrant gradients.
- **Color Rule (60-30-10)**: 
    - **60% Primary**: Deep Earthy Tones / Dark Mode.
    - **30% Secondary**: Soft Glass Finishes.
    - **10% Accent**: Bright Blaze Orange (`#FF5F38`) for calls to action.
- **Responsive**: Built for desktop management and mobile-ready tenant access.

---

## 💻 Tech Stack

- **Backend**: Python 3.9+ with **Flask**
- **Database**: **Firebase Firestore** (NoSQL, Real-time)
- **Security**: CSRF Protection, Session Management, and Firebase Admin SDK
- **PDF Engine**: `fpdf2` for dynamic invoice generation
- **Frontend**: HTML5, Vanilla CSS, JS (Poppins Typography)

---

## ⚙️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Bharat82450-Dare/SmartRentals.git
   cd SmartRentals
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Firebase Configuration**:
   - Place your `serviceAccountKey.json` in the root directory.
   - Ensure you have a Firestore project set up with collections: `properties`, `tenants`, `agreements`, `payments`, `complaints`, `staff_users`.

4. **Run the application**:
   ```bash
   python app.py
   ```
   Access the dashboard at `http://127.0.0.1:5000`.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

---
*Developed with ❤️ for Property Managers everywhere.*
