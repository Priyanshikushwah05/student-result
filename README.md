#  Student Result Management System

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat&logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

A full-stack web application to manage student results — add students, enter subject-wise marks, auto-calculate grades, and export PDF report cards.

---

##  Demo

![Dashboard](screenshots/dashboard.png)
![Student Detail](screenshots/detail.png)

---

##  Features

- **Add & manage students** — name, roll number, created date
- **Subject-wise marks** — add/update/delete marks per subject
- **Auto grade calculation** — A+, A, B, C, D, F based on percentage
- **PDF report cards** — export individual student result as a formatted PDF
- **Dashboard analytics** — class average, top student, grade distribution
- **Search & filter** — find students by name, roll number, or grade

##  Grade System

| Grade | Percentage |
|-------|-----------|
| A+    | 90% and above |
| A     | 80% – 89% |
| B     | 70% – 79% |
| C     | 60% – 69% |
| D     | 50% – 59% |
| F     | Below 50% |

---

##  Project Structure

```
student-result/
├── app.py           # Flask backend — all API routes + PDF generation
├── index.html       # Frontend dashboard
├── requirements.txt # Python dependencies
├── .gitignore
└── README.md
```

**Architecture:** Single-file Flask backend with SQLite database + vanilla JS frontend. REST API connects both layers.

---

##  Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/student-result.git
cd student-result

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the backend
python app.py

# 4. Open frontend (new terminal)
python -m http.server 8080

# 5. Open browser
# Go to: http://localhost:8080
```

---

##  Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.8+ | Core language |
| Flask | REST API backend |
| SQLite | Relational database |
| fpdf2 | PDF report generation |
| JavaScript | Frontend interactivity |
| Chart.js | Grade distribution chart |
| HTML/CSS | UI design |

---

##  What I Learned

- Designing a **relational database** with SQLite (students + marks tables with foreign keys)
- Building **CRUD REST APIs** with Flask
- Generating **formatted PDF reports** programmatically
- Connecting a **vanilla JS frontend** to a Flask backend via fetch API
- Handling **cascading deletes** and data integrity in SQLite

---

##  Possible Extensions

- [ ] Multi-class / multi-semester support
- [ ] Login system for teachers
- [ ] Email report cards directly to students
- [ ] Export full class report as Excel

---

##  License

MIT License
