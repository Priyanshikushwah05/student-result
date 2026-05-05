import os
import json
import sqlite3
from datetime import date
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from fpdf import FPDF
import tempfile

app = Flask(__name__)
CORS(app)

DB_FILE = "students.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            marks INTEGER NOT NULL,
            max_marks INTEGER NOT NULL DEFAULT 100,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def calculate_grade(percentage):
    if percentage >= 90: return "A+"
    elif percentage >= 80: return "A"
    elif percentage >= 70: return "B"
    elif percentage >= 60: return "C"
    elif percentage >= 50: return "D"
    else: return "F"

def get_student_result(student_id):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        conn.close()
        return None
    marks = conn.execute("SELECT * FROM marks WHERE student_id = ?", (student_id,)).fetchall()
    conn.close()

    marks_list = [{"id": m["id"], "subject": m["subject"], "marks": m["marks"], "max_marks": m["max_marks"]} for m in marks]
    total = sum(m["marks"] for m in marks)
    max_total = sum(m["max_marks"] for m in marks)
    percentage = round((total / max_total * 100), 2) if max_total > 0 else 0
    grade = calculate_grade(percentage) if marks_list else "N/A"

    return {
        "id": student["id"],
        "name": student["name"],
        "roll_number": student["roll_number"],
        "created_at": student["created_at"],
        "marks": marks_list,
        "total": total,
        "max_total": max_total,
        "percentage": percentage,
        "grade": grade
    }

@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db()
    students = conn.execute("SELECT * FROM students ORDER BY roll_number").fetchall()
    conn.close()
    results = []
    for s in students:
        r = get_student_result(s["id"])
        if r: results.append(r)
    grade_filter = request.args.get("grade")
    search = request.args.get("search", "").lower()
    if grade_filter:
        results = [r for r in results if r["grade"] == grade_filter]
    if search:
        results = [r for r in results if search in r["name"].lower() or search in r["roll_number"].lower()]
    return jsonify(results)

@app.route("/api/students", methods=["POST"])
def add_student():
    body = request.json
    name = body.get("name", "").strip()
    roll_number = body.get("roll_number", "").strip()
    if not name or not roll_number:
        return jsonify({"error": "Name and roll number are required"}), 400
    try:
        conn = get_db()
        conn.execute("INSERT INTO students (name, roll_number, created_at) VALUES (?, ?, ?)",
                     (name, roll_number, str(date.today())))
        conn.commit()
        student = conn.execute("SELECT * FROM students WHERE roll_number = ?", (roll_number,)).fetchone()
        conn.close()
        return jsonify(get_student_result(student["id"])), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Roll number already exists"}), 409

@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    conn = get_db()
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/students/<int:student_id>/marks", methods=["POST"])
def add_marks(student_id):
    body = request.json
    subject = body.get("subject", "").strip()
    marks = body.get("marks")
    max_marks = body.get("max_marks", 100)
    if not subject or marks is None:
        return jsonify({"error": "Subject and marks are required"}), 400
    if int(marks) > int(max_marks):
        return jsonify({"error": "Marks cannot exceed max marks"}), 400
    conn = get_db()
    existing = conn.execute("SELECT id FROM marks WHERE student_id = ? AND subject = ?", (student_id, subject)).fetchone()
    if existing:
        conn.execute("UPDATE marks SET marks = ?, max_marks = ? WHERE student_id = ? AND subject = ?",
                     (int(marks), int(max_marks), student_id, subject))
    else:
        conn.execute("INSERT INTO marks (student_id, subject, marks, max_marks) VALUES (?, ?, ?, ?)",
                     (student_id, subject, int(marks), int(max_marks)))
    conn.commit()
    conn.close()
    return jsonify(get_student_result(student_id)), 201

@app.route("/api/students/<int:student_id>/marks/<int:mark_id>", methods=["DELETE"])
def delete_mark(student_id, mark_id):
    conn = get_db()
    conn.execute("DELETE FROM marks WHERE id = ? AND student_id = ?", (mark_id, student_id))
    conn.commit()
    conn.close()
    return jsonify(get_student_result(student_id))

@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = get_db()
    total_students = conn.execute("SELECT COUNT(*) as c FROM students").fetchone()["c"]
    conn.close()
    all_results = []
    conn = get_db()
    students = conn.execute("SELECT id FROM students").fetchall()
    conn.close()
    for s in students:
        r = get_student_result(s["id"])
        if r and r["marks"]: all_results.append(r)
    if not all_results:
        return jsonify({"total_students": total_students, "avg_percentage": 0, "top_student": None, "grade_distribution": {}})
    avg_pct = round(sum(r["percentage"] for r in all_results) / len(all_results), 2)
    top = max(all_results, key=lambda r: r["percentage"])
    grade_dist = {}
    for r in all_results:
        grade_dist[r["grade"]] = grade_dist.get(r["grade"], 0) + 1
    return jsonify({
        "total_students": total_students,
        "avg_percentage": avg_pct,
        "top_student": {"name": top["name"], "percentage": top["percentage"]},
        "grade_distribution": grade_dist
    })

@app.route("/api/students/<int:student_id>/pdf", methods=["GET"])
def export_student_pdf(student_id):
    r = get_student_result(student_id)
    if not r:
        return jsonify({"error": "Student not found"}), 404
    pdf = generate_pdf(r)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return send_file(tmp.name, as_attachment=True, download_name=f"result_{r['roll_number']}.pdf")

def generate_pdf(r):
    pdf = FPDF()
    pdf.add_page()
    # Header
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 40, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_y(10)
    pdf.cell(0, 10, "Student Result Card", align="C", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Generated on {date.today()}", align="C", ln=True)
    pdf.set_y(48)
    pdf.set_text_color(0, 0, 0)
    # Student info
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Student Information", ln=True)
    pdf.set_draw_color(99, 102, 241)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(50, 7, "Name:", ln=False)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, r["name"], ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(50, 7, "Roll Number:", ln=False)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, r["roll_number"], ln=True)
    pdf.ln(4)
    # Marks table
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Subject-wise Marks", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(80, 8, "Subject", border=1, fill=True)
    pdf.cell(40, 8, "Marks", border=1, fill=True, align="C")
    pdf.cell(40, 8, "Max Marks", border=1, fill=True, align="C")
    pdf.cell(30, 8, "%", border=1, fill=True, align="C", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    for i, m in enumerate(r["marks"]):
        pct = round(m["marks"] / m["max_marks"] * 100, 1)
        fill = i % 2 == 0
        pdf.set_fill_color(245, 245, 255)
        pdf.cell(80, 7, m["subject"], border=1, fill=fill)
        pdf.cell(40, 7, str(m["marks"]), border=1, fill=fill, align="C")
        pdf.cell(40, 7, str(m["max_marks"]), border=1, fill=fill, align="C")
        pdf.cell(30, 7, f"{pct}%", border=1, fill=fill, align="C", ln=True)
    pdf.ln(6)
    # Result summary
    grade_colors = {"A+": (34,197,94), "A": (74,222,128), "B": (96,165,250), "C": (251,191,36), "D": (251,146,60), "F": (239,68,68), "N/A": (156,163,175)}
    gc = grade_colors.get(r["grade"], (99,102,241))
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Result Summary", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(60, 8, f"Total Marks: {r['total']} / {r['max_total']}")
    pdf.cell(60, 8, f"Percentage: {r['percentage']}%")
    pdf.set_fill_color(*gc)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(30, 8, f"Grade: {r['grade']}", fill=True, align="C", ln=True)
    pdf.set_text_color(0, 0, 0)
    # Footer
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, "Student Result Management System", align="C")
    return pdf

init_db()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
