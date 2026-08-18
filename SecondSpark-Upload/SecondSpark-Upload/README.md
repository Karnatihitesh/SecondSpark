# SecondSpark

> **Give Unfinished Ideas a Second Spark.**

SecondSpark is a full-stack platform where creators of abandoned, incomplete, faulty, or stalled hardware and software projects can upload their prototypes and connect with skilled engineers, developers, and makers who can repair, improve, complete, or co-develop them.

---

## 🌟 Core Features

- **Modern Minimalist UI**: Built with custom responsive CSS, subtle emerald green styling (`#35C98A`), and refined glassmorphism cards.
- **Interactive 3D Hero Visualization**: Dynamic Three.js canvas depicting floating project nodes and connecting sparks of collaboration, with automatic fallback for low-power devices.
- **Database-Driven Discovery**: Real-time project discovery with live-search autocomplete, category pills, budget ranges, status filters, and multi-field sorting.
- **Full Project Lifecycle**: Project upload with multi-image previews, file uploads (.ino, .py, .pdf, .stl), condition tagging, problem detailing, edit controls, and lifecycle state management (Open, Help Needed, In Discussion, In Progress, Completed, Closed).
- **Real-Time Communication**: Dual-pane conversation and direct messaging interface with auto-scrolling, unread badges, and live background polling.
- **Reputation & Review System**: 1-to-5 star ratings and peer reviews on completed collaborations.
- **Admin Moderation Portal**: Comprehensive control center for platform statistics, user management (activate/suspend), project moderation (feature/delete), report resolution queue, category creation, and contact inquiry triage.
- **Zero-Config Dual Database**: Production-ready for MySQL with zero-configuration fallback to SQLite out of the box.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, Flask 3.0, Flask-SQLAlchemy, Werkzeug (PBKDF2 Password Hashing) |
| **Database** | MySQL / SQLite with SQLAlchemy ORM |
| **Frontend** | HTML5, Vanilla CSS3 (Custom Design System), JavaScript (ES6+), Three.js |
| **Icons & Typography** | FontAwesome 6, Google Inter Font |

---

## 📁 Directory Structure

```
SecondSpark/
├── app/
│   ├── __init__.py               # Flask factory, context processors, error handlers
│   ├── models/                   # SQLAlchemy relational models
│   │   ├── user.py               # User authentication & profile
│   │   ├── category.py           # Project categories
│   │   ├── project.py            # Project, Images, Docs, Saved bookmarks
│   │   ├── message.py            # Conversations & Messages
│   │   ├── notification.py       # User alerts
│   │   ├── review.py             # Collaboration reviews & star ratings
│   │   ├── report.py             # Moderation reports
│   │   └── contact.py            # Contact inquiries
│   ├── routes/                   # Modular Flask Blueprints
│   │   ├── auth.py               # /auth (login, register, logout, profile)
│   │   ├── main.py               # / (home, about, contact, how-it-works)
│   │   ├── projects.py           # /projects (browse, upload, edit, details)
│   │   ├── dashboard.py          # /dashboard (analytics, my projects, bookmarks)
│   │   ├── messages.py           # /messages (conversations & chat)
│   │   ├── notifications.py      # /notifications (feed & mark-read)
│   │   ├── reviews.py            # /reviews (create reviews)
│   │   ├── reports.py            # /reports (file reports)
│   │   ├── admin.py              # /admin (moderation portal)
│   │   └── api.py                # /api (live search, chat polling, save toggle)
│   ├── services/                 # Helper & business logic services
│   ├── static/
│   │   ├── css/                  # style.css & responsive.css
│   │   ├── js/                   # three-hero.js, chat.js, projects.js, etc.
│   │   ├── images/               # Logo, avatar, and placeholder SVGs
│   │   └── uploads/              # Project photos & documents
│   └── templates/                # Jinja2 templates extending base.html
├── config.py                     # Configuration classes
├── run.py                        # App runner & CLI seed command
├── seed_data.py                  # Database seed script
├── requirements.txt              # Production dependencies
├── .env                          # Environment variables
└── README.md
```

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed Database (Creates tables, 16 categories, admin, demo projects & chats)
```bash
python run.py --seed
```

### 3. Run the Development Server
```bash
python run.py
```
Open **http://localhost:5000** in your browser.

---

## 🔑 Default Credentials

### Administrator Account
- **Username:** `admin`
- **Email:** `admin@secondspark.com`
- **Password:** `Admin@12345`

### Demo User Accounts
| Username | Email | Password | Role / Specialty |
|---|---|---|---|
| `alex_chen` | `alex@secondspark.com` | `Alex@12345` | Robotics & ROS2 |
| `priya_sharma` | `priya@secondspark.com` | `Priya@12345` | Embedded Systems & IoT |
| `marcus_vance` | `marcus@secondspark.com` | `Marcus@12345` | Computer Vision & Edge AI |
| `elena_rostova` | `elena@secondspark.com` | `Elena@12345` | Biomedical CAD & Bionics |

---

## 👥 Core Development Team

- **Karnati Hitesh Sadineni** — Team Lead & Full-Stack Integration (`karnatihitesh@gmail.com` / `+91 9490682602`)
- **Mrudul Annepalli** — Frontend Development & Glassmorphism UI
- **Jashwanth Reddy Siripanga** — Authentication, Cryptography & Backend REST APIs
- **Manikumar Nandala** — Project Management Module & Filter Engine
- **Supriya Mamidi** — Communication Module & Real-Time Messaging
- **Vydhika** — Quality Assurance, Testing & API Documentation

---

## 📄 License
© 2026 SecondSpark. All rights reserved.
